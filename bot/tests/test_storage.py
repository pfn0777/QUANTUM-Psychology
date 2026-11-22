"""Storage contract tests using a temporary SQLite database."""

import asyncio
import csv
import io
from datetime import datetime, timedelta, timezone

import pytest

from storage import Storage


EXPECTED_COLUMNS = [
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
]


def make_lead(**overrides: object) -> dict:
    lead = {
        "tg_user_id": 123456,
        "tg_username": "aziza",
        "tg_full_name": "Азиза Каримова",
        "name": "Азиза Каримова",
        "age": 34,
        "phone": "+998901234567",
        "region": "tashkent_city",
        "topics": ["family", "fear"],
        "prior": "no",
        "call_time": "evening",
        "source": "ig",
        "comment": "Суҳбат керак",
        "script": "cyr",
    }
    lead.update(overrides)
    return lead


def csv_rows(data: bytes) -> list[dict[str, str]]:
    assert data.startswith(b"\xef\xbb\xbf")
    return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))


@pytest.mark.asyncio
async def test_init_twice_and_round_trip_all_fields(tmp_path) -> None:
    path = tmp_path / "nested" / "leads.db"
    storage = Storage(path)
    await storage.init()
    await storage.init()
    try:
        first = make_lead()
        first_id = await storage.save(first)
        second_id = await storage.save(make_lead(name="Иккинчи"))
        assert second_id > first_id
        assert path.is_file()

        rows = await storage.all_rows()
        assert len(rows) == 2
        for key, value in first.items():
            assert rows[0][key] == value
        assert rows[0]["id"] == first_id
        assert rows[0]["delivered"] == 0
        assert isinstance(rows[0]["topics"], list)
        timestamp = datetime.fromisoformat(rows[0]["created_at"])
        assert timestamp.utcoffset() == timedelta(0)
        assert abs(datetime.now(timezone.utc) - timestamp) < timedelta(minutes=1)
    finally:
        await storage.close()


@pytest.mark.asyncio
async def test_undelivered_oldest_first_limit_and_mark(tmp_path) -> None:
    storage = Storage(tmp_path / "leads.db")
    await storage.init()
    try:
        newer_id = await storage.save(
            make_lead(created_at="2026-11-20T11:00:00+00:00")
        )
        older_id = await storage.save(
            make_lead(created_at="2026-11-20T10:00:00+00:00")
        )
        assert [row["id"] for row in await storage.undelivered(limit=1)] == [older_id]
        assert [row["id"] for row in await storage.undelivered()] == [
            older_id,
            newer_id,
        ]
        await storage.mark_delivered(older_id)
        assert [row["id"] for row in await storage.undelivered()] == [newer_id]
        assert next(row for row in await storage.all_rows() if row["id"] == older_id)[
            "delivered"
        ] == 1
    finally:
        await storage.close()


@pytest.mark.asyncio
async def test_rows_since_filters_aware_utc_time(tmp_path) -> None:
    storage = Storage(tmp_path / "leads.db")
    await storage.init()
    try:
        old_id = await storage.save(
            make_lead(created_at="2026-11-19T23:59:59+00:00")
        )
        edge_id = await storage.save(
            make_lead(created_at="2026-11-20T05:00:00+05:00")
        )
        recent_id = await storage.save(
            make_lead(created_at="2026-11-20T01:00:00+00:00")
        )
        assert [row["id"] for row in await storage.rows_since(
            datetime(2026, 11, 20, tzinfo=timezone.utc)
        )] == [edge_id, recent_id]
        assert old_id not in [row["id"] for row in await storage.rows_since(
            datetime(2026, 11, 20, tzinfo=timezone.utc)
        )]
        with pytest.raises(ValueError, match="timezone-aware"):
            await storage.rows_since(datetime(2026, 11, 20))
    finally:
        await storage.close()


@pytest.mark.asyncio
async def test_export_csv_labels_bom_and_formula_guard(tmp_path) -> None:
    storage = Storage(tmp_path / "leads.db")
    await storage.init()
    try:
        await storage.save(
            make_lead(
                name="=HYPERLINK(\"https://example.test\")",
                phone="+998901234567",
                tg_username="@x",
                comment="-1",
                topics=["family", "fear"],
            )
        )
        await storage.save(make_lead(tg_full_name="\tTabbed", comment="\rCarriage"))
        data = await storage.export_csv(
            labels={
                "region": {"tashkent_city": "Тошкент шаҳри"},
                "topics": {"family": "Оила", "fear": "Қўрқув"},
                "prior": {"no": "Йўқ"},
            }
        )
        assert data.startswith(b"\xef\xbb\xbf")
        assert next(csv.reader(io.StringIO(data.decode("utf-8-sig")))) == EXPECTED_COLUMNS
        rows = csv_rows(data)
        row = rows[0]
        assert row["name"] == "'=HYPERLINK(\"https://example.test\")"
        assert row["phone"] == "998 90 123 45 67"
        assert row["comment"] == "'-1"
        assert row["tg_username"] == "'@x"
        assert row["topics"] == "Оила, Қўрқув"
        assert row["region"] == "Тошкент шаҳри"
        assert row["prior"] == "Йўқ"
        assert rows[1]["tg_full_name"] == "'\tTabbed"
        assert rows[1]["comment"] == "'\rCarriage"
    finally:
        await storage.close()


