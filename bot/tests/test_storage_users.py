"""User storage contract tests using a temporary SQLite database."""

import asyncio
import codecs
import csv
import io
import logging
from datetime import datetime, timedelta, timezone

import aiosqlite
import pytest

from storage import Storage


FIRST_SEEN = datetime(2026, 11, 20, tzinfo=timezone.utc)
LATER_SEEN = FIRST_SEEN + timedelta(days=1)
RECOVERY_TIMEOUT_SECONDS = 2


def make_lead(**overrides: object) -> dict:
    lead = {
        "created_at": FIRST_SEEN,
        "tg_user_id": 1,
        "tg_username": "aziza",
        "tg_full_name": "Aziza Karimova",
        "name": "Aziza Karimova",
        "age": 34,
        "phone": "+998901234567",
        "region": "tashkent_city",
        "topics": ["family", "fear"],
        "prior": "no",
        "call_time": "evening",
        "source": "ig",
        "script": "lat",
    }
    lead.update(overrides)
    return lead


def record_connection_cleanup(
    monkeypatch: pytest.MonkeyPatch, db: aiosqlite.Connection, calls: list[str]
) -> None:
    rollback = db.rollback
    close = db.close

    async def record_rollback() -> None:
        await rollback()
        calls.append("rollback")

    async def record_close() -> None:
        calls.append("close")
        await close()

    monkeypatch.setattr(db, "rollback", record_rollback)
    monkeypatch.setattr(db, "close", record_close)


@pytest.mark.asyncio
async def test_upsert_inserts_user_with_utc_timestamps(tmp_path) -> None:
    storage = Storage(tmp_path / "leads.db")
    await storage.init()
    try:
        seen_at = FIRST_SEEN.astimezone(timezone(timedelta(hours=5)))
        await storage.upsert_user(1, "aziza", "Aziza Karimova", "ig", seen_at)

        assert await storage.user_rows_since(FIRST_SEEN) == [
            {
                "tg_user_id": 1,
                "tg_username": "aziza",
                "tg_full_name": "Aziza Karimova",
                "source": "ig",
                "first_seen_at": FIRST_SEEN.isoformat(),
                "last_seen_at": FIRST_SEEN.isoformat(),
            }
        ]
    finally:
        await storage.close()


@pytest.mark.asyncio
async def test_upsert_updates_profile_and_last_seen_and_keeps_first_source(tmp_path) -> None:
    storage = Storage(tmp_path / "leads.db")
    await storage.init()
    try:
        await storage.upsert_user(1, "aziza", "Aziza Karimova", "ig", FIRST_SEEN)
        await storage.upsert_user(1, None, "Aziza Ahmedova", "tg", LATER_SEEN)

        assert await storage.count_users() == 1
        assert await storage.user_rows_since(FIRST_SEEN) == [
            {
                "tg_user_id": 1,
                "tg_username": None,
                "tg_full_name": "Aziza Ahmedova",
                "source": "ig",
                "first_seen_at": FIRST_SEEN.isoformat(),
                "last_seen_at": LATER_SEEN.isoformat(),
            }
        ]
    finally:
        await storage.close()


@pytest.mark.asyncio
async def test_upsert_fills_missing_source_on_later_visit(tmp_path) -> None:
    storage = Storage(tmp_path / "leads.db")
    await storage.init()
    try:
        await storage.upsert_user(1, None, "Aziza", None, FIRST_SEEN)
        await storage.upsert_user(1, None, "Aziza", "yt", LATER_SEEN)

        [user] = await storage.user_rows_since(FIRST_SEEN)
        assert user["source"] == "yt"
    finally:
        await storage.close()


@pytest.mark.asyncio
async def test_upsert_rejects_naive_datetime(tmp_path) -> None:
    storage = Storage(tmp_path / "leads.db")
    await storage.init()
    try:
        with pytest.raises(ValueError, match="timezone-aware"):
            await storage.upsert_user(1, None, "Aziza", None, FIRST_SEEN.replace(tzinfo=None))
        assert await storage.count_users() == 0
    finally:
        await storage.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("tg_user_id", [None, True, False, "42", 4.5])
async def test_upsert_rejects_non_integer_user_id(tmp_path, tg_user_id) -> None:
    storage = Storage(tmp_path / "leads.db")
    await storage.init()
    try:
        with pytest.raises(ValueError, match="tg_user_id must be an int"):
            await storage.upsert_user(tg_user_id, None, "Aziza", None, FIRST_SEEN)
        assert await storage.count_users() == 0
    finally:
        await storage.close()


