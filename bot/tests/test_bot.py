"""Tests for Mini App bot handlers without Telegram network access."""

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest
from aiogram.enums import ParseMode
from aiogram.types import BufferedInputFile, FSInputFile, InlineKeyboardMarkup, ReplyKeyboardMarkup

import bot as bot_module
from bot import BotHandlers, ConfigError, Settings, build_dispatcher, load_settings
from storage import Storage
from texts import t


ADMIN_CHAT_ID = -100123
WEBAPP_URL = "https://example.org/app"
EVENT_TIMEOUT_SECONDS = 1
PAYLOAD = {
    "v": 1,
    "name": "Aziza Karimova",
    "age": 34,
    "phone": "+998901234567",
    "region": "tashkent_city",
    "topics": ["family"],
    "prior": "no",
    "call_time": "evening",
    "source": "ig",
    "comment": "",
    "consent": True,
    "script": "lat",
}


@dataclass
class FakeChat:
    id: int


class FakeMessage:
    def __init__(self, user, *, text=None, data=None, chat_id=1, photo_error=None):
        self.from_user = user
        self.text = text
        self.chat = FakeChat(chat_id)
        self.web_app_data = SimpleNamespace(data=data) if data is not None else None
        self.answers = []
        self.photos = []
        self.calls = []
        self.photo_error = photo_error
        self.documents = []

    async def answer(self, text, **kwargs):
        self.calls.append("answer")
        self.answers.append((text, kwargs))

    async def answer_photo(self, photo, **kwargs):
        if self.photo_error is not None:
            raise self.photo_error
        self.calls.append("photo")
        self.photos.append((photo, kwargs))

    async def answer_document(self, document, **kwargs):
        self.documents.append((document, kwargs))


class FakeBot:
    def __init__(self, fail=False):
        self.fail = fail
        self.sent = []

    async def send_message(self, chat_id, text, **kwargs):
        if self.fail:
            raise RuntimeError("Telegram unavailable")
        self.sent.append((chat_id, text, kwargs))


@pytest.fixture
async def configured(tmp_db_path):
    storage = Storage(tmp_db_path)
    await storage.init()
    handlers = BotHandlers(Settings("unused", ADMIN_CHAT_ID, WEBAPP_URL, tmp_db_path), storage)
    try:
        yield handlers, storage
    finally:
        await storage.close()


def payload(**changes):
    return json.dumps(PAYLOAD | changes, ensure_ascii=False)


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        ({"ADMIN_CHAT_ID": "1", "WEBAPP_URL": WEBAPP_URL}, "BOT_TOKEN"),
        ({"BOT_TOKEN": "token", "ADMIN_CHAT_ID": "x", "WEBAPP_URL": WEBAPP_URL}, "ADMIN_CHAT_ID"),
        ({"BOT_TOKEN": "token", "ADMIN_CHAT_ID": "-1", "WEBAPP_URL": "http://example.org"}, "WEBAPP_URL"),
        ({"BOT_TOKEN": "token", "ADMIN_CHAT_ID": "-1", "WEBAPP_URL": "https://"}, "WEBAPP_URL"),
    ],
)
def test_invalid_settings(tmp_path: Path, values: dict, expected: str):
    with pytest.raises(ConfigError, match=expected):
        load_settings(values, tmp_path / "missing.env")


def test_dotenv_and_environment_override(tmp_path: Path):
    path = tmp_path / "test.env"
    path.write_text("BOT_TOKEN=from_file\nADMIN_CHAT_ID=-42\nWEBAPP_URL=https://example.org\n", encoding="utf-8")
    settings = load_settings({"BOT_TOKEN": "from_env"}, path)
    assert settings.token == "from_env"
    assert settings.admin_chat_id == -42
    assert settings.db_path.name == "leads.db"
    assert settings.db_path.parent.name == "data"


