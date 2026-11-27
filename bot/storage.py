"""Async SQLite storage for consultation leads and Telegram users."""

import asyncio
import csv
import io
import json
import logging
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from unicodedata import category

import aiosqlite

from leads import UZ_FULL_DIGITS, UZBEKISTAN_PHONE_PREFIX


logger = logging.getLogger(__name__)

CSV_COLUMNS = (
    "id",
    "created_at",
    "tg_user_id",
    "tg_username",
    "tg_full_name",
    "name",
    "age",
    "phone",
    "region",
    "topics",
    "prior",
    "call_time",
    "source",
    "comment",
    "script",
    "delivered",
)
USER_CSV_COLUMNS = (
    "tg_user_id",
    "tg_username",
    "tg_full_name",
    "source",
    "first_seen_at",
    "last_seen_at",
)
CSV_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
PHONE_COLUMN = "phone"
# Group sizes after the 998 country code: 90 123 45 67.
UZ_PHONE_GROUP_SIZES = (2, 3, 2, 2)
UZ_PHONE_EXPORT_SEPARATOR = " "
DEFAULT_UNDELIVERED_LIMIT = 50
UNDELIVERED = 0
DELIVERED = 1


def format_uz_phone(value: str) -> str | None:
    """Return '998 XX XXX XX XX' for a stored +998 number, else None."""
    full_prefix = "+" + UZBEKISTAN_PHONE_PREFIX
    digits = value[1:]
    if not value.startswith(full_prefix) or not (
        digits.isascii() and digits.isdigit() and len(digits) == UZ_FULL_DIGITS
    ):
        return None
    national = digits[len(UZBEKISTAN_PHONE_PREFIX):]
    groups = [UZBEKISTAN_PHONE_PREFIX]
    start = 0
    for size in UZ_PHONE_GROUP_SIZES:
        groups.append(national[start:start + size])
        start += size
    return UZ_PHONE_EXPORT_SEPARATOR.join(groups)


def _guard_csv_formula(cell: str) -> str:
    if cell.startswith(CSV_FORMULA_PREFIXES):
        return "'" + cell
    return cell


def _guard_users_csv_formula(cell: str) -> str:
    # Check the first visible character while preserving the original cell text.
    for index, char in enumerate(cell):
        if not (char.isspace() or category(char) in ("Cc", "Cf")):
            if cell.startswith(CSV_FORMULA_PREFIXES, index):
                return "'" + cell
            break
    return _guard_csv_formula(cell)


