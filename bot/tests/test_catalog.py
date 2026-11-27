"""Catalog and client text contracts shared with the Mini App."""

import re

import pytest

from catalog import (
    AGE_MAX,
    AGE_MIN,
    CALL_TIMES,
    COMMENT_MAX,
    COOLDOWN_SECONDS,
    DEEP_LINK_SOURCES,
    NAME_MAX,
    NAME_MIN,
    PAYLOAD_MAX_BYTES,
    PHONE_MAX_DIGITS,
    PHONE_MIN_DIGITS,
    PRIOR,
    REGIONS,
    RETRY_INTERVAL_SECONDS,
    SCRIPTS,
    SOURCES,
    TOPIC_MODULES,
    TOPICS,
    label,
)
from texts import TEXTS, t


EXPECTED_CODES = (
    (
        REGIONS,
        (
            "tashkent_city",
            "tashkent_region",
            "andijan",
            "bukhara",
            "fergana",
            "jizzakh",
            "kashkadarya",
            "navoi",
            "namangan",
            "samarkand",
            "surkhandarya",
            "syrdarya",
            "khorezm",
            "karakalpakstan",
            "abroad",
        ),
    ),
    (
        TOPICS,
        ("family", "parents", "fear", "money", "health", "selfworth", "support", "fatigue"),
    ),
    (PRIOR, ("no", "finished", "stopped")),
    (CALL_TIMES, ("morning", "day", "evening")),
    (SOURCES, ("ig", "tg", "yt", "friend", "other")),
)
EXPECTED_COUNTS = (15, 8, 3, 3, 5)
EXPECTED_TEXT_KEYS = {
    "cmd_admin",
    "cmd_start",
    "cmd_stats",
    "cmd_export",
    "welcome_caption",
    "start_greeting",
    "results_button",
    "coaching_button",
    "about_button",
    "contact_button",
    "callback_button",
    "results_intro",
    "results_footer",
    "results_more_button",
    "results_empty",
    "coaching_caption",
    "about_text",
    "contact_text",
    "callback_thanks",
    "callback_not_own",
    "callback_cooldown",
    "media_unavailable",
    "nav_results",
    "nav_coaching",
    "nav_about",
    "admin_phone_button",
    "write_admin_button",
    "more_info_button",
    "open_button",
    "thanks",
    "cooldown",
    "server_error",
    "admin_read_error",
    "fallback_hint",
    "invalid_payload",
    "err_name",
    "err_age",
    "err_phone",
    "err_region",
    "err_topics",
    "err_prior",
    "err_call_time",
    "err_source",
    "err_consent",
}
EXPECTED_TOPIC_MODULES = {
    "family": (3, 10),
    "parents": (3, 4),
    "fear": (1, 4),
    "money": (6, 9),
    "health": (8,),
    "selfworth": (2, 11),
    "support": (1, 11),
    "fatigue": (1, 8),
}
MODULE_MIN = 1
MODULE_MAX = 12
EMOJI_HIGH_START = 0x1F000
EMOJI_MISC_START = 0x2600
EMOJI_MISC_END = 0x27BF
CYRILLIC = re.compile(r"[\u0400-\u052f]")
LATIN = re.compile(r"[A-Za-z]")


@pytest.mark.parametrize("table,codes", EXPECTED_CODES)
def test_catalog_codes_and_labels(table: dict[str, dict[str, str]], codes: tuple[str, ...]) -> None:
    assert tuple(table) == codes
    assert len(table) == len(set(table))
    for entry in table.values():
        assert set(entry) == set(SCRIPTS)
        assert all(isinstance(value, str) and value.strip() for value in entry.values())
        assert CYRILLIC.search(entry["lat"]) is None
        assert "\u2018" not in entry["lat"]
        assert "\u2019" not in entry["lat"]
        if entry["cyr"] not in {"Instagram", "Telegram", "YouTube"}:
            assert LATIN.search(entry["cyr"]) is None


