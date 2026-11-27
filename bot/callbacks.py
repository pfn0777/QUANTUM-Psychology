"""Pure helpers for Telegram call-back requests."""

import html
import re
import unicodedata
from datetime import datetime, timezone

from aiogram.types import Contact, User

from leads import TASHKENT, _valid_phone


LINE_BREAKS = "\r\n\u2028\u2029"
CONTROL_CATEGORIES = frozenset({"Cc", "Cf"})
TASHKENT_TIME_FORMAT = "%d.%m.%Y %H:%M"


def _require_aware(now_utc: datetime) -> None:
    if now_utc.tzinfo is None or now_utc.utcoffset() is None:
        raise ValueError("now_utc must be timezone-aware")


def _safe_user_text(value: object) -> str:
    """Use the same control-character handling as leads.render_admin."""
    text = "".join(
        " " if char in LINE_BREAKS else char
        for char in str(value)
        if unicodedata.category(char) not in CONTROL_CATEGORIES or char in LINE_BREAKS
    )
    return html.escape(re.sub(r"\s+", " ", text).strip(), quote=True)


def own_contact_phone(contact: Contact | None, from_user_id: int | None) -> str | None:
    """Return a normalized number only for the sender's own contact."""
    if (
        contact is None
        or contact.user_id is None
        or from_user_id is None
        or contact.user_id != from_user_id
    ):
        return None

    raw_phone = contact.phone_number
    normalized = _valid_phone(raw_phone)
    if normalized is not None or "+" in raw_phone:
        return normalized

    digits = "".join(char for char in raw_phone if "0" <= char <= "9")
    return _valid_phone("+" + digits)


def callback_row(user: User, phone: str, now_utc: datetime) -> dict:
    """Build a storage row with an explicit UTC timestamp."""
    _require_aware(now_utc)
    return {
        "tg_user_id": user.id,
        "tg_username": user.username,
        "tg_full_name": user.full_name,
        "phone": phone,
        "created_at": now_utc.astimezone(timezone.utc).isoformat(),
    }


def render_callback_admin(row: dict, now_utc: datetime) -> str:
    """Render the stored request as safe Telegram HTML."""
    _require_aware(now_utc)
    tg_user_id = row["tg_user_id"]
    if isinstance(tg_user_id, bool) or not isinstance(tg_user_id, int):
        raise ValueError("tg_user_id must be an int")

    user_link = (
        f'<a href="tg://user?id={tg_user_id}">'
        f'{_safe_user_text(row["tg_full_name"])}</a>'
    )
    if row.get("tg_username"):
        user_link += f' (@{_safe_user_text(row["tg_username"])})'

    lines = [
        "<b>Қўнғироқ сўрови</b>",
        f'Сўров ID: {html.escape(str(row["id"]), quote=True)}',
        f'Вақт: {now_utc.astimezone(TASHKENT).strftime(TASHKENT_TIME_FORMAT)}',
        f'Телефон: {_safe_user_text(row["phone"])}',
        f'Telegram: {user_link}',
    ]
    return "\n".join(lines)
