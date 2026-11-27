"""Phone ownership, callback rows, and safe admin notifications."""

from datetime import datetime, timedelta, timezone

import pytest
from aiogram.types import Contact

from callbacks import callback_row, own_contact_phone, render_callback_admin


USER_ID = 42
NOW_UTC = datetime(2026, 11, 27, 19, 30, tzinfo=timezone.utc)


def make_contact(phone: str, user_id: int | None = USER_ID) -> Contact:
    return Contact(phone_number=phone, first_name="Test", user_id=user_id)


def make_row() -> dict:
    return {
        "id": 7,
        "tg_user_id": USER_ID,
        "tg_username": "tester",
        "tg_full_name": "Test User",
        "phone": "+998916628111",
    }


def test_contact_must_belong_to_sender() -> None:
    assert own_contact_phone(None, USER_ID) is None
    assert own_contact_phone(make_contact("+998916628111", user_id=99), USER_ID) is None
    assert own_contact_phone(make_contact("+998916628111", user_id=None), USER_ID) is None
    assert own_contact_phone(make_contact("+998916628111"), None) is None


@pytest.mark.parametrize("phone", ["123", "abc", ""])
def test_invalid_contact_phone_is_rejected(phone: str) -> None:
    assert own_contact_phone(make_contact(phone), USER_ID) is None


@pytest.mark.parametrize(
    "phone, expected",
    [
        ("998916628111", "+998916628111"),
        ("+998916628111", "+998916628111"),
        ("916628111", "+998916628111"),
        ("998 91 662 81 11", "+998916628111"),
        ("79123456789", "+79123456789"),
    ],
)
def test_own_phone_is_normalized(phone: str, expected: str) -> None:
    assert own_contact_phone(make_contact(phone), USER_ID) == expected


def test_callback_row_uses_utc_iso_and_user_identity(fake_user_factory) -> None:
    user = fake_user_factory(id=USER_ID, username="tester", full_name="Test User")
    local_time = datetime(2026, 11, 28, 0, 30, tzinfo=timezone(timedelta(hours=5)))
    assert callback_row(user, "+998916628111", local_time) == {
        "tg_user_id": USER_ID,
        "tg_username": "tester",
        "tg_full_name": "Test User",
        "phone": "+998916628111",
        "created_at": "2026-11-27T19:30:00+00:00",
    }


def test_admin_message_matches_spec_and_tashkent_date() -> None:
    assert render_callback_admin(make_row(), NOW_UTC) == (
        "<b>Қўнғироқ сўрови</b>\n"
        "Сўров ID: 7\n"
        "Вақт: 28.11.2026 00:30\n"
        "Телефон: +998916628111\n"
        'Telegram: <a href="tg://user?id=42">Test User</a> (@tester)'
    )


def test_admin_escapes_html_and_removes_control_characters() -> None:
    row = make_row() | {
        "tg_full_name": '<script> & "Name"\nNext\u2066\x00',
        "tg_username": '<script> & "admin"\nnext\u202e',
        "phone": "+998<bad>&\n123",
    }
    rendered = render_callback_admin(row, NOW_UTC)
    assert '<a href="tg://user?id=42">&lt;script&gt; &amp; &quot;Name&quot; Next</a>' in rendered
    assert '(@&lt;script&gt; &amp; &quot;admin&quot; next)' in rendered
    assert "Телефон: +998&lt;bad&gt;&amp; 123" in rendered
    assert "<script>" not in rendered
    assert all(control not in rendered for control in ("\u2066", "\x00", "\u202e"))
    assert len(rendered.splitlines()) == 5


@pytest.mark.parametrize("username", [None, ""])
def test_admin_omits_missing_username(username: str | None) -> None:
    row = make_row() | {"tg_username": username}
    rendered = render_callback_admin(row, NOW_UTC)
    assert 'Telegram: <a href="tg://user?id=42">Test User</a>' in rendered
    assert " (@" not in rendered


@pytest.mark.parametrize("invalid_id", ["42", None, 42.0, True])
def test_admin_rejects_non_integer_telegram_id(invalid_id: object) -> None:
    with pytest.raises(ValueError, match="tg_user_id"):
        render_callback_admin(make_row() | {"tg_user_id": invalid_id}, NOW_UTC)


def test_both_time_helpers_reject_naive_datetime(fake_user_factory) -> None:
    naive_time = datetime(2026, 11, 27, 19, 30)
    with pytest.raises(ValueError, match="timezone-aware"):
        callback_row(fake_user_factory(), "+998916628111", naive_time)
    with pytest.raises(ValueError, match="timezone-aware"):
        render_callback_admin(make_row(), naive_time)