def test_main_reports_config_error_without_traceback(monkeypatch, capsys):
    def invalid_settings():
        raise ConfigError("BOT_TOKEN is missing")

    monkeypatch.setattr(bot_module, "load_settings", invalid_settings)
    assert asyncio.run(bot_module.main()) == 1
    output = capsys.readouterr()
    assert "BOT_TOKEN" in output.out
    assert output.err == ""


@pytest.mark.asyncio
async def test_start_source_and_unknown(configured, fake_user_factory):
    handlers, _ = configured
    handlers.settings = Settings("unused", ADMIN_CHAT_ID, WEBAPP_URL + "?a=1", handlers.settings.db_path)
    source_message = FakeMessage(fake_user_factory(), text="/start ig")
    await handlers.start(source_message)
    assert source_message.calls == ["photo", "answer", "answer"]
    assert len(source_message.photos) == 1
    photo, photo_kwargs = source_message.photos[0]
    assert isinstance(photo, FSInputFile)
    assert photo.path == bot_module.WELCOME_PHOTO
    assert photo_kwargs["caption"] == t("welcome_caption")
    assert "reply_markup" not in photo_kwargs
    text, kwargs = source_message.answers[0]
    assert text == t("start_greeting")
    assert isinstance(kwargs["reply_markup"], ReplyKeyboardMarkup)
    button = kwargs["reply_markup"].keyboard[0][0]
    assert button.text == t("open_button")
    assert button.web_app.url == WEBAPP_URL + "?a=1&src=ig"
    info_text, info_kwargs = source_message.answers[1]
    assert info_text == t("more_info_text")
    assert isinstance(info_kwargs["reply_markup"], InlineKeyboardMarkup)
    info_button = info_kwargs["reply_markup"].inline_keyboard[0][0]
    assert info_button.text == t("more_info_button")
    assert info_button.url == "https://birjoyda.vercel.app/quantum-psychology"
    unknown_message = FakeMessage(fake_user_factory(), text="/start unknown")
    await handlers.start(unknown_message)
    assert unknown_message.answers[0][1]["reply_markup"].keyboard[0][0].web_app.url == WEBAPP_URL + "?a=1"
    plain_message = FakeMessage(fake_user_factory(), text="/start")
    await handlers.start(plain_message)
    assert plain_message.answers[0][1]["reply_markup"].keyboard[0][0].web_app.url == WEBAPP_URL + "?a=1"
    fallback = FakeMessage(fake_user_factory(), text="hello")
    await handlers.fallback(fallback)
    assert fallback.answers[0][0] == t("fallback_hint")
    assert fallback.answers[0][1]["reply_markup"].keyboard[0][0].web_app.url == WEBAPP_URL + "?a=1"


@pytest.mark.asyncio
async def test_start_photo_error_still_sends_greeting(configured, fake_user_factory, caplog):
    handlers, _ = configured
    message = FakeMessage(fake_user_factory(), text="/start ig", photo_error=RuntimeError("photo unavailable"))

    await handlers.start(message)

    assert message.answers[0][0] == t("start_greeting")
    assert isinstance(message.answers[0][1]["reply_markup"], ReplyKeyboardMarkup)
    assert message.answers[0][1]["reply_markup"].keyboard[0][0].web_app.url == WEBAPP_URL + "?src=ig"
    info_text, info_kwargs = message.answers[1]
    assert info_text == t("more_info_text")
    assert isinstance(info_kwargs["reply_markup"], InlineKeyboardMarkup)
    info_button = info_kwargs["reply_markup"].inline_keyboard[0][0]
    assert info_button.text == t("more_info_button")
    assert info_button.url == "https://birjoyda.vercel.app/quantum-psychology"
    assert "Could not send welcome photo: RuntimeError" in caplog.text


def test_welcome_photo_exists():
    assert bot_module.WELCOME_PHOTO.exists()


