"""Tests for the pure admin panel message and keyboard builders."""

from datetime import datetime, timedelta, timezone

from aiogram.types import InlineKeyboardMarkup

from admin_panel import (
    ACTIVE_DAYS,
    CALLBACK_PREFIX,
    CB_CSV_LEADS,
    CB_CSV_USERS,
    CB_DAILY,
    CB_LEADS,
    CB_OVERVIEW,
    CB_USERS,
    DAILY_DAYS,
    LOOKBACK_DAYS,
    NEW_USER_PERIODS,
    SOURCE_DAYS,
    TASHKENT_TZ,
    back_keyboard,
    build_daily,
    build_overview,
    build_users,
    panel_keyboard,
)


NOW = datetime(2026, 11, 22, 10, tzinfo=timezone.utc)
TASHKENT_MIDNIGHT_UTC = datetime(2026, 11, 21, 19, tzinfo=timezone.utc)


def make_user(
    first_seen_at: datetime, *, last_seen_at: datetime | None = None, source: str | None = None
) -> dict:
    return {
        "first_seen_at": first_seen_at.isoformat(),
        "last_seen_at": (last_seen_at or first_seen_at).isoformat(),
        "source": source,
    }


def make_lead(created_at: datetime) -> dict:
    return {"created_at": created_at.isoformat().replace("+00:00", "Z")}


def test_panel_constants() -> None:
    assert CALLBACK_PREFIX == "adm:"
    assert (CB_OVERVIEW, CB_USERS, CB_LEADS, CB_DAILY, CB_CSV_LEADS, CB_CSV_USERS) == (
        "adm:overview", "adm:users", "adm:leads", "adm:daily", "adm:csv_leads", "adm:csv_users"
    )
    assert ACTIVE_DAYS == 7
    assert DAILY_DAYS == 14
    assert NEW_USER_PERIODS == (7, 30)
    assert SOURCE_DAYS == 30
    assert LOOKBACK_DAYS == 30
    assert TASHKENT_TZ == timezone(timedelta(hours=5))


def test_overview_uses_tashkent_midnight_and_rounds_conversion() -> None:
    before_midnight = TASHKENT_MIDNIGHT_UTC - timedelta(seconds=1)
    users = [
        make_user(before_midnight),
        make_user(TASHKENT_MIDNIGHT_UTC),
        make_user(NOW, last_seen_at=NOW),
    ]
    leads = [make_lead(before_midnight), make_lead(TASHKENT_MIDNIGHT_UTC)]

    assert build_overview(3, users, 1, leads, 1, NOW).splitlines() == [
        "<b>Админ панел</b>",
        "Фойдаланувчилар: 3",
        "Янги: бугун 2 · 7 кун 3 · 30 кун 3",
        "Фаол (7 кун): 3",
        "Ариза қолдирганлар: 1 (33%)",
        "Аризалар: бугун 1 · 7 кун 2 · 30 кун 2",
        "Етказилмаган аризалар: 1",
        "Янгиланди: 22.11.2026 15:00",
    ]


def test_overview_rolling_windows_include_both_bounds_and_exclude_future() -> None:
    seven_days_ago = NOW - timedelta(days=7)
    thirty_days_ago = NOW - timedelta(days=30)
    tick = timedelta(microseconds=1)
    timestamps = [
        NOW,
        seven_days_ago,
        seven_days_ago - tick,
        thirty_days_ago,
        thirty_days_ago - tick,
        NOW + tick,
    ]
    users = [make_user(timestamp) for timestamp in timestamps]
    leads = [make_lead(timestamp) for timestamp in timestamps]

    overview = build_overview(len(users), users, 0, leads, 0, NOW)

    assert "Янги: бугун 1 · 7 кун 2 · 30 кун 4" in overview
    assert "Аризалар: бугун 1 · 7 кун 2 · 30 кун 4" in overview


def test_overview_counts_active_users_by_last_seen() -> None:
    first_seen_at = NOW - timedelta(days=40)
    seven_days_ago = NOW - timedelta(days=7)
    users = [
        make_user(first_seen_at, last_seen_at=seven_days_ago),
        make_user(first_seen_at, last_seen_at=NOW),
        make_user(first_seen_at, last_seen_at=seven_days_ago - timedelta(seconds=1)),
        make_user(first_seen_at, last_seen_at=NOW + timedelta(seconds=1)),
    ]

    overview = build_overview(len(users), users, 0, [], 0, NOW)

    assert "Янги: бугун 0 · 7 кун 0 · 30 кун 0" in overview
    assert "Фаол (7 кун): 2" in overview


