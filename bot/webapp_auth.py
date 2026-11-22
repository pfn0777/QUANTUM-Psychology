"""Verify Telegram Mini App init data using the bot token."""

import hmac
import json
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Literal
from urllib.parse import parse_qsl


INIT_DATA_MAX_AGE = timedelta(hours=24)
ALLOWED_CLOCK_SKEW = timedelta(minutes=5)
_UNIX_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_MICROSECOND = timedelta(microseconds=1)
_MICROSECONDS_PER_SECOND = timedelta(seconds=1) // _MICROSECOND


class InitDataError(Exception):
    def __init__(self, code: Literal["unauthorized", "expired"]) -> None:
        super().__init__(code)
        self.code = code


def validate_init_data(
    init_data: str,
    bot_token: str,
    now: datetime,
    max_age: timedelta = INIT_DATA_MAX_AGE,
) -> dict:
    """Return the authenticated Telegram user. The supplied time must be UTC-aware."""
    try:
        pairs = parse_qsl(init_data, keep_blank_values=True, strict_parsing=True)
    except ValueError:
        raise InitDataError("unauthorized") from None

    fields = dict(pairs)
    if len(fields) != len(pairs):
        raise InitDataError("unauthorized")

    received_hash = fields.pop("hash", "")
    if not received_hash or not received_hash.isascii():
        raise InitDataError("unauthorized")

    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(fields.items()))
    try:
        signed_data = data_check_string.encode()
    except UnicodeEncodeError:
        raise InitDataError("unauthorized") from None

    secret_key = hmac.new(b"WebAppData", bot_token.encode(), sha256).digest()
    expected = hmac.new(secret_key, signed_data, sha256).hexdigest()
    if not hmac.compare_digest(expected, received_hash):
        raise InitDataError("unauthorized")

    try:
        auth_date = int(fields["auth_date"])
    except (KeyError, ValueError):
        raise InitDataError("unauthorized") from None

    # Integer arithmetic preserves the time boundaries for Unix timestamps of any size.
    now_microseconds = (now - _UNIX_EPOCH) // _MICROSECOND
    age_microseconds = now_microseconds - auth_date * _MICROSECONDS_PER_SECOND
    if age_microseconds > max_age // _MICROSECOND:
        raise InitDataError("expired")
    if age_microseconds < -(ALLOWED_CLOCK_SKEW // _MICROSECOND):
        raise InitDataError("unauthorized")

    try:
        user = json.loads(fields["user"])
    except (KeyError, ValueError, RecursionError):
        raise InitDataError("unauthorized") from None
    if not isinstance(user, dict) or type(user.get("id")) is not int:
        raise InitDataError("unauthorized")

    return user
