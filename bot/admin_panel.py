"""Pure Cyrillic HTML messages and inline keyboards for the admin panel."""

import html
from collections import Counter
from datetime import date, datetime, timedelta, timezone

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

import catalog


CALLBACK_PREFIX = "adm:"
CB_OVERVIEW = f"{CALLBACK_PREFIX}overview"
CB_USERS = f"{CALLBACK_PREFIX}users"
CB_LEADS = f"{CALLBACK_PREFIX}leads"
CB_DAILY = f"{CALLBACK_PREFIX}daily"
CB_CSV_LEADS = f"{CALLBACK_PREFIX}csv_leads"
CB_CSV_USERS = f"{CALLBACK_PREFIX}csv_users"
PANEL_BUTTON_TEXT = "Визуал статистика"

TASHKENT_TZ = timezone(timedelta(hours=5))
ACTIVE_DAYS = 7
DAILY_DAYS = 14
NEW_USER_PERIODS = (7, 30)
SOURCE_DAYS = 30
LOOKBACK_DAYS = max(ACTIVE_DAYS, DAILY_DAYS, SOURCE_DAYS, *NEW_USER_PERIODS)
_PERCENT_SCALE = 100


def panel_keyboard(panel_url: str | None = None) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="Фойдаланувчилар", callback_data=CB_USERS),
            InlineKeyboardButton(text="Аризалар", callback_data=CB_LEADS),
        ],
        [InlineKeyboardButton(text=f"{DAILY_DAYS} кунлик динамика", callback_data=CB_DAILY)],
        [
            InlineKeyboardButton(text="Аризалар CSV", callback_data=CB_CSV_LEADS),
            InlineKeyboardButton(text="Фойдаланувчилар CSV", callback_data=CB_CSV_USERS),
        ],
        [InlineKeyboardButton(text="Янгилаш", callback_data=CB_OVERVIEW)],
    ]
    if panel_url:
        rows.insert(0, [InlineKeyboardButton(text=PANEL_BUTTON_TEXT, web_app=WebAppInfo(url=panel_url))])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="« Орқага", callback_data=CB_OVERVIEW)]]
    )


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _count_between(timestamps: list[datetime], start: datetime, end: datetime) -> int:
    return sum(start <= timestamp <= end for timestamp in timestamps)


def _period_summary(timestamps: list[datetime], midnight: datetime, now_utc: datetime) -> str:
    today = _count_between(timestamps, midnight, now_utc)
    parts = [f"бугун {today}"]
    for days in NEW_USER_PERIODS:
        count = _count_between(timestamps, now_utc - timedelta(days=days), now_utc)
        parts.append(f"{days} кун {count}")
    return " · ".join(parts)


def build_overview(
    total_users: int,
    user_rows: list[dict],
    lead_user_count: int,
    lead_rows: list[dict],
    undelivered: int,
    now_utc: datetime,
) -> str:
    """Build the admin overview using the supplied reporting time."""
    now_local = now_utc.astimezone(TASHKENT_TZ)
    midnight = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    first_seen = [_parse_timestamp(row["first_seen_at"]) for row in user_rows]
    last_seen = [_parse_timestamp(row["last_seen_at"]) for row in user_rows]
    lead_times = [_parse_timestamp(row["created_at"]) for row in lead_rows]
    active = _count_between(last_seen, now_utc - timedelta(days=ACTIVE_DAYS), now_utc)
    conversion = f"{round(lead_user_count / total_users * _PERCENT_SCALE)}%" if total_users else "—"

    return "\n".join(
        [
            "<b>Админ панел</b>",
            f"Фойдаланувчилар: {total_users}",
            f"Янги: {_period_summary(first_seen, midnight, now_utc)}",
            f"Фаол ({ACTIVE_DAYS} кун): {active}",
            f"Ариза қолдирганлар: {lead_user_count} ({conversion})",
            f"Аризалар: {_period_summary(lead_times, midnight, now_utc)}",
            f"Етказилмаган аризалар: {undelivered}",
            f"Янгиланди: {now_local:%d.%m.%Y %H:%M}",
        ]
    )


def build_users(total_users: int, user_rows: list[dict], now_utc: datetime) -> str:
    """Summarize acquisition sources for users first seen in the source window."""
    start = now_utc - timedelta(days=SOURCE_DAYS)
    counts: Counter[str | None] = Counter(
        row["source"] for row in user_rows
        if start <= _parse_timestamp(row["first_seen_at"]) <= now_utc
    )
    lines = ["<b>Фойдаланувчилар</b>", f"Жами: {html.escape(str(total_users))}"]
    if not counts:
        return "\n".join((*lines, "Янги фойдаланувчи йўқ"))

    ranks = {code: index for index, code in enumerate(catalog.SOURCES)}
    entries = sorted(
        counts.items(),
        key=lambda entry: (
            -entry[1],
            ranks.get(entry[0], len(ranks)),
            entry[0] is None,
            entry[0] or "",
        ),
    )
    for code, count in entries:
        display = "Тўғридан-тўғри" if code is None else catalog.label(catalog.SOURCES, code)
        lines.append(f"{html.escape(display)}: {html.escape(str(count))}")
    return "\n".join(lines)


def _daily_counts(rows: list[dict], timestamp_key: str, now_utc: datetime) -> Counter[date]:
    timestamps = (_parse_timestamp(row[timestamp_key]) for row in rows)
    return Counter(
        timestamp.astimezone(TASHKENT_TZ).date()
        for timestamp in timestamps
        if timestamp <= now_utc
    )


def build_daily(
    user_rows: list[dict],
    lead_rows: list[dict],
    now_utc: datetime,
    days: int = DAILY_DAYS,
) -> str:
    """Count new users and leads by Tashkent calendar date, newest first."""
    today = now_utc.astimezone(TASHKENT_TZ).date()
    users_by_date = _daily_counts(user_rows, "first_seen_at", now_utc)
    leads_by_date = _daily_counts(lead_rows, "created_at", now_utc)
    lines = [f"<b>{days} кунлик динамика</b>"]
    for offset in range(days):
        day = today - timedelta(days=offset)
        lines.append(
            f"{day:%d.%m} — фойдаланувчи: {users_by_date[day]} · ариза: {leads_by_date[day]}"
        )
    return "\n".join(lines)
