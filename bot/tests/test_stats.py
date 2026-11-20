"""Tests for the pure admin statistics builder."""

from datetime import datetime, timedelta, timezone

import pytest

from catalog import PRIOR, REGIONS, SOURCES, TOPICS, label
from stats import age_bucket, build_stats


NOW = datetime(2026, 11, 20, 12, tzinfo=timezone.utc)


def make_row(created_at: datetime, **overrides: object) -> dict:
    row = {
        "created_at": created_at.isoformat(),
        "source": "ig",
        "topics": ["family"],
        "region": "tashkent_city",
        "age": 24,
        "prior": "no",
    }
    row.update(overrides)
    return row


@pytest.mark.parametrize(
    ("age", "expected"),
    [
        (18, "18–24"),
        (24, "18–24"),
        (25, "25–34"),
        (34, "25–34"),
        (35, "35–44"),
        (44, "35–44"),
        (45, "45–54"),
        (54, "45–54"),
        (55, "55+"),
        (99, "55+"),
    ],
)
def test_age_bucket_boundaries(age: int, expected: str) -> None:
    assert age_bucket(age) == expected


def test_empty_periods() -> None:
    assert build_stats([], NOW) == (
        "<b>Охирги 7 кун</b>\nАриза йўқ\n\n"
        "<b>Охирги 30 кун</b>\nАриза йўқ"
    )


def test_window_start_is_inclusive_and_future_is_excluded() -> None:
    rows = [
        make_row(NOW - timedelta(days=7)),
        make_row(NOW - timedelta(days=7, microseconds=1)),
        make_row(NOW + timedelta(microseconds=1)),
    ]
    seven_days, thirty_days = build_stats(rows, NOW).split("\n\n")
    # The start boundary is inclusive; one microsecond before it is outside.
    assert "Жами: 1" in seven_days
    assert "Жами: 2" in thirty_days


def test_counts_labels_deduplicated_topics_and_descending_order() -> None:
    rows = [
        make_row(NOW, topics=["family", "fear", "family"]),
        make_row(
            NOW - timedelta(days=7),
            source="tg",
            topics='["family", "money"]',
            region="andijan",
            age=35,
            prior="finished",
        ),
        make_row(
            NOW - timedelta(days=8),
            source="tg",
            region="andijan",
            age=54,
            prior="stopped",
        ),
        make_row(
            NOW - timedelta(days=30),
            source="friend",
            topics=["fear"],
            region="bukhara",
            age=55,
        ),
        make_row(NOW - timedelta(days=30, seconds=1), source="yt"),
    ]
    seven_days, thirty_days = build_stats(rows, NOW).split("\n\n")

    assert "Жами: 2" in seven_days
    assert f"{label(TOPICS, 'family')}: 2" in seven_days
    assert f"{label(TOPICS, 'fear')}: 1" in seven_days
    assert "18–24: 1" in seven_days
    assert "35–44: 1" in seven_days
    assert f"{label(SOURCES, 'friend')}" not in seven_days
    assert "YouTube" not in seven_days

    assert "Жами: 4" in thirty_days
    assert thirty_days.index(f"{label(SOURCES, 'tg')}: 2") < thirty_days.index(
        f"{label(SOURCES, 'ig')}: 1"
    )
    assert thirty_days.index(f"{label(TOPICS, 'family')}: 3") < thirty_days.index(
        f"{label(TOPICS, 'fear')}: 2"
    )
    assert f"{label(REGIONS, 'andijan')}: 2" in thirty_days
    assert f"{label(PRIOR, 'no')}: 2" in thirty_days
    assert "55+: 1" in thirty_days
    assert "YouTube" not in thirty_days


def test_unknown_catalog_codes_fall_back_to_html_escaped_code() -> None:
    row = make_row(
        NOW,
        source="missing&source",
        topics=["<other>", "<other>"],
        region="unknown<region>",
        prior="unknown&prior",
    )
    result = build_stats([row], NOW)
    assert "missing&amp;source: 1" in result
    assert "&lt;other&gt;: 1" in result
    assert "unknown&lt;region&gt;: 1" in result
    assert "unknown&amp;prior: 1" in result
    assert "<other>" not in result
