"""Tests for Telegram Mini App init data validation."""

import hmac
import json
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from urllib.parse import urlencode

import pytest

from webapp_auth import InitDataError, validate_init_data


NOW = datetime(2026, 11, 22, 10, tzinfo=timezone.utc)
TEST_TOKEN = "fixture-token"
USER = {"id": 123456789, "first_name": "Élodie + Ali"}
SIGNATURE = "fixture-signature"
ONE_SECOND = timedelta(seconds=1)
MAX_AGE = timedelta(hours=24)
CLOCK_SKEW = timedelta(minutes=5)


def make_fields(auth_date: datetime = NOW) -> dict[str, str]:
    return {
        "user": json.dumps(USER, ensure_ascii=False),
        "signature": SIGNATURE,
        "query_id": "",
        "auth_date": str(int(auth_date.timestamp())),
    }


def sign_fields(fields: list[tuple[str, str]]) -> str:
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(fields))
    secret = hmac.new(b"WebAppData", TEST_TOKEN.encode(), sha256).digest()
    digest = hmac.new(secret, data_check_string.encode(), sha256).hexdigest()
    return urlencode([*fields, ("hash", digest)])


def signed_init_data(auth_date: datetime = NOW) -> str:
    return sign_fields(list(make_fields(auth_date).items()))


def assert_rejected(init_data: str, code: str) -> None:
    with pytest.raises(InitDataError) as error:
        validate_init_data(init_data, TEST_TOKEN, NOW)
    assert error.value.code == code


def test_valid_init_data_returns_user() -> None:
    assert validate_init_data(signed_init_data(), TEST_TOKEN, NOW) == USER


def test_tampered_signature_is_rejected() -> None:
    assert_rejected(signed_init_data().replace(SIGNATURE, "modified"), "unauthorized")


def test_wrong_token_is_rejected() -> None:
    with pytest.raises(InitDataError) as error:
        validate_init_data(signed_init_data(), "wrong-fixture-token", NOW)
    assert error.value.code == "unauthorized"


@pytest.mark.parametrize("suffix", ["", "&hash=", "&hash=%C3%A9"])
def test_missing_or_invalid_hash_is_rejected(suffix: str) -> None:
    assert_rejected(urlencode(make_fields()) + suffix, "unauthorized")


@pytest.mark.parametrize("key", ["query_id", "hash"])
def test_duplicate_keys_are_rejected(key: str) -> None:
    assert_rejected(f"{signed_init_data()}&{key}=", "unauthorized")


def test_malformed_query_is_rejected() -> None:
    assert_rejected(signed_init_data() + "&malformed", "unauthorized")


def test_empty_init_data_is_rejected() -> None:
    assert_rejected("", "unauthorized")


def test_expired_auth_date_is_rejected() -> None:
    assert_rejected(signed_init_data(NOW - MAX_AGE - ONE_SECOND), "expired")


def test_future_auth_date_beyond_clock_skew_is_rejected() -> None:
    assert_rejected(signed_init_data(NOW + CLOCK_SKEW + ONE_SECOND), "unauthorized")


@pytest.mark.parametrize("offset", [-MAX_AGE, CLOCK_SKEW])
def test_auth_date_at_time_limit_is_accepted(offset: timedelta) -> None:
    assert validate_init_data(signed_init_data(NOW + offset), TEST_TOKEN, NOW) == USER


def test_custom_max_age_is_used() -> None:
    with pytest.raises(InitDataError) as error:
        validate_init_data(signed_init_data(NOW - MAX_AGE), TEST_TOKEN, NOW, ONE_SECOND)
    assert error.value.code == "expired"


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("auth_date", None),
        ("auth_date", "not-an-integer"),
        ("user", None),
        ("user", "{invalid-json}"),
        ("user", "[]"),
        ("user", '{}'),
        ("user", '{"id":true}'),
        ("user", '{"id":"123456789"}'),
        ("user", '{"id":123456789.0}'),
    ],
)
def test_missing_or_invalid_required_fields_are_rejected(key: str, value: str | None) -> None:
    fields = make_fields()
    if value is None:
        del fields[key]
    else:
        fields[key] = value
    assert_rejected(sign_fields(list(fields.items())), "unauthorized")
