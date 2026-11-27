"""Callback request storage tests using a temporary SQLite database."""

from datetime import datetime, timedelta, timezone

import pytest

from storage import Storage


def make_callback(**overrides: object) -> dict:
    row = {
        "tg_user_id": 123456,
        "tg_username": "tester",
        "tg_full_name": "Test User",
        "phone": "+998901234567",
    }
    row.update(overrides)
    return row


def make_lead() -> dict:
    return {
        **make_callback(),
        "name": "Test User",
        "age": 34,
        "region": "tashkent_city",
        "topics": ["family"],
        "prior": "no",
        "call_time": "evening",
        "source": "ig",
        "comment": None,
        "script": "lat",
    }


@pytest.mark.asyncio
async def test_save_callback_round_trip_and_nullable_username(tmp_db_path) -> None:
    storage = Storage(tmp_db_path)
    await storage.init()
    try:
        callback = make_callback(tg_username=None)
        callback_id = await storage.save_callback(callback)
        rows = await storage.undelivered_callbacks()

        assert len(rows) == 1
        assert rows[0]["id"] == callback_id
        assert rows[0]["delivered"] == 0
        for key, value in callback.items():
            assert rows[0][key] == value
        assert set(rows[0]) == {
            "id", "created_at", "tg_user_id", "tg_username",
            "tg_full_name", "phone", "delivered",
        }
        timestamp = datetime.fromisoformat(rows[0]["created_at"])
        assert timestamp.utcoffset() == timedelta(0)
        assert abs(datetime.now(timezone.utc) - timestamp) < timedelta(minutes=1)
    finally:
        await storage.close()


@pytest.mark.asyncio
async def test_undelivered_callbacks_oldest_first_limit_and_mark(tmp_db_path) -> None:
    storage = Storage(tmp_db_path)
    await storage.init()
    try:
        newer_id = await storage.save_callback(
            make_callback(created_at="2026-11-20T11:00:00+00:00")
        )
        older_id = await storage.save_callback(
            make_callback(created_at="2026-11-20T15:00:00+05:00")
        )
        assert [row["id"] for row in await storage.undelivered_callbacks(limit=1)] == [
            older_id
        ]
        assert [row["id"] for row in await storage.undelivered_callbacks()] == [
            older_id, newer_id
        ]
        assert (await storage.undelivered_callbacks(limit=1))[0]["created_at"] == (
            "2026-11-20T10:00:00+00:00"
        )

        await storage.mark_callback_delivered(older_id)
        assert [row["id"] for row in await storage.undelivered_callbacks()] == [newer_id]
        assert storage._db is not None
        async with storage._db.execute(
            "SELECT delivered FROM callback_requests WHERE id = ?", (older_id,)
        ) as cursor:
            assert (await cursor.fetchone())[0] == 1
    finally:
        await storage.close()


@pytest.mark.asyncio
async def test_init_twice_preserves_existing_leads_and_callbacks(tmp_db_path) -> None:
    storage = Storage(tmp_db_path)
    await storage.init()
    try:
        lead_id = await storage.save(make_lead())
        callback_id = await storage.save_callback(make_callback())
        await storage.init()
        assert [row["id"] for row in await storage.all_rows()] == [lead_id]
        assert [row["id"] for row in await storage.undelivered_callbacks()] == [
            callback_id
        ]
    finally:
        await storage.close()

    reopened = Storage(tmp_db_path)
    await reopened.init()
    try:
        assert [row["id"] for row in await reopened.all_rows()] == [lead_id]
        assert [row["id"] for row in await reopened.undelivered_callbacks()] == [
            callback_id
        ]
    finally:
        await reopened.close()
