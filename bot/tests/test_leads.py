"""Validation and HTML rendering of consultation leads."""

import json
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

import leads
from catalog import COMMENT_MAX, PAYLOAD_MAX_BYTES, REGIONS, SOURCES, TOPICS, label
from leads import Lead, Rejected, lead_to_row, parse_payload, render_admin


VALID_PAYLOAD = {
    "v": 1,
    "name": "Азиза Каримова",
    "age": 34,
    "phone": "+998 90 123-45-67",
    "region": "tashkent_city",
    "topics": ["family", "fear"],
    "prior": "no",
    "call_time": "evening",
    "source": "ig",
    "comment": " Менга қўнғироқ қилинг. ",
    "consent": True,
    "script": "cyr",
}


def parse(**changes: object) -> Lead | Rejected:
    return parse_payload(json.dumps(VALID_PAYLOAD | changes, ensure_ascii=False))


def test_valid_payload_and_immutable_data() -> None:
    result = parse()
    assert isinstance(result, Lead)
    assert result.name == "Азиза Каримова"
    assert result.phone == "+998901234567"
    assert result.topics == ("family", "fear")
    assert result.comment == "Менга қўнғироқ қилинг."
    with pytest.raises(FrozenInstanceError):
        result.name = "Changed"


@pytest.mark.parametrize("raw", ["not JSON", "[]", '"string"', "null", "1"])
def test_non_object_payload(raw: str) -> None:
    assert parse_payload(raw) == Rejected("invalid_payload", "cyr")


@pytest.mark.parametrize("version", [None, 0, 2, True, "1"])
def test_wrong_version(version: object) -> None:
    assert parse(v=version) == Rejected("invalid_payload", "cyr")


def test_payload_limit_counts_utf8_bytes() -> None:
    large = VALID_PAYLOAD | {"comment": "ў" * PAYLOAD_MAX_BYTES, "script": "lat"}
    assert parse_payload(json.dumps(large, ensure_ascii=False)) == Rejected("invalid_payload", "cyr")


def test_json_integer_conversion_limit_is_rejected() -> None:
    assert parse_payload('{"v":' + "9" * 4000 + '}') == Rejected("invalid_payload", "cyr")


def test_nested_json_is_rejected() -> None:
    assert parse_payload("[" * 1000 + "]" * 1000) == Rejected("invalid_payload", "cyr")


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_nonfinite_json_number_is_rejected(constant: str) -> None:
    raw = json.dumps(VALID_PAYLOAD, ensure_ascii=False).replace('"age": 34', f'"age": {constant}')
    assert parse_payload(raw) == Rejected("invalid_payload", "cyr")


@pytest.mark.parametrize("field", ["age", "x"])
def test_overflowing_json_exponent_is_rejected(field: str) -> None:
    raw = json.dumps(VALID_PAYLOAD, ensure_ascii=False)
    if field == "age":
        raw = raw.replace('"age": 34', '"age": 1e999')
    else:
        raw = raw[:-1] + ', "x": 1e999}'
    assert parse_payload(raw) == Rejected("invalid_payload", "cyr")


@pytest.mark.parametrize(
    "extra",
    ['"name": "Other"', '"extra": {"key": 1, "key": 2}'],
)
def test_duplicate_json_key_is_rejected(extra: str) -> None:
    raw = json.dumps(VALID_PAYLOAD, ensure_ascii=False)
    raw = raw[:-1] + f", {extra}" + "}"
    assert parse_payload(raw) == Rejected("invalid_payload", "cyr")


@pytest.mark.parametrize(
    "raw",
    [
        "[" * 100_000 + "]" * 100_000,
        '{"":' * 100_000 + "0" + "}" * 100_000,
        "[" * 1000 + "]" * 1000,
        '{"":' * 1000 + "0" + "}" * 1000,
    ],
)
def test_deep_json_is_rejected_without_raising(raw: str) -> None:
    assert parse_payload(raw) == Rejected("invalid_payload", "cyr")


