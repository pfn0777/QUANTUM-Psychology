"""Async SQLite storage for consultation leads."""

import asyncio
import csv
import io
import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite


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
CSV_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
DEFAULT_UNDELIVERED_LIMIT = 50
UNDELIVERED = 0
DELIVERED = 1


class Storage:
    """Store leads; returned rows contain a topics list and delivered as int 0 or 1."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._db: aiosqlite.Connection | None = None
        self._write_lock = asyncio.Lock()

    async def init(self) -> None:
        """Create the database parent and schema; safe to call more than once."""
        if self._db is not None:
            return
        await asyncio.to_thread(self.path.parent.mkdir, parents=True, exist_ok=True)
        db = await aiosqlite.connect(self.path)
        try:
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
            await db.commit()
        except Exception:
            await db.close()
            raise
        self._db = db

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

    async def _fetch_rows(self, query: str, parameters: tuple = ()) -> list[dict]:
        db = self._connection()
        async with self._write_lock:
            async with db.execute(query, parameters) as cursor:
                rows = await cursor.fetchall()
        return [self._decode_row(row) for row in rows]

    async def undelivered(self, limit: int = DEFAULT_UNDELIVERED_LIMIT) -> list[dict]:
        return await self._fetch_rows(
            "SELECT * FROM leads WHERE delivered = ? ORDER BY created_at, id LIMIT ?",
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
                if cell.startswith(CSV_FORMULA_PREFIXES):
                    cell = "'" + cell
                cells.append(cell)
            writer.writerow(cells)
        return output.getvalue().encode("utf-8-sig")

    async def close(self) -> None:
        async with self._write_lock:
            if self._db is not None:
                db = self._db
                await db.close()
                self._db = None