class Storage:
    """Store Telegram users and leads with decoded topics."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._db: aiosqlite.Connection | None = None
        self._write_lock = asyncio.Lock()

    async def init(self) -> None:
        """Create the database parent and schema; safe to call more than once."""
        if self._db is not None:
            return
        await asyncio.to_thread(self.path.parent.mkdir, parents=True, exist_ok=True)
        # Let SQLite finish opening so cancellation cannot orphan its connection.
        opening = asyncio.ensure_future(aiosqlite.connect(self.path))
        db = None
        try:
            db = await asyncio.shield(opening)
            db.row_factory = aiosqlite.Row
            await db.execute(
                """CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    tg_user_id INTEGER NOT NULL,
                    tg_username TEXT,
                    tg_full_name TEXT NOT NULL,
                    name TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    phone TEXT NOT NULL,
                    region TEXT NOT NULL,
                    topics TEXT NOT NULL,
                    prior TEXT NOT NULL,
                    call_time TEXT NOT NULL,
                    source TEXT NOT NULL,
                    comment TEXT,
                    script TEXT NOT NULL,
                    delivered INTEGER NOT NULL DEFAULT 0
                )"""
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads (created_at)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_leads_delivered ON leads (delivered)"
            )
            await db.execute(
                """CREATE TABLE IF NOT EXISTS callback_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    tg_user_id INTEGER NOT NULL,
                    tg_username TEXT,
                    tg_full_name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    delivered INTEGER NOT NULL DEFAULT 0
                )"""
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_callback_requests_created_at ON callback_requests (created_at)"
            )
            await db.execute("BEGIN")
            await db.execute(
                """CREATE TABLE IF NOT EXISTS users (
                    tg_user_id INTEGER PRIMARY KEY,
                    tg_username TEXT,
                    tg_full_name TEXT NOT NULL,
                    source TEXT,
                    first_seen_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL
                )"""
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_first_seen_at ON users (first_seen_at)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_last_seen_at ON users (last_seen_at)"
            )
            await db.execute(
                """INSERT OR IGNORE INTO users (
                    tg_user_id, tg_username, tg_full_name, source, first_seen_at, last_seen_at
                )
                SELECT latest.tg_user_id, latest.tg_username, latest.tg_full_name,
                       NULL, history.first_seen_at, history.last_seen_at
                FROM (
                    SELECT MAX(id) AS latest_id,
                           MIN(created_at) AS first_seen_at,
                           MAX(created_at) AS last_seen_at
                    FROM leads
                    WHERE typeof(tg_user_id) = 'integer'
                    GROUP BY tg_user_id
                ) AS history
                JOIN leads AS latest ON latest.id = history.latest_id"""
            )
            async with db.execute(
                "SELECT COUNT(*) FROM leads WHERE typeof(tg_user_id) <> 'integer'"
            ) as cursor:
                row = await cursor.fetchone()
                assert row is not None
                skipped_rows = row[0]
            await db.commit()
            if skipped_rows:
                logger.warning(
                    "Skipped %d lead rows with invalid Telegram user IDs during backfill",
                    skipped_rows,
                )
        except BaseException as error:
            if db is not None or isinstance(error, asyncio.CancelledError):
                cleanup = asyncio.create_task(self._rollback_and_close_after_open(opening))
                try:
                    while not cleanup.done():
                        try:
                            await asyncio.shield(cleanup)
                        except asyncio.CancelledError:
                            logger.debug("Cancellation received while cleaning up SQLite initialization")
                    cleanup.result()
                except (asyncio.CancelledError, Exception):
                    logger.exception("Failed to clean up SQLite after initialization failed")
            raise
        self._db = db

    @staticmethod
    async def _rollback_and_close_after_open(
        opening: asyncio.Future[aiosqlite.Connection],
    ) -> None:
        db = await opening
        try:
            await db.rollback()
        finally:
            await db.close()

    def _connection(self) -> aiosqlite.Connection:
        if self._db is None:
            raise RuntimeError("Storage.init() must be called before using the database")
        return self._db

    @staticmethod
    def _utc_iso(value: datetime | str) -> str:
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at and since must be timezone-aware")
        return value.astimezone(timezone.utc).isoformat()

    @staticmethod
    def _decode_row(row: aiosqlite.Row) -> dict:
        result = dict(row)
        result["topics"] = json.loads(result["topics"])
        return result

    async def save(self, lead: dict) -> int:
        """Insert one lead, assigning a UTC timestamp and delivered=0."""
        db = self._connection()
        created_at = lead.get("created_at")
        if created_at is None:
            created_at = datetime.now(timezone.utc)
        created_at = self._utc_iso(created_at)
        async with self._write_lock:
            try:
                async with db.execute(
                    """INSERT INTO leads (
                        created_at, tg_user_id, tg_username, tg_full_name, name,
                        age, phone, region, topics, prior, call_time, source,
                        comment, script, delivered
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        created_at,
                        lead["tg_user_id"],
                        lead.get("tg_username"),
                        lead["tg_full_name"],
                        lead["name"],
                        lead["age"],
                        lead["phone"],
                        lead["region"],
                        json.dumps(lead["topics"], ensure_ascii=False),
                        lead["prior"],
                        lead["call_time"],
                        lead["source"],
                        lead.get("comment"),
                        lead["script"],
                        UNDELIVERED,
                    ),
                ) as cursor:
                    lead_id = cursor.lastrowid
                if lead_id is None:
                    raise RuntimeError("SQLite did not return a lead id")
                await db.commit()
                return lead_id
            except BaseException:
                await db.rollback()
                raise

    async def mark_delivered(self, lead_id: int) -> None:
        db = self._connection()
        async with self._write_lock:
            try:
                async with db.execute(
                    "UPDATE leads SET delivered = ? WHERE id = ?", (DELIVERED, lead_id)
                ):
                    pass
                await db.commit()
            except BaseException:
                await db.rollback()
                raise

    async def save_callback(self, row: dict) -> int:
        """Insert one callback request with a UTC timestamp."""
        db = self._connection()
        created_at = row.get("created_at")
        if created_at is None:
            created_at = datetime.now(timezone.utc)
        created_at = self._utc_iso(created_at)
        async with self._write_lock:
            try:
                async with db.execute(
                    """INSERT INTO callback_requests (
                        created_at, tg_user_id, tg_username, tg_full_name, phone
                    ) VALUES (?, ?, ?, ?, ?)""",
                    (
                        created_at,
                        row["tg_user_id"],
                        row.get("tg_username"),
                        row["tg_full_name"],
                        row["phone"],
                    ),
                ) as cursor:
                    callback_id = cursor.lastrowid
                if callback_id is None:
                    raise RuntimeError("SQLite did not return a callback request id")
                await db.commit()
                return callback_id
            except BaseException:
                await db.rollback()
                raise

    async def mark_callback_delivered(self, callback_id: int) -> None:
        db = self._connection()
        async with self._write_lock:
            try:
                async with db.execute(
                    "UPDATE callback_requests SET delivered = ? WHERE id = ?",
                    (DELIVERED, callback_id),
                ):
                    pass
                await db.commit()
            except BaseException:
                await db.rollback()
                raise

    async def upsert_user(
        self,
        tg_user_id: int,
        tg_username: str | None,
        tg_full_name: str,
        source: str | None,
        seen_at: datetime,
    ) -> None:
        if not isinstance(tg_user_id, int) or isinstance(tg_user_id, bool):
            raise ValueError("tg_user_id must be an int other than bool")
        db = self._connection()
        seen_at_iso = self._utc_iso(seen_at)
        async with self._write_lock:
            try:
                async with db.execute(
                    """INSERT INTO users (
                        tg_user_id, tg_username, tg_full_name, source, first_seen_at, last_seen_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(tg_user_id) DO UPDATE SET
                        tg_username = excluded.tg_username,
                        tg_full_name = excluded.tg_full_name,
                        source = COALESCE(users.source, excluded.source),
                        last_seen_at = excluded.last_seen_at""",
                    (tg_user_id, tg_username, tg_full_name, source, seen_at_iso, seen_at_iso),
                ):
                    pass
                await db.commit()
            except BaseException:
                await db.rollback()
                raise

    async def _fetch_rows(self, query: str, parameters: tuple = ()) -> list[dict]:
        db = self._connection()
        async with self._write_lock:
            async with db.execute(query, parameters) as cursor:
                rows = await cursor.fetchall()
        return [self._decode_row(row) for row in rows]

    async def _fetch_user_rows(self, query: str, parameters: tuple = ()) -> list[dict]:
        db = self._connection()
        async with self._write_lock:
            async with db.execute(query, parameters) as cursor:
                rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def _fetch_count(self, query: str, parameters: tuple = ()) -> int:
        db = self._connection()
        async with self._write_lock:
            async with db.execute(query, parameters) as cursor:
                row = await cursor.fetchone()
        assert row is not None
        return row[0]

    async def count_users(self) -> int:
        return await self._fetch_count("SELECT COUNT(*) FROM users")

    async def count_lead_users(self) -> int:
        return await self._fetch_count(
            "SELECT COUNT(DISTINCT tg_user_id) FROM leads WHERE typeof(tg_user_id) = 'integer'"
        )

    async def count_undelivered(self) -> int:
        return await self._fetch_count(
            "SELECT COUNT(*) FROM leads WHERE delivered = ?", (UNDELIVERED,)
        )

    async def user_rows_since(self, since: datetime) -> list[dict]:
        since_iso = self._utc_iso(since)
        return await self._fetch_user_rows(
            """SELECT * FROM users
               WHERE first_seen_at >= ? OR last_seen_at >= ?
               ORDER BY first_seen_at, tg_user_id""",
            (since_iso, since_iso),
        )

    async def recent_users(self, limit: int) -> list[dict]:
        return await self._fetch_user_rows(
            """SELECT users.*, EXISTS (
                   SELECT 1 FROM leads WHERE leads.tg_user_id = users.tg_user_id
               ) AS has_lead
               FROM users ORDER BY first_seen_at DESC LIMIT ?""",
            (limit,),
        )

    async def recent_leads(self, limit: int) -> list[dict]:
        return await self._fetch_rows(
            "SELECT * FROM leads ORDER BY created_at DESC, id DESC LIMIT ?",
            (limit,),
        )

    async def undelivered(self, limit: int = DEFAULT_UNDELIVERED_LIMIT) -> list[dict]:
        return await self._fetch_rows(
            "SELECT * FROM leads WHERE delivered = ? ORDER BY created_at, id LIMIT ?",
            (UNDELIVERED, limit),
        )

    async def undelivered_callbacks(
        self, limit: int = DEFAULT_UNDELIVERED_LIMIT
    ) -> list[dict]:
        return await self._fetch_user_rows(
            """SELECT * FROM callback_requests
               WHERE delivered = ? ORDER BY created_at, id LIMIT ?""",
            (UNDELIVERED, limit),
        )

    async def rows_since(self, since: datetime) -> list[dict]:
        return await self._fetch_rows(
            "SELECT * FROM leads WHERE created_at >= ? ORDER BY created_at, id",
            (self._utc_iso(since),),
        )

    async def all_rows(self) -> list[dict]:
        return await self._fetch_rows("SELECT * FROM leads ORDER BY created_at, id")

    async def export_csv(
        self, labels: Mapping[str, Mapping[str, str]] | None = None
    ) -> bytes:
        """Export comma CSV with a BOM, human labels, and formula-safe cells."""
        rows = await self.all_rows()
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(CSV_COLUMNS)
        labels = labels or {}
        for row in rows:
            cells = []
            for column in CSV_COLUMNS:
                value = row[column]
                column_labels = labels.get(column, {})
                if column == "topics":
                    value = ", ".join(column_labels.get(code, code) for code in value)
                elif value is None:
                    value = ""
                else:
                    value = column_labels.get(value, value)
                cell = str(value)
                formatted_phone = (
                    format_uz_phone(cell) if column == PHONE_COLUMN else None
                )
                if formatted_phone is not None:
                    cell = formatted_phone
                else:
                    cell = _guard_csv_formula(cell)
                cells.append(cell)
            writer.writerow(cells)
        return output.getvalue().encode("utf-8-sig")

    async def export_users_csv(self) -> bytes:
        """Export users as comma CSV with a BOM and formula-safe cells."""
        rows = await self._fetch_user_rows("SELECT * FROM users ORDER BY first_seen_at, tg_user_id")
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(USER_CSV_COLUMNS)
        for row in rows:
            cells = []
            for column in USER_CSV_COLUMNS:
                value = row[column]
                cells.append(_guard_users_csv_formula("" if value is None else str(value)))
            writer.writerow(cells)
        return output.getvalue().encode("utf-8-sig")

    async def close(self) -> None:
        async with self._write_lock:
            if self._db is not None:
                db = self._db
                await db.close()
                self._db = None