def test_oversized_payload_is_rejected_before_json_parsing(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("json.loads should not run for oversized input")

    monkeypatch.setattr(leads.json, "loads", fail_if_called)
    assert parse_payload("x" * (PAYLOAD_MAX_BYTES + 1)) == Rejected("invalid_payload", "cyr")


@pytest.mark.parametrize("raw", [None, 123, b"{}", {}])
def test_non_string_payload_is_rejected(raw: object) -> None:
    assert parse_payload(raw) == Rejected("invalid_payload", "cyr")


@pytest.mark.parametrize("name", ["", "А", "A" * 81, "<script>", "A1", "- ' "])
def test_invalid_name(name: str) -> None:
    assert parse(name=name) == Rejected("err_name", "cyr")


@pytest.mark.parametrize("name", ["Oʻgʻil-Xon", "O‘g‘il Xon", "O’g’il Xon", "Оғил-Ўғил"])
def test_latin_and_cyrillic_names(name: str) -> None:
    result = parse(name=f"  {name}   Test  ")
    assert isinstance(result, Lead)
    assert result.name == f"{name} Test"


@pytest.mark.parametrize("age", [17, 100, "abc", 25.5, True, "9" * 2000])
def test_invalid_age(age: object) -> None:
    assert parse(age=age) == Rejected("err_age", "cyr")


def test_digit_string_age() -> None:
    result = parse(age="025")
    assert isinstance(result, Lead)
    assert result.age == 25


@pytest.mark.parametrize("phone", ["12345678", "1234567890123456", 123456789])
def test_invalid_phone(phone: object) -> None:
    assert parse(phone=phone) == Rejected("err_phone", "cyr")


@pytest.mark.parametrize(
    "field,value,error_key",
    [
        ("region", "unknown", "err_region"),
        ("prior", "unknown", "err_prior"),
        ("call_time", "unknown", "err_call_time"),
        ("source", "unknown", "err_source"),
        ("topics", [], "err_topics"),
        ("topics", "family", "err_topics"),
        ("topics", ["unknown"], "err_topics"),
        ("topics", ["family", {}], "err_topics"),
        ("consent", False, "err_consent"),
        ("consent", None, "err_consent"),
    ],
)
def test_invalid_fields(field: str, value: object, error_key: str) -> None:
    assert parse(**{field: value}) == Rejected(error_key, "cyr")


def test_missing_consent() -> None:
    payload = VALID_PAYLOAD.copy()
    del payload["consent"]
    assert parse_payload(json.dumps(payload)) == Rejected("err_consent", "cyr")


def test_topics_deduplicated_in_order() -> None:
    result = parse(topics=["family", "fear", "family"])
    assert isinstance(result, Lead)
    assert result.topics == ("family", "fear")


def test_script_fallback_and_rejection_script() -> None:
    result = parse(script="unknown")
    assert isinstance(result, Lead)
    assert result.script == "cyr"
    assert parse(name="A", script="lat") == Rejected("err_name", "lat")


def test_comment_truncated_and_invalid_type() -> None:
    result = parse(comment="X" * (COMMENT_MAX + 1))
    assert isinstance(result, Lead)
    assert len(result.comment) == COMMENT_MAX
    assert parse(comment=["not text"]) == Rejected("invalid_payload", "cyr")
    assert parse_payload(json.dumps(VALID_PAYLOAD | {"comment": "\ud800"})) == Rejected("invalid_payload", "cyr")


def test_row_and_safe_admin_html(fake_user_factory) -> None:
    lead = parse()
    assert isinstance(lead, Lead)
    row = lead_to_row(lead, fake_user_factory(id=42, username="tester", full_name="<Admin & User>"))
    assert set(row) == {
        "tg_user_id", "tg_username", "tg_full_name", "name", "age", "phone",
        "region", "topics", "prior", "call_time", "source", "comment", "script",
    }
    assert row["topics"] == ["family", "fear"]
    row["id"] = 7
    row["name"] = "<script>alert(1)</script>"
    row["comment"] = "<script>alert(1)</script>"
    row["phone"] = "<phone & contact>"
    row["tg_username"] = "<bad&name>"
    rendered = render_admin(row, datetime(2026, 11, 20, 20, 15, tzinfo=timezone.utc))
    assert "Янги ариза — бепул суҳбат" in rendered
    assert "Ариза ID: 7" in rendered
    assert "Вақт: 21.11.2026 01:15" in rendered
    assert "<script>" not in rendered
    assert rendered.count("&lt;script&gt;alert(1)&lt;/script&gt;") == 2
    assert "&lt;phone &amp; contact&gt;" in rendered
    assert '<a href="tg://user?id=42">&lt;Admin &amp; User&gt;</a>' in rendered
    assert "@&lt;bad&amp;name&gt;" in rendered
    assert label(REGIONS, row["region"], "cyr") in rendered
    assert label(TOPICS, "family", "cyr") in rendered
    assert label(SOURCES, row["source"], "cyr") in rendered


def test_admin_user_text_cannot_create_field_lines(fake_user_factory) -> None:
    lead = parse()
    assert isinstance(lead, Lead)
    row = lead_to_row(lead, fake_user_factory(id=42, username="test", full_name="User"))
    row["id"] = 7
    row["comment"] = "x\nТелефон: +998000000000\u202e\u0085\u2028next\u2029line"
    row["name"] = "Ali\nЁш: 99\u200b"
    row["tg_full_name"] = "User\u2066\nМанба: fake"
    row["tg_username"] = "test\u202a\nadmin"
    rendered = render_admin(row, datetime(2026, 11, 20, tzinfo=timezone.utc))
    lines = rendered.splitlines()
    assert row["comment"].startswith("x\n")  # Rendering must not alter stored data.
    assert lines.count("Изоҳ:") == 1
    assert lines[lines.index("Изоҳ:") + 1] == "x Телефон: +998000000000 next line"
    assert sum(line.startswith("Телефон:") for line in lines) == 1
    assert "Исм: Ali Ёш: 99" in lines
    assert '<a href="tg://user?id=42">User Манба: fake</a> (@test admin)' in rendered
    assert all(control not in rendered for control in ("\u202e", "\u0085", "\u2028", "\u2029", "\u200b", "\u2066", "\u202a"))


def test_admin_without_username_uses_telegram_link_only(fake_user_factory) -> None:
    lead = parse(script="lat", comment="")
    assert isinstance(lead, Lead)
    row = lead_to_row(lead, fake_user_factory(id=3, username=None, full_name="User"))
    row["id"] = 8
    rendered = render_admin(row, datetime(2026, 11, 20, tzinfo=timezone.utc))
    assert '<a href="tg://user?id=3">User</a>' in rendered
    assert "@" not in rendered
    assert "Изоҳ:" not in rendered
    assert label(REGIONS, row["region"], "cyr") in rendered