@pytest.mark.asyncio
async def test_export_csv_formats_uzbek_phone_without_plus_or_quote(tmp_path) -> None:
    storage = Storage(tmp_path / "leads.db")
    await storage.init()
    try:
        await storage.save(make_lead(phone="+998901234567"))
        rows = csv_rows(await storage.export_csv())
        assert rows[0]["phone"] == "998 90 123 45 67"
        stored = await storage.all_rows()
        assert stored[0]["phone"] == "+998901234567"
    finally:
        await storage.close()


@pytest.mark.asyncio
async def test_export_csv_keeps_guard_on_foreign_phone(tmp_path) -> None:
    storage = Storage(tmp_path / "leads.db")
    await storage.init()
    try:
        await storage.save(make_lead(phone="+79123456789"))
        rows = csv_rows(await storage.export_csv())
        assert rows[0]["phone"] == "'+79123456789"
    finally:
        await storage.close()


@pytest.mark.asyncio
async def test_export_csv_keeps_formula_guard_on_name_and_comment(tmp_path) -> None:
    storage = Storage(tmp_path / "leads.db")
    await storage.init()
    try:
        await storage.save(make_lead(name="=1+1", comment="=SUM(A1)"))
        rows = csv_rows(await storage.export_csv())
        assert rows[0]["name"] == "'=1+1"
        assert rows[0]["comment"] == "'=SUM(A1)"
    finally:
        await storage.close()


@pytest.mark.asyncio
async def test_sql_like_name_is_literal_and_table_survives(tmp_path) -> None:
    storage = Storage(tmp_path / "leads.db")
    await storage.init()
    try:
        suspicious_name = "'); DROP TABLE leads;--"
        await storage.save(make_lead(name=suspicious_name))
        assert (await storage.all_rows())[0]["name"] == suspicious_name
        await storage.save(make_lead(name="Иккинчи"))
        assert len(await storage.all_rows()) == 2
    finally:
        await storage.close()


@pytest.mark.asyncio
async def test_empty_export_has_only_header(tmp_path) -> None:
    storage = Storage(tmp_path / "leads.db")
    await storage.init()
    try:
        data = await storage.export_csv()
        assert data.startswith(b"\xef\xbb\xbf")
        assert list(csv.reader(io.StringIO(data.decode("utf-8-sig")))) == [
            EXPECTED_COLUMNS
        ]
    finally:
        await storage.close()


@pytest.mark.asyncio
async def test_failed_commit_rolls_back_save_and_delivery(tmp_path, monkeypatch) -> None:
    storage = Storage(tmp_path / "leads.db")
    await storage.init()
    try:
        assert storage._db is not None

        async def fail_commit() -> None:
            raise RuntimeError("commit failed")

        with monkeypatch.context() as patcher:
            patcher.setattr(storage._db, "commit", fail_commit)
            with pytest.raises(RuntimeError, match="commit failed"):
                await storage.save(make_lead())
        assert await storage.all_rows() == []

        lead_id = await storage.save(make_lead())
        with monkeypatch.context() as patcher:
            patcher.setattr(storage._db, "commit", fail_commit)
            with pytest.raises(RuntimeError, match="commit failed"):
                await storage.mark_delivered(lead_id)
        assert (await storage.all_rows())[0]["delivered"] == 0

        await storage.mark_delivered(lead_id)
        assert (await storage.all_rows())[0]["delivered"] == 1
    finally:
        await storage.close()


@pytest.mark.asyncio
async def test_cancelled_save_rolls_back_before_next_commit(tmp_path, monkeypatch) -> None:
    storage = Storage(tmp_path / "leads.db")
    await storage.init()
    try:
        assert storage._db is not None
        commit_started = asyncio.Event()
        never_released = asyncio.Event()

        async def pause_commit() -> None:
            commit_started.set()
            await never_released.wait()

        with monkeypatch.context() as patcher:
            patcher.setattr(storage._db, "commit", pause_commit)
            save_task = asyncio.create_task(storage.save(make_lead(name="Cancelled")))
            await commit_started.wait()
            save_task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await save_task

        assert await storage.all_rows() == []
        await storage.save(make_lead(name="Retained"))
        assert [row["name"] for row in await storage.all_rows()] == ["Retained"]
    finally:
        await storage.close()


@pytest.mark.asyncio
async def test_close_waits_for_active_write(tmp_path, monkeypatch) -> None:
    path = tmp_path / "leads.db"
    storage = Storage(path)
    await storage.init()
    try:
        assert storage._db is not None
        original_commit = storage._db.commit
        commit_started = asyncio.Event()
        release_commit = asyncio.Event()

        async def pause_commit() -> None:
            commit_started.set()
            await release_commit.wait()
            await original_commit()

        with monkeypatch.context() as patcher:
            patcher.setattr(storage._db, "commit", pause_commit)
            save_task = asyncio.create_task(storage.save(make_lead()))
            await commit_started.wait()
            close_task = asyncio.create_task(storage.close())
            try:
                await asyncio.sleep(0)
                assert not close_task.done()
            finally:
                release_commit.set()
            await save_task
            await close_task

        reopened = Storage(path)
        await reopened.init()
        try:
            assert len(await reopened.all_rows()) == 1
        finally:
            await reopened.close()
    finally:
        await storage.close()