@pytest.mark.asyncio
async def test_valid_lead_saved_and_delivered(configured, fake_user_factory):
    handlers, storage = configured
    message = FakeMessage(fake_user_factory(), data=payload())
    bot = FakeBot()
    await handlers.web_app_data(message, bot)
    rows = await storage.all_rows()
    assert len(rows) == 1
    assert rows[0]["delivered"] == 1
    assert bot.sent[0][0] == ADMIN_CHAT_ID
    assert bot.sent[0][2]["parse_mode"] == ParseMode.HTML
    assert str(rows[0]["id"]) in bot.sent[0][1]
    assert message.answers[0][0] == t("thanks", "lat")


@pytest.mark.asyncio
async def test_send_error_leaves_undelivered_then_retry(configured, fake_user_factory):
    handlers, storage = configured
    message = FakeMessage(fake_user_factory(), data=payload())
    await handlers.web_app_data(message, FakeBot(fail=True))
    assert (await storage.all_rows())[0]["delivered"] == 0
    assert message.answers[0][0] == t("thanks", "lat")
    bot = FakeBot()
    await handlers.retry_undelivered_once(bot)
    assert len(bot.sent) == 1
    assert (await storage.all_rows())[0]["delivered"] == 1


@pytest.mark.asyncio
async def test_retry_skips_lead_while_fresh_delivery_is_in_flight(configured, fake_user_factory):
    handlers, storage = configured
    sending = asyncio.Event()
    release = asyncio.Event()

    class BlockingBot(FakeBot):
        async def send_message(self, chat_id, text, **kwargs):
            sending.set()
            await release.wait()
            await super().send_message(chat_id, text, **kwargs)

    bot = BlockingBot()
    message = FakeMessage(fake_user_factory(), data=payload())
    delivery = asyncio.create_task(handlers.web_app_data(message, bot))
    try:
        await asyncio.wait_for(sending.wait(), timeout=1)
        rows = await storage.all_rows()
        assert rows[0]["id"] in handlers._delivering_ids
        await asyncio.wait_for(handlers.retry_undelivered_once(bot), timeout=1)
        assert bot.sent == []
    finally:
        release.set()
        await delivery

    assert len(bot.sent) == 1
    assert handlers._delivering_ids == set()
    assert (await storage.all_rows())[0]["delivered"] == 1
    assert message.answers[0][0] == t("thanks", "lat")


@pytest.mark.asyncio
async def test_retry_skips_stale_row_after_fresh_delivery_finishes(configured, fake_user_factory):
    handlers, storage = configured
    await handlers.web_app_data(
        FakeMessage(fake_user_factory(), data=payload()), FakeBot(fail=True)
    )
    fresh_sending = asyncio.Event()
    release_fresh = asyncio.Event()
    retry_sending = asyncio.Event()
    release_retry = asyncio.Event()

    class BlockingBot(FakeBot):
        def __init__(self, sending, release):
            super().__init__()
            self.sending = sending
            self.release = release

        async def send_message(self, chat_id, text, **kwargs):
            self.sending.set()
            await self.release.wait()
            await super().send_message(chat_id, text, **kwargs)

    fresh_bot = BlockingBot(fresh_sending, release_fresh)
    retry_bot = BlockingBot(retry_sending, release_retry)
    fresh = asyncio.create_task(
        handlers.web_app_data(FakeMessage(fake_user_factory(id=2), data=payload()), fresh_bot)
    )
    retry = None
    try:
        await asyncio.wait_for(fresh_sending.wait(), timeout=EVENT_TIMEOUT_SECONDS)
        retry = asyncio.create_task(handlers.retry_undelivered_once(retry_bot))
        await asyncio.wait_for(retry_sending.wait(), timeout=EVENT_TIMEOUT_SECONDS)
        release_fresh.set()
        await fresh
        release_retry.set()
        await retry
    finally:
        release_fresh.set()
        release_retry.set()
        await fresh
        if retry is not None:
            await retry

    assert len(fresh_bot.sent) == 1
    assert len(retry_bot.sent) == 1
    assert all(row["delivered"] == 1 for row in await storage.all_rows())


