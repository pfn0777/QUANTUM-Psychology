"""JSON payload for the admin Mini App dashboard."""

from collections import Counter
from datetime import datetime, timedelta, timezone

from admin_panel import (
    ACTIVE_DAYS,
    NEW_USER_PERIODS,
    SOURCE_DAYS,
    TASHKENT_TZ,
    _count_between,
    _daily_counts,
    _parse_timestamp,
)
from catalog import DEEP_LINK_SOURCES, SOURCES, label
from storage import format_uz_phone


RECENT_LIMIT = 200
DAILY_DAYS = 30
_PERCENT_SCALE = 100
_CONVERSION_DECIMAL_PLACES = 1
_DIRECT_SOURCE_LABEL = "Тўғридан-тўғри"


def _source_label(source: str | None) -> str:
    return _DIRECT_SOURCE_LABEL if source is None else label(SOURCES, source)


def _source_counts(
    rows: list[dict], timestamp_key: str, start: datetime, end: datetime
) -> Counter[str | None]:
    return Counter(
        row["source"] for row in rows if start <= _parse_timestamp(row[timestamp_key]) <= end
    )


def _lead_item(row: dict) -> dict:
    phone = row["phone"]
    formatted_phone = format_uz_phone(phone)
    return {
        "created_at": row["created_at"],
        "name": row["name"],
        "phone": formatted_phone if formatted_phone is not None else phone,
        "tg_username": row["tg_username"],
        "source_label": _source_label(row["source"]),
        "region": row["region"],
        "age": row["age"],
        "topics": list(row["topics"]),
    }


def _user_item(row: dict) -> dict:
    return {
        "first_seen_at": row["first_seen_at"],
        "last_seen_at": row["last_seen_at"],
        "tg_full_name": row["tg_full_name"],
        "tg_username": row["tg_username"],
        "source_label": _source_label(row["source"]),
        "has_lead": bool(row["has_lead"]),
    }


def build_dashboard(
    *,
    total_users: int,
    user_rows: list[dict],
    lead_user_count: int,
    lead_rows: list[dict],
    undelivered: int,
    recent_leads: list[dict],
    recent_users: list[dict],
    now_utc: datetime,
) -> dict:
    """Build the dashboard from storage rows and the supplied reporting time."""
    now_utc = now_utc.astimezone(timezone.utc)
    now_local = now_utc.astimezone(TASHKENT_TZ)
    midnight = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_ago, thirty_days_ago = (
        now_utc - timedelta(days=days) for days in NEW_USER_PERIODS
    )
    active_since = now_utc - timedelta(days=ACTIVE_DAYS)
    first_seen = [_parse_timestamp(row["first_seen_at"]) for row in user_rows]
    last_seen = [_parse_timestamp(row["last_seen_at"]) for row in user_rows]
    lead_times = [_parse_timestamp(row["created_at"]) for row in lead_rows]
    conversion_pct = (
        round(lead_user_count / total_users * _PERCENT_SCALE, _CONVERSION_DECIMAL_PLACES)
        if total_users else None
    )

    today = now_local.date()
    users_by_date = _daily_counts(user_rows, "first_seen_at", now_utc)
    leads_by_date = _daily_counts(lead_rows, "created_at", now_utc)
    daily = []
    for offset in reversed(range(DAILY_DAYS)):
        day = today - timedelta(days=offset)
        daily.append({"date": day.isoformat(), "users": users_by_date[day], "leads": leads_by_date[day]})

    source_start = now_utc - timedelta(days=SOURCE_DAYS)
    users_by_source = _source_counts(user_rows, "first_seen_at", source_start, now_utc)
    leads_by_source = _source_counts(lead_rows, "created_at", source_start, now_utc)

    return {
        "generated_at": now_utc.isoformat(),
        "totals": {
            "users": total_users,
            "users_today": _count_between(first_seen, midnight, now_utc),
            "users_7d": _count_between(first_seen, seven_days_ago, now_utc),
            "users_30d": _count_between(first_seen, thirty_days_ago, now_utc),
            "active_7d": _count_between(last_seen, active_since, now_utc),
            "lead_users": lead_user_count,
            "conversion_pct": conversion_pct,
            "leads_today": _count_between(lead_times, midnight, now_utc),
            "leads_7d": _count_between(lead_times, seven_days_ago, now_utc),
            "leads_30d": _count_between(lead_times, thirty_days_ago, now_utc),
            "undelivered": undelivered,
        },
        "daily": daily,
        "sources": [
            {
                "key": source,
                "label": _source_label(source),
                "users": users_by_source[source],
                "leads": leads_by_source[source],
            }
            for source in (*DEEP_LINK_SOURCES, None)
        ],
        "leads": [_lead_item(row) for row in recent_leads[:RECENT_LIMIT]],
        "users": [_user_item(row) for row in recent_users[:RECENT_LIMIT]],
    }