@pytest.mark.asyncio
async def test_init_backfills_each_lead_user_with_profile_from_highest_lead_id(tmp_path) -> None:
    path = tmp_path / "leads.db"
    storage = Storage(path)
    await storage.init()
    try:
        await storage.save(make_lead(created_at=LATER_SEEN))
        await storage.save(make_lead(tg_user_id=2, tg_username=None, tg_full_name="Kamol"))
        await storage.save(make_lead(tg_username="aziza_new", tg_full_name="Aziza Ahmedova"))
    finally:
        await storage.close()

    reopened = Storage(path)
    await reopened.init()
    try:
        assert await reopened.count_users() == 2
        assert await reopened.user_rows_since(FIRST_SEEN) == [
            {
                "tg_user_id": 1,
                "tg_username": "aziza_new",
                "tg_full_name": "Aziza Ahmedova",
                "source": None,
                "first_seen_at": FIRST_SEEN.isoformat(),
                "last_seen_at": LATER_SEEN.isoformat(),
            },
            {
                "tg_user_id": 2,
                "tg_username": None,
                "tg_full_name": "Kamol",
                "source": None,
                "first_seen_at": FIRST_SEEN.isoformat(),
                "last_seen_at": FIRST_SEEN.isoformat(),
            },
        ]
    finally:
        await reopened.close()


@pytest.mark.asyncio
async def test_init_skips_invalid_lead_user_ids_and_counts_only_valid_ids(tmp_path, caplog) -> None:
    path = tmp_path / "leads.db"
    async with aiosqlite.connect(path) as db:
        # This legacy fixture allows NULL, unlike the current leads schema.
        await db.execute(
            """CREATE TABLE leads (
                id INTEGER PRIMARY KEY, created_at TEXT, tg_user_id INTEGER,
                tg_username TEXT, tg_full_name TEXT, delivered INTEGER
            )"""
        )
        await db.executemany(
            "INSERT INTO leads (created_at, tg_user_id, tg_full_name) VALUES (?, ?, ?)",
            [(FIRST_SEEN.isoformat(), user_id, "Legacy Name")
             for user_id in (1, None, "invalid-id", 4.5, "invalid-id")],
        )
        await db.commit()

    storage = Storage(path)
    try:
        with caplog.at_level(logging.WARNING, logger="storage"):
            await storage.init()
        [user] = await storage.user_rows_since(FIRST_SEEN)
        assert user["tg_user_id"] == 1
        assert await storage.count_lead_users() == 1
        assert caplog.record_tuples == [
            ("storage", logging.WARNING, "Skipped 4 lead rows with invalid Telegram user IDs during backfill")
        ]
    finally:
        await storage.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("cancel_twice", [False, True], ids=["single", "double"])