def test_catalog_counts_and_deep_links() -> None:
    assert tuple(len(table) for table, _ in EXPECTED_CODES) == EXPECTED_COUNTS
    assert SCRIPTS == ("cyr", "lat")
    assert DEEP_LINK_SOURCES == ("ig", "tg", "yt")
    assert set(DEEP_LINK_SOURCES) <= set(SOURCES)


def test_validation_and_retry_limits() -> None:
    assert (NAME_MIN, NAME_MAX) == (2, 80)
    assert (AGE_MIN, AGE_MAX) == (18, 99)
    assert (PHONE_MIN_DIGITS, PHONE_MAX_DIGITS) == (9, 15)
    assert COMMENT_MAX == 500
    assert PAYLOAD_MAX_BYTES == 4096
    assert COOLDOWN_SECONDS == 30
    assert RETRY_INTERVAL_SECONDS == 300


def test_topic_modules() -> None:
    assert set(TOPIC_MODULES) == set(TOPICS)
    assert TOPIC_MODULES == EXPECTED_TOPIC_MODULES
    assert all(
        isinstance(modules, tuple)
        and modules
        and all(MODULE_MIN <= module <= MODULE_MAX for module in modules)
        for modules in TOPIC_MODULES.values()
    )


def test_label_fallbacks() -> None:
    assert label(REGIONS, "fergana", "lat") == "Fargʻona"
    assert label(REGIONS, "fergana", "unknown") == "Фарғона"
    assert label(REGIONS, "missing") == "missing"
    assert label(REGIONS, "missing", "lat") == "missing"


def test_text_keys_and_messages() -> None:
    assert set(TEXTS) == set(SCRIPTS)
    assert set(TEXTS["cyr"]) == set(TEXTS["lat"]) == EXPECTED_TEXT_KEYS
    for messages in TEXTS.values():
        assert all(isinstance(message, str) and message.strip() for message in messages.values())
        assert "\n" in messages["start_greeting"]


def test_text_fallbacks_and_unknown_key() -> None:
    assert t("thanks", "lat") == TEXTS["lat"]["thanks"]
    assert t("thanks", "unknown") == TEXTS["cyr"]["thanks"]
    with pytest.raises(KeyError):
        t("missing")
    with pytest.raises(KeyError):
        t("missing", "unknown")


def test_text_formatting(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(TEXTS["cyr"], "formatted", "Салом, {name}!")
    assert t("formatted", name="Азиза") == "Салом, Азиза!"


def test_required_client_copy() -> None:
    expected_captions = {
        "cyr": "Ассалому алайкум! QUANTUM Psychology’га хуш келибсиз. Бизда шахсий ва руҳий ривожланиш учун 12 ойлик дастур бор. Дастур ҳақида танишишни истасангиз, пастдаги «Бепул суҳбатга ёзилиш» тугмани босинг. Дастлабки суҳбат бепул.",
        "lat": "Assalomu alaykum! QUANTUM Psychology’ga xush kelibsiz. Bizda shaxsiy va ruhiy rivojlanish uchun 12 oylik dastur bor. Dastur haqida tanishishni istasangiz, pastdagi «Bepul suhbatga yozilish» tugmani bosing. Dastlabki suhbat bepul.",
    }
    for script in SCRIPTS:
        caption = TEXTS[script]["welcome_caption"]
        thanks = TEXTS[script]["thanks"]
        assert caption == expected_captions[script]
        assert ("Дастлабки суҳбат бепул" if script == "cyr" else "Dastlabki suhbat bepul") in caption
        assert ("тугмани босинг" if script == "cyr" else "tugmani bosing") in caption
        assert ("Сиз танлаган вақтда" if script == "cyr" else "Siz tanlagan vaqtda") in thanks
        assert "18–99" in TEXTS[script]["err_age"]
        assert "+998 XX XXX XX XX" in TEXTS[script]["err_phone"]


@pytest.mark.parametrize("script", SCRIPTS)
@pytest.mark.parametrize("key", ("results_footer", "results_more_button"))
def test_results_page_text_formatting(script: str, key: str) -> None:
    rendered = t(key, script, page=1, total=3)
    assert "1" in rendered
    assert "3" in rendered
    assert "{" not in rendered and "}" not in rendered
