"""Dashboard payload and recent SQLite rows for the admin Mini App."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from dashboard import DAILY_DAYS, RECENT_LIMIT, build_dashboard
from storage import Storage


NOW = datetime(2026, 11, 22, 19, tzinfo=timezone.utc)


def user_row(seen_at: datetime = NOW, **overrides: object) -> dict:
    return {
        "first_seen_at": seen_at.isoformat(),
        "last_seen_at": seen_at.isoformat(),
        "tg_full_name": "Example User",
        "tg_username": None,
        "source": None,
        "has_lead": 0,
        **overrides,
    }


def lead_row(created_at: datetime = NOW, **overrides: object) -> dict:
    return {
        "created_at": created_at.isoformat(),
        "tg_user_id": 1,
        "tg_username": "tester",
        "tg_full_name": "Example User",
        "name": "Example Lead",
        "phone": "+998901234567",
        "age": 34,
        "region": "tashkent_city",
        "topics": ["family", "fear"],
        "prior": "no",
        "call_time": "evening",
        "source": "ig",
        "script": "cyr",
        **overrides,
    }


def dashboard(
    *,
    total_users: int = 0,
    user_rows: list[dict] | None = None,
    lead_rows: list[dict] | None = None,
    lead_user_count: int = 0,
    undelivered: int = 0,
    recent_leads: list[dict] | None = None,
    recent_users: list[dict] | None = None,
    now_utc: datetime = NOW,
) -> dict:
    return build_dashboard(
        total_users=total_users,
        user_rows=user_rows or [],
        lead_user_count=lead_user_count,
        lead_rows=lead_rows or [],
        undelivered=undelivered,
        recent_leads=recent_leads or [],
        recent_users=recent_users or [],
        now_utc=now_utc,
    )


def test_empty_dashboard_has_exact_contract_and_zero_filled_daily_series() -> None:
    result = dashboard()

    assert set(result) == {"generated_at", "totals", "daily", "sources", "leads", "users"}
    assert result["generated_at"] == "2026-11-22T19:00:00+00:00"
    assert result["totals"] == {
        "users": 0,
        "users_today": 0,
        "users_7d": 0,
        "users_30d": 0,
        "active_7d": 0,
        "lead_users": 0,
        "conversion_pct": None,
        "leads_today": 0,
        "leads_7d": 0,
        "leads_30d": 0,
        "undelivered": 0,
    }
    assert DAILY_DAYS == 30
    oldest_date = datetime(2026, 10, 25).date()
    assert result["daily"] == [
        {"date": (oldest_date + timedelta(days=offset)).isoformat(), "users": 0, "leads": 0}
        for offset in range(DAILY_DAYS)
    ]
    assert result["leads"] == result["users"] == []


@pytest.mark.parametrize(
    ("now_utc", "today", "daily_day_counts"),
    [
        (NOW - timedelta(minutes=1), "2026-11-22", (0, 1)),
        (NOW, "2026-11-23", (1, 1)),
    ],
)
def test_today_and_daily_counts_switch_at_tashkent_midnight(
    now_utc: datetime, today: str, daily_day_counts: tuple[int, int]
) -> None:
    before_midnight = NOW - timedelta(minutes=1)
    result = dashboard(
        total_users=2,
        user_rows=[user_row(before_midnight), user_row(NOW)],
        lead_rows=[lead_row(before_midnight), lead_row(NOW)],
        now_utc=now_utc,
    )

    assert result["totals"]["users_today"] == result["totals"]["leads_today"] == 1
    assert result["daily"][-1]["date"] == today
    assert tuple(day["users"] for day in result["daily"][-2:]) == daily_day_counts
    assert tuple(day["leads"] for day in result["daily"][-2:]) == daily_day_counts


def test_rolling_totals_include_boundaries_and_count_returning_users_as_active() -> None:
    seven_days_ago = NOW - timedelta(days=7)
    thirty_days_ago = NOW - timedelta(days=30)
    just_outside = timedelta(seconds=1)
    result = dashboard(
        total_users=6,
        lead_user_count=1,
        undelivered=2,
        user_rows=[
            user_row(seven_days_ago),
            user_row(thirty_days_ago, last_seen_at=NOW.isoformat()),
            user_row(thirty_days_ago - just_outside),
            user_row(seven_days_ago - just_outside),
            user_row(NOW + just_outside),
        ],
        lead_rows=[
            lead_row(seven_days_ago),
            lead_row(thirty_days_ago),
            lead_row(thirty_days_ago - just_outside),
            lead_row(seven_days_ago - just_outside),
            lead_row(NOW + just_outside),
        ],
    )

    assert result["totals"] == {
        "users": 6,
        "users_today": 0,
        "users_7d": 1,
        "users_30d": 3,
        "active_7d": 2,
        "lead_users": 1,
        "conversion_pct": 16.7,
        "leads_today": 0,
        "leads_7d": 1,
        "leads_30d": 3,
        "undelivered": 2,
    }
    assert sum(day["users"] for day in result["daily"]) == 2
    assert sum(day["leads"] for day in result["daily"]) == 2


def test_sources_count_deep_links_and_direct_within_the_source_window() -> None:
    source_start = NOW - timedelta(days=30)
    result = dashboard(
        user_rows=[
            user_row(source_start, source="ig"),
            user_row(source_start - timedelta(seconds=1), source="tg"),
            user_row(source="yt"),
            user_row(source=None),
            user_row(source="unknown"),
        ],
        lead_rows=[
            lead_row(source="ig"),
            lead_row(source="ig"),
            lead_row(source="tg"),
            lead_row(source=None),
            lead_row(source="unknown"),
            lead_row(source="friend"),
            lead_row(NOW + timedelta(seconds=1), source="yt"),
        ],
    )

    assert result["sources"] == [
        {"key": "ig", "label": "Instagram", "users": 1, "leads": 2},
        {"key": "tg", "label": "Telegram", "users": 0, "leads": 1},
        {"key": "yt", "label": "YouTube", "users": 1, "leads": 0},
        {"key": None, "label": "Тўғридан-тўғри", "users": 1, "leads": 1},
    ]


def test_recent_items_preserve_contract_and_are_json_safe() -> None:
    foreign_phone = "+12025550123"
    result = dashboard(
        recent_leads=[lead_row(), lead_row(phone=foreign_phone, source="friend")],
        recent_users=[user_row(has_lead=1), user_row(source="unknown")],
    )

    assert json.loads(json.dumps(result)) == result
    assert result["leads"] == [
        {
            "created_at": NOW.isoformat(),
            "name": "Example Lead",
            "phone": "998 90 123 45 67",
            "tg_username": "tester",
            "source_label": "Instagram",
            "region": "tashkent_city",
            "age": 34,
            "topics": ["family", "fear"],
        },
        {
            "created_at": NOW.isoformat(),
            "name": "Example Lead",
            "phone": foreign_phone,
            "tg_username": "tester",
            "source_label": "Танишлар орқали",
            "region": "tashkent_city",
            "age": 34,
            "topics": ["family", "fear"],
        },
    ]
    assert result["users"] == [
        {
            "first_seen_at": NOW.isoformat(),
            "last_seen_at": NOW.isoformat(),
            "tg_full_name": "Example User",
            "tg_username": None,
            "source_label": "Тўғридан-тўғри",
            "has_lead": True,
        },
        {
            "first_seen_at": NOW.isoformat(),
            "last_seen_at": NOW.isoformat(),
            "tg_full_name": "Example User",
            "tg_username": None,
            "source_label": "unknown",
            "has_lead": False,
        },
    ]
    assert result["users"][0]["has_lead"] is True
    assert result["users"][1]["has_lead"] is False


def test_payload_limits_recent_lists_to_200_items() -> None:
    result = dashboard(
        recent_leads=[lead_row()] * RECENT_LIMIT + [lead_row(name="Excluded Lead")],
        recent_users=[user_row()] * RECENT_LIMIT + [user_row(tg_full_name="Excluded User")],
    )

    assert RECENT_LIMIT == 200
    assert len(result["leads"]) == len(result["users"]) == RECENT_LIMIT
    assert result["leads"][-1]["name"] == "Example Lead"
    assert result["users"][-1]["tg_full_name"] == "Example User"


async def test_storage_returns_limited_recent_rows_in_order_with_lead_status(
    tmp_db_path: Path,
) -> None:
    storage = Storage(tmp_db_path)
    await storage.init()
    try:
        older = NOW - timedelta(days=2)
        middle = NOW - timedelta(days=1)
        await storage.upsert_user(1, "tester", "With Lead", "ig", NOW)
        await storage.upsert_user(2, None, "Without Lead", None, middle)
        await storage.upsert_user(3, None, "Older User", None, older)
        await storage.upsert_user(3, None, "Older User", None, NOW)
        first = await storage.save(lead_row())
        await storage.save(lead_row(older))
        latest = await storage.save(lead_row())

        leads = await storage.recent_leads(2)
        users = await storage.recent_users(2)

        assert [row["id"] for row in leads] == [latest, first]
        assert [row["topics"] for row in leads] == [["family", "fear"]] * 2
        assert [row["tg_user_id"] for row in users] == [1, 2]
        assert [row["has_lead"] for row in users] == [1, 0]
        assert await storage.recent_leads(0) == await storage.recent_users(0) == []
    finally:
        await storage.close()