async def test_init_closes_connection_when_cancelled_during_open(
    tmp_path, monkeypatch, cancel_twice
) -> None:
    storage = Storage(tmp_path / "leads.db")
    connect = aiosqlite.connect
    connection_opened = asyncio.Event()
    finish_opening = asyncio.Event()
    cleanup_calls: list[str] = []
    db = None

    async def delayed_connect(path):
        nonlocal db
        db = await connect(path)
        record_connection_cleanup(patcher, db, cleanup_calls)
        connection_opened.set()
        await finish_opening.wait()
        return db

    try:
        with monkeypatch.context() as patcher:
            patcher.setattr(aiosqlite, "connect", delayed_connect)
            task = asyncio.create_task(storage.init())
            await connection_opened.wait()
            task.cancel("initial cancellation")
            if cancel_twice:
                # Let init enter its cleanup while the open is still pending.
                await asyncio.sleep(0)
                task.cancel("second cancellation")
            finish_opening.set()
            with pytest.raises(asyncio.CancelledError) as cancellation:
                await task

        assert cleanup_calls == ["rollback", "close"]
        assert db is not None
        with pytest.raises(ValueError, match="no active connection"):
            await db.execute("SELECT 1")
        assert str(cancellation.value) == "initial cancellation"
        await storage.init()
        await asyncio.wait_for(
            storage.upsert_user(1, None, "Recovered User", None, FIRST_SEEN),
            timeout=RECOVERY_TIMEOUT_SECONDS,
        )
        assert await storage.count_users() == 1
    finally:
        if db is not None:
            await db.close()
        await storage.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("failure", "cancel_during_rollback"),
    [
        pytest.param(RuntimeError, False, id="error"),
        pytest.param(asyncio.CancelledError, False, id="cancelled"),
        pytest.param(asyncio.CancelledError, True, id="cancelled-again-during-rollback"),
    ],
)
async def test_init_rolls_back_and_closes_connection_on_backfill_failure(
    tmp_path, monkeypatch, failure, cancel_during_rollback
) -> None:
    path = tmp_path / "leads.db"
    storage = Storage(path)
    execute = aiosqlite.Connection.execute
    cleanup_calls: list[str] = []
    db = None

    async def fail_after_backfill(connection, sql, parameters=None):
        nonlocal db
        cursor = await execute(connection, sql, parameters)
        if sql.startswith("INSERT OR IGNORE INTO users"):
            await cursor.close()
            db = connection
            record_connection_cleanup(patcher, db, cleanup_calls)
            if failure is asyncio.CancelledError:
                task = asyncio.current_task()
                assert task is not None
                if cancel_during_rollback:
                    rollback = connection.rollback

                    async def cancel_then_rollback() -> None:
                        task.cancel("second cancellation")
                        await asyncio.sleep(0)
                        await rollback()

                    patcher.setattr(connection, "rollback", cancel_then_rollback)
                task.cancel("backfill interrupted")
                await asyncio.Event().wait()
            raise failure("backfill interrupted")
        return cursor

    try:
        with monkeypatch.context() as patcher:
            patcher.setattr(aiosqlite.Connection, "execute", fail_after_backfill)
            with pytest.raises(failure, match="backfill interrupted"):
                await asyncio.create_task(storage.init())

        assert cleanup_calls == ["rollback", "close"]
        assert db is not None
        with pytest.raises(ValueError, match="no active connection"):
            await db.execute("SELECT 1")
        async with aiosqlite.connect(path) as probe:
            async with probe.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'users'"
            ) as cursor:
                assert await cursor.fetchone() is None
        await storage.init()
        assert await storage.count_users() == 0
        await asyncio.wait_for(
            storage.upsert_user(1, None, "Recovered User", None, FIRST_SEEN),
            timeout=RECOVERY_TIMEOUT_SECONDS,
        )
        assert await storage.count_users() == 1
    finally:
        if db is not None:
            await db.close()
        await storage.close()


@pytest.mark.asyncio
async def test_init_creates_lead_and_user_indexes(tmp_path) -> None:
    path = tmp_path / "leads.db"
    storage = Storage(path)
    await storage.init()
    try:
        async with aiosqlite.connect(path) as db:
            async with db.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'index' AND tbl_name IN ('leads', 'users') LIMIT 4"
            ) as cursor:
                assert {name for (name,) in await cursor.fetchall()} == {
                    "idx_leads_created_at",
                    "idx_leads_delivered",
                    "idx_users_first_seen_at",
                    "idx_users_last_seen_at",
                }
    finally:
        await storage.close()


@pytest.mark.asyncio
async def test_repeated_init_preserves_existing_user_rows(tmp_path) -> None:
    path = tmp_path / "leads.db"
    storage = Storage(path)
    await storage.init()
    try:
        await storage.upsert_user(1, "current", "Current Name", "yt", LATER_SEEN)
        await storage.save(make_lead())
        await storage.save(make_lead(tg_user_id=2))
        [existing_user] = await storage.user_rows_since(FIRST_SEEN)
    finally:
        await storage.close()

    reopened = Storage(path)
    for _ in range(2):
        await reopened.init()
        try:
            await reopened.init()
            assert await reopened.count_users() == 2
            assert await reopened.user_rows_since(LATER_SEEN) == [existing_user]
        finally:
            await reopened.close()


@pytest.mark.asyncio
async def test_counts_users_distinct_lead_users_and_undelivered_leads(tmp_path) -> None:
    storage = Storage(tmp_path / "leads.db")
    await storage.init()
    try:
        assert await storage.count_users() == 0
        assert await storage.count_lead_users() == 0
        assert await storage.count_undelivered() == 0

        await storage.upsert_user(1, None, "Aziza", None, FIRST_SEEN)
        delivered_id = await storage.save(make_lead())
        await storage.save(make_lead())
        await storage.save(make_lead(tg_user_id=2))
        await storage.mark_delivered(delivered_id)

        assert await storage.count_users() == 1
        assert await storage.count_lead_users() == 2
        assert await storage.count_undelivered() == 2
    finally:
        await storage.close()