def test_overview_shows_dash_with_zero_users() -> None:
    assert "Ариза қолдирганлар: 0 (—)" in build_overview(0, [], 0, [], 0, NOW)


def test_users_source_counts_are_sorted_and_escaped() -> None:
    thirty_days_ago = NOW - timedelta(days=30)
    users = [
        make_user(NOW),
        make_user(NOW, source="<x>"),
        make_user(NOW, source="yt"),
        make_user(thirty_days_ago, source="ig"),
        make_user(NOW, source="tg"),
        make_user(NOW, source="tg"),
        make_user(thirty_days_ago - timedelta(seconds=1), source="ig", last_seen_at=NOW),
        make_user(NOW + timedelta(seconds=1), source="yt"),
    ]

    assert build_users(12, users, NOW).splitlines() == [
        "<b>Фойдаланувчилар</b>",
        "Жами: 12",
        "Telegram: 2",
        "Instagram: 1",
        "YouTube: 1",
        "&lt;x&gt;: 1",
        "Тўғридан-тўғри: 1",
    ]


def test_users_reports_no_new_users_outside_source_window() -> None:
    users = [make_user(NOW - timedelta(days=31), last_seen_at=NOW, source="ig")]

    assert build_users(1, users, NOW).splitlines() == [
        "<b>Фойдаланувчилар</b>",
        "Жами: 1",
        "Янги фойдаланувчи йўқ",
    ]


def test_daily_counts_tashkent_dates_and_includes_empty_days() -> None:
    before_midnight = TASHKENT_MIDNIGHT_UTC - timedelta(seconds=1)
    future = NOW + timedelta(seconds=1)
    users = [make_user(before_midnight), make_user(TASHKENT_MIDNIGHT_UTC), make_user(future)]
    leads = [make_lead(TASHKENT_MIDNIGHT_UTC), make_lead(NOW), make_lead(future)]

    title, *days = build_daily(users, leads, NOW).splitlines()

    assert title == "<b>14 кунлик динамика</b>"
    assert len(days) == 14
    assert days[:3] == [
        "22.11 — фойдаланувчи: 1 · ариза: 2",
        "21.11 — фойдаланувчи: 1 · ариза: 0",
        "20.11 — фойдаланувчи: 0 · ариза: 0",
    ]
    assert days[-1] == "09.11 — фойдаланувчи: 0 · ариза: 0"


def test_daily_uses_requested_days_and_current_tashkent_date() -> None:
    now = TASHKENT_MIDNIGHT_UTC - timedelta(seconds=1)

    assert build_daily([], [], now, days=2).splitlines() == [
        "<b>2 кунлик динамика</b>",
        "21.11 — фойдаланувчи: 0 · ариза: 0",
        "20.11 — фойдаланувчи: 0 · ариза: 0",
    ]


def test_panel_keyboard_layout_and_callbacks() -> None:
    keyboard = panel_keyboard()

    assert isinstance(keyboard, InlineKeyboardMarkup)
    buttons = [
        [(button.text, button.callback_data) for button in row]
        for row in keyboard.inline_keyboard
    ]
    assert buttons == [
        [("Фойдаланувчилар", CB_USERS), ("Аризалар", CB_LEADS)],
        [("14 кунлик динамика", CB_DAILY)],
        [("Аризалар CSV", CB_CSV_LEADS), ("Фойдаланувчилар CSV", CB_CSV_USERS)],
        [("Янгилаш", CB_OVERVIEW)],
    ]
    for row in keyboard.inline_keyboard:
        for button in row:
            assert button.callback_data.startswith(CALLBACK_PREFIX)
            assert len(button.callback_data.encode("utf-8")) <= 64


def test_back_keyboard_returns_to_overview() -> None:
    keyboard = back_keyboard()

    assert isinstance(keyboard, InlineKeyboardMarkup)
    buttons = [
        [(button.text, button.callback_data) for button in row]
        for row in keyboard.inline_keyboard
    ]
    assert buttons == [[("« Орқага", CB_OVERVIEW)]]
