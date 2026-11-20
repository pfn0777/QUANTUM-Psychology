"""Validate Mini App leads and render safe admin notifications."""

import html
import json
import math
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from catalog import (
    AGE_MAX,
    AGE_MIN,
    CALL_TIMES,
    COMMENT_MAX,
    NAME_MAX,
    NAME_MIN,
    PAYLOAD_MAX_BYTES,
    PHONE_MAX_DIGITS,
    PHONE_MIN_DIGITS,
    PRIOR,
    REGIONS,
    SCRIPTS,
    SOURCES,
    TOPICS,
    label,
)


PAYLOAD_VERSION = 1
UZBEKISTAN_PHONE_PREFIX = "998"
TASHKENT_UTC_OFFSET_HOURS = 5
TASHKENT = timezone(timedelta(hours=TASHKENT_UTC_OFFSET_HOURS))
NAME_PUNCTUATION = frozenset("ʻ‘’'ʼ- ")


@dataclass(frozen=True)
class Lead:
    name: str
    age: int
    phone: str
    region: str
    topics: tuple[str, ...]
    prior: str
    call_time: str
    source: str
    comment: str
    script: str


@dataclass(frozen=True)
class Rejected:
    error_key: str
    script: str


def _valid_name(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    name = " ".join(value.split())
    if not NAME_MIN <= len(name) <= NAME_MAX:
        return None
    letters = 0
    for char in name:
        if char.isalpha() and ("A" <= char <= "Z" or "a" <= char <= "z" or "\u0400" <= char <= "\u052f"):
            letters += 1
        elif char not in NAME_PUNCTUATION:
            return None
    return name if letters >= NAME_MIN else None


def _valid_age(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        age = value
    elif isinstance(value, str) and re.fullmatch(r"[0-9]+", value):
        digits = value.lstrip("0") or "0"
        if len(digits) > len(str(AGE_MAX)):
            return None
        age = int(digits)
    else:
        return None
    return age if AGE_MIN <= age <= AGE_MAX else None


def _valid_phone(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    phone = value.strip()
    digits = "".join(char for char in phone if "0" <= char <= "9")
    if not PHONE_MIN_DIGITS <= len(digits) <= PHONE_MAX_DIGITS:
        return None
    if len(digits) == len(UZBEKISTAN_PHONE_PREFIX) + PHONE_MIN_DIGITS and digits.startswith(UZBEKISTAN_PHONE_PREFIX):
        return "+" + digits
    return ("+" if phone.startswith("+") else "") + digits


def _reject_json_constant(value: str) -> None:
    raise ValueError("Non-finite JSON number")


def _finite_json_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Non-finite JSON number")
    return number


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def parse_payload(raw: object) -> Lead | Rejected:
    """Reject malformed or out-of-contract input before it reaches storage."""
    if not isinstance(raw, str):
        return Rejected("invalid_payload", "cyr")
    try:
        if len(raw.encode("utf-8")) > PAYLOAD_MAX_BYTES:
            return Rejected("invalid_payload", "cyr")
        payload = json.loads(
            raw,
            parse_constant=_reject_json_constant,
            parse_float=_finite_json_float,
            object_pairs_hook=_unique_json_object,
        )
    except (UnicodeEncodeError, ValueError, RecursionError):
        return Rejected("invalid_payload", "cyr")
    if not isinstance(payload, dict):
        return Rejected("invalid_payload", "cyr")

    script = payload.get("script")
    script = script if isinstance(script, str) and script in SCRIPTS else "cyr"
    reject = lambda key: Rejected(key, script)
    if type(payload.get("v")) is not int or payload["v"] != PAYLOAD_VERSION:
        return reject("invalid_payload")

    name = _valid_name(payload.get("name"))
    if name is None:
        return reject("err_name")
    age = _valid_age(payload.get("age"))
    if age is None:
        return reject("err_age")
    phone = _valid_phone(payload.get("phone"))
    if phone is None:
        return reject("err_phone")

    region = payload.get("region")
    if not isinstance(region, str) or region not in REGIONS:
        return reject("err_region")
    raw_topics = payload.get("topics")
    if not isinstance(raw_topics, list) or not raw_topics:
        return reject("err_topics")
    if any(not isinstance(code, str) or code not in TOPICS for code in raw_topics):
        return reject("err_topics")
    topics = tuple(dict.fromkeys(raw_topics))
    if len(topics) > len(TOPICS):
        return reject("err_topics")

    prior = payload.get("prior")
    if not isinstance(prior, str) or prior not in PRIOR:
        return reject("err_prior")
    call_time = payload.get("call_time")
    if not isinstance(call_time, str) or call_time not in CALL_TIMES:
        return reject("err_call_time")
    source = payload.get("source")
    if not isinstance(source, str) or source not in SOURCES:
        return reject("err_source")

    comment = payload.get("comment", "")
    if not isinstance(comment, str):
        return reject("invalid_payload")
    try:
        comment.encode("utf-8")
    except UnicodeEncodeError:
        return reject("invalid_payload")
    if payload.get("consent") is not True:
        return reject("err_consent")
    return Lead(name, age, phone, region, topics, prior, call_time, source,
                comment.strip()[:COMMENT_MAX], script)


def lead_to_row(lead: Lead, user: object) -> dict:
    """Attach Telegram identity to validated form fields for Storage.save."""
    return {
        "tg_user_id": user.id,
        "tg_username": user.username,
        "tg_full_name": user.full_name,
        "name": lead.name,
        "age": lead.age,
        "phone": lead.phone,
        "region": lead.region,
        "topics": list(lead.topics),
        "prior": lead.prior,
        "call_time": lead.call_time,
        "source": lead.source,
        "comment": lead.comment,
        "script": lead.script,
    }


def render_admin(row: dict, now_utc: datetime) -> str:
    """Render one stored lead with trusted markup and escaped values."""
    if now_utc.tzinfo is None or now_utc.utcoffset() is None:
        raise ValueError("now_utc must be timezone-aware")
    safe = lambda value: html.escape(str(value), quote=True)
    def safe_user_text(value: object) -> str:
        text = "".join(
            " " if char in "\r\n\u2028\u2029" else char
            for char in str(value)
            if unicodedata.category(char) not in {"Cc", "Cf"} or char in "\r\n\u2028\u2029"
        )
        return html.escape(re.sub(r"\s+", " ", text).strip(), quote=True)

    topic_labels = ", ".join(label(TOPICS, code, "cyr") for code in row["topics"])
    user_link = f'<a href="tg://user?id={safe(row["tg_user_id"])}">{safe_user_text(row["tg_full_name"])}</a>'
    if row.get("tg_username"):
        user_link += f' (@{safe_user_text(row["tg_username"])})'
    lines = [
        "<b>Янги ариза — бепул суҳбат</b>",
        f'Ариза ID: {safe(row["id"])}',
        f'Вақт: {safe(now_utc.astimezone(TASHKENT).strftime("%d.%m.%Y %H:%M"))}',
        f'Исм: {safe_user_text(row["name"])}',
        f'Ёш: {safe(row["age"])}',
        f'Телефон: {safe_user_text(row["phone"])}',
        f'Ҳудуд: {safe(label(REGIONS, row["region"], "cyr"))}',
        f'Мавзулар: {safe(topic_labels)}',
        f'Олдин қатнашган: {safe(label(PRIOR, row["prior"], "cyr"))}',
        f'Қўнғироқ вақти: {safe(label(CALL_TIMES, row["call_time"], "cyr"))}',
        f'Манба: {safe(label(SOURCES, row["source"], "cyr"))}',
    ]
    if row.get("comment"):
        lines.extend(('Изоҳ:', safe_user_text(row["comment"])))
    lines.append(f'Telegram: {user_link}')
    return "\n".join(lines)