@pytest.mark.asyncio
async def test_user_rows_since_matches_either_timestamp_and_orders_by_first_seen(tmp_path) -> None:
    storage = Storage(tmp_path / "leads.db")
    await storage.init()
    try:
        await storage.upsert_user(3, None, "Returning User", None, FIRST_SEEN)
        await storage.upsert_user(3, None, "Returning User", None, LATER_SEEN)
        await storage.upsert_user(2, None, "New User", None, LATER_SEEN)
        await storage.upsert_user(1, None, "Older User", None, FIRST_SEEN)
        await storage.upsert_user(4, None, "Backdated Visit", None, LATER_SEEN)
        await storage.upsert_user(4, None, "Backdated Visit", None, FIRST_SEEN)

        since = LATER_SEEN.astimezone(timezone(timedelta(hours=5)))
        rows = await storage.user_rows_since(since)
        assert [row["tg_user_id"] for row in rows] == [3, 2, 4]
    finally:
        await storage.close()


@pytest.mark.asyncio
async def test_export_users_csv_has_bom_order_header_and_formula_guard(tmp_path) -> None:
    storage = Storage(tmp_path / "leads.db")
    await storage.init()
    try:
        await storage.upsert_user(1, "@user", "Later User", "+src", LATER_SEEN)
        await storage.upsert_user(3, None, "Same First Seen", None, FIRST_SEEN)
        await storage.upsert_user(2, None, "=cmd", None, FIRST_SEEN)

        data = await storage.export_users_csv()
        assert data.startswith(codecs.BOM_UTF8)
        reader = csv.reader(io.StringIO(data.decode("utf-8-sig")))
        assert next(reader) == [
            "tg_user_id", "tg_username", "tg_full_name", "source", "first_seen_at", "last_seen_at"
        ]
        first_seen = FIRST_SEEN.isoformat()
        later_seen = LATER_SEEN.isoformat()
        assert list(reader) == [
            ["2", "", "'=cmd", "", first_seen, first_seen],
            ["3", "", "Same First Seen", "", first_seen, first_seen],
            ["1", "'@user", "Later User", "'+src", later_seen, later_seen],
        ]
    finally:
        await storage.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("cell", [" =pending", "\n=1+1", " \t+1", "\xa0-1", "\x00\x1b@user", "\ufeff=1"])
async def test_export_users_csv_guards_formulas_after_whitespace_and_controls(tmp_path, cell) -> None:
    storage = Storage(tmp_path / "leads.db")
    await storage.init()
    try:
        await storage.upsert_user(1, cell, " Plain Name", cell, FIRST_SEEN)
        data = await storage.export_users_csv()
        reader = csv.reader(io.StringIO(data.decode("utf-8-sig"), newline=""))
        next(reader)
        [row] = reader
        assert row[1:4] == ["'" + cell, " Plain Name", "'" + cell]
    finally:
        await storage.close()


@pytest.mark.asyncio
async def test_upsert_rolls_back_when_commit_fails(tmp_path, monkeypatch) -> None:
    storage = Storage(tmp_path / "leads.db")
    await storage.init()
    cleanup_calls: list[str] = []
    try:
        assert storage._db is not None
        record_connection_cleanup(monkeypatch, storage._db, cleanup_calls)
        await storage.upsert_user(1, "original", "Original Name", None, FIRST_SEEN)
        rows_before = await storage.user_rows_since(FIRST_SEEN)

        async def fail_commit() -> None:
            raise RuntimeError("commit failed")

        with monkeypatch.context() as patcher:
            patcher.setattr(storage._db, "commit", fail_commit)
            with pytest.raises(RuntimeError, match="commit failed"):
                await storage.upsert_user(1, "updated", "Updated Name", "ig", LATER_SEEN)

        assert cleanup_calls == ["rollback"]
        assert await storage.user_rows_since(FIRST_SEEN) == rows_before
        await storage.upsert_user(1, "retry", "Retried Name", "ig", LATER_SEEN)
        [user] = await storage.user_rows_since(LATER_SEEN)
        assert user["tg_username"] == "retry"
    finally:
        await storage.close()
    assert cleanup_calls == ["rollback", "close"]