@pytest.mark.asyncio
async def test_mark_delivered_error_is_logged_and_client_thanked(
    configured, fake_user_factory, monkeypatch, caplog
):
    handlers, storage = configured

    async def fail_mark_delivered(lead_id):
        raise RuntimeError("database write failed")

    monkeypatch.setattr(storage, "mark_delivered", fail_mark_delivered)
    message = FakeMessage(fake_user_factory(), data=payload())
    bot = FakeBot()
    await handlers.web_app_data(message, bot)

    assert len(bot.sent) == 1
    assert message.answers[0][0] == t("thanks", "lat")
    assert (await storage.all_rows())[0]["delivered"] == 0
    assert "Could not mark application delivered id=" in caplog.text
    assert PAYLOAD["name"] not in caplog.text
    assert any(record.exc_info for record in caplog.records if "Could not mark application" in record.message)


@pytest.mark.asyncio
async def test_cooldown_second_lead(configured, fake_user_factory):
    handlers, storage = configured
    user = fake_user_factory()
    await handlers.web_app_data(FakeMessage(user, data=payload()), FakeBot())
    second = FakeMessage(user, data=payload())
    await handlers.web_app_data(second, FakeBot())
    assert second.answers[0][0] == t("cooldown", "lat")
    assert len(await storage.all_rows()) == 1


@pytest.mark.asyncio
async def test_rejected_age_uses_latin(configured, fake_user_factory):
    handlers, storage = configured
    message = FakeMessage(fake_user_factory(), data=payload(age=17))
    await handlers.web_app_data(message, FakeBot())
    assert message.answers[0][0] == t("err_age", "lat")
    assert await storage.all_rows() == []


@pytest.mark.asyncio
async def test_admin_commands_only_in_admin_chat(configured, fake_user_factory):
    handlers, storage = configured
    user = fake_user_factory()
    await handlers.web_app_data(FakeMessage(user, data=payload()), FakeBot())
    admin_export = FakeMessage(user, text="/export", chat_id=ADMIN_CHAT_ID)
    await handlers.export(admin_export)
    assert isinstance(admin_export.documents[0][0], BufferedInputFile)
    assert admin_export.documents[0][0].data.startswith(b"\xef\xbb\xbf")
    admin_stats = FakeMessage(user, text="/stats", chat_id=ADMIN_CHAT_ID)
    await handlers.statistics(admin_stats)
    assert "Жами: 1" in admin_stats.answers[0][0]
    foreign = FakeMessage(user, text="/export", chat_id=99)
    await handlers.export(foreign)
    await handlers.statistics(foreign)
    assert foreign.answers == [] and foreign.documents == []
    assert build_dispatcher(handlers).resolve_used_update_types() == ["message"]


@pytest.mark.asyncio
async def test_admin_message_escapes_user_name(configured, fake_user_factory):
    handlers, _ = configured
    user = fake_user_factory(full_name="<script>alert(1)</script>")
    bot = FakeBot()
    await handlers.web_app_data(FakeMessage(user, data=payload()), bot)
    assert "&lt;script&gt;" in bot.sent[0][1]
    assert "<script>" not in bot.sent[0][1]


@pytest.mark.asyncio
async def test_save_error_does_not_start_cooldown(configured, fake_user_factory, monkeypatch):
    handlers, storage = configured
    original_save = storage.save

    async def fail_save(row):
        raise RuntimeError("disk unavailable")

    monkeypatch.setattr(storage, "save", fail_save)
    user = fake_user_factory()
    failed = FakeMessage(user, data=payload())
    await handlers.web_app_data(failed, FakeBot())
    assert failed.answers[0][0] == t("server_error", "lat")
    monkeypatch.setattr(storage, "save", original_save)
    accepted = FakeMessage(user, data=payload())
    await handlers.web_app_data(accepted, FakeBot())
    assert accepted.answers[0][0] == t("thanks", "lat")
