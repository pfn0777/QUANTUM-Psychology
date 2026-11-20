"""Pure Cyrillic HTML summary of consultation leads."""

import html
import json
from collections import Counter
from datetime import datetime, timedelta

from catalog import AGE_MAX, AGE_MIN, PRIOR, REGIONS, SOURCES, TOPICS, label


PERIOD_DAYS = (7, 30)
AGE_BANDS = (
    (24, "18–24"),
    (34, "25–34"),
    (44, "35–44"),
    (54, "45–54"),
    (AGE_MAX, "55+"),
)


def age_bucket(age: int) -> str:
    """Return the age range used in the admin summary."""
    if not AGE_MIN <= age <= AGE_MAX:
        raise ValueError(f"age must be between {AGE_MIN} and {AGE_MAX}")
    for upper_bound, bucket in AGE_BANDS:
        if age <= upper_bound:
            return bucket
    raise AssertionError("valid age has no bucket")


def _count_lines(
    title: str, counts: Counter[str], table: dict[str, dict[str, str]] | None = None
) -> list[str]:
    order = tuple(table) if table is not None else tuple(bucket for _, bucket in AGE_BANDS)
    ranks = {code: index for index, code in enumerate(order)}
    entries = sorted(
        counts.items(),
        key=lambda entry: (-entry[1], ranks.get(entry[0], len(ranks)), entry[0]),
    )
    lines = [f"<b>{title}</b>"]
    for code, count in entries:
        display = label(table, code) if table is not None else code
        lines.append(f"{html.escape(display)}: {count}")
    return lines


def _period_stats(rows: list[dict], now_utc: datetime, days: int) -> str:
    start = now_utc - timedelta(days=days)
    # Both endpoints are inclusive: a lead exactly `days` ago belongs here.
    period_rows = [
        row
        for row in rows
        if start <= datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) <= now_utc
    ]
    lines = [f"<b>Охирги {days} кун</b>"]
    if not period_rows:
        return "\n".join((*lines, "Ариза йўқ"))

    sources: Counter[str] = Counter()
    topics: Counter[str] = Counter()
    regions: Counter[str] = Counter()
    ages: Counter[str] = Counter()
    prior: Counter[str] = Counter()
    for row in period_rows:
        sources[row["source"]] += 1
        topic_codes = row["topics"]
        if isinstance(topic_codes, str):
            topic_codes = json.loads(topic_codes)
        topics.update(dict.fromkeys(topic_codes, 1))
        regions[row["region"]] += 1
        ages[age_bucket(row["age"])] += 1
        prior[row["prior"]] += 1

    lines.append(f"Жами: {len(period_rows)}")
    lines.extend(_count_lines("Манба", sources, SOURCES))
    lines.extend(_count_lines("Мавзу", topics, TOPICS))
    lines.extend(_count_lines("Ҳудуд", regions, REGIONS))
    lines.extend(_count_lines("Ёш", ages))
    lines.extend(_count_lines("Олдин қатнашган", prior, PRIOR))
    return "\n".join(lines)


def build_stats(rows: list[dict], now_utc: datetime) -> str:
    """Summarize the last 7 and 30 days without accessing storage or time."""
    return "\n\n".join(_period_stats(rows, now_utc, days) for days in PERIOD_DAYS)
