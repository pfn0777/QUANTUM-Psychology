"""Tests for Mini App bot handlers without Telegram network access."""

import asyncio
import json
from contextlib import nullcontext
from datetime import datetime, timedelta, timezone
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, call

import pytest
from aiogram.enums import ParseMode
from aiogram.exceptions import ClientDecodeError, TelegramBadRequest, TelegramNetworkError
from aiogram.methods import EditMessageText
from aiogram.types import (
    BotCommandScopeChat,
    BotCommandScopeDefault,
    BufferedInputFile,
    Chat,
    FSInputFile,
    InaccessibleMessage,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardMarkup,
)

import admin_panel
import bot as bot_module
import leads
from bot import BotHandlers, ConfigError, Settings, build_dispatcher, load_settings
from storage import Storage
from texts import t


ADMIN_CHAT_ID = -100123
VIEWER_ID = 111
OTHER_VIEWER_ID = 222
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


class FakeMessage:
    def __init__(self, user, *, text=None, data=None, chat_id=1, chat_type="private", photo_error=None):
        self.from_user = user
        self.text = text
        self.chat = Chat(id=chat_id, type=chat_type)
        self.web_app_data = SimpleNamespace(data=data) if data is not None else None
        self.answers = []
        self.photos = []
        self.calls = []
        self.photo_error = photo_error
        self.documents = []
        self.edits = []

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

    async def edit_text(self, text, **kwargs):
        self.edits.append((text, kwargs))


class FakeCallback:
    def __init__(self, data, message):
        self.data = data
        self.message = message
        self.answer = AsyncMock()


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


@pytest.mark.parametrize("overrides, expected", [
    ({}, "BOT_TOKEN"),
    ({"ADMIN_CHAT_ID": "x"}, "ADMIN_CHAT_ID"),
    *[({"WEBAPP_URL": value}, "WEBAPP_URL") for value in ("http://example.org", "https://")],
    *[({"STATS_VIEWER_IDS": value}, "^STATS_VIEWER_IDS must be comma-separated positive integers$")
      for value in ("abc", "0", "-5", "111,,222")],
    *[({"PANEL_URL": value}, "PANEL_URL") for value in (
        "http://example.org", "https://", "https://exa mple.org", "https://example.org:bogus",
        " https://example.org", "https://example.org/\npath", "https://exa<mple.org", "https://.",
        "https://example..org", "https://-bad.example.org")],
    *[({"PANEL_PORT": value}, "PANEL_PORT") for value in ("x", "0", "65536")],
])
def test_invalid_settings(tmp_path: Path, overrides: dict[str, str], expected: str):
    values = {"ADMIN_CHAT_ID": "-1", "WEBAPP_URL": WEBAPP_URL}
    if overrides:
        values.update({"BOT_TOKEN": "token", **overrides})
    with pytest.raises(ConfigError, match=expected):
        load_settings(values, tmp_path / "missing.example")


@pytest.mark.parametrize("viewer_ids, panel_url", [
    ("111, 222", "https://panel.example.org"), ("111,222,", "https://panel.example.org:8443/path"),
    ("", "https://192.0.2.1"), (None, ""),
])
def test_dotenv_and_environment_override(tmp_path: Path, viewer_ids: str | None, panel_url: str):
    path = tmp_path / "test.example"
    path.write_text("BOT_TOKEN=from_file\nADMIN_CHAT_ID=-42\nWEBAPP_URL=https://example.org\n", encoding="utf-8")
    env = {"BOT_TOKEN": "from_env"}
    if viewer_ids is not None:
        env.update(STATS_VIEWER_IDS=viewer_ids, PANEL_URL=panel_url, PANEL_PORT="65535")
    settings = load_settings(env, path)
    assert settings.token == "from_env"
    assert settings.admin_chat_id == -42
    assert settings.db_path == bot_module.BOT_DIR / "data" / "leads.db"
    assert settings.viewer_ids == (frozenset({VIEWER_ID, OTHER_VIEWER_ID}) if viewer_ids else frozenset())
    assert isinstance(settings.viewer_ids, frozenset)
    assert settings.panel_url == panel_url
    assert settings.panel_port == (65535 if viewer_ids is not None else 8090)


def test_main_reports_config_error_without_traceback(monkeypatch, capsys):
    def invalid_settings():
        raise ConfigError("BOT_TOKEN is missing")

    monkeypatch.setattr(bot_module, "load_settings", invalid_settings)
    assert asyncio.run(bot_module.main()) == 1
    output = capsys.readouterr()
    assert "BOT_TOKEN" in output.out
    assert output.err == ""


@pytest.mark.parametrize("viewer_ids, failure_count", [
    ((), 0), ((), 2), ((VIEWER_ID, OTHER_VIEWER_ID), 0), ((VIEWER_ID, OTHER_VIEWER_ID), 3),
])
async def test_setup_commands_registers_scopes_even_after_errors(tmp_db_path, caplog, viewer_ids, failure_count):
    set_commands = AsyncMock(side_effect=[RuntimeError] * failure_count + [None] * (2 + len(viewer_ids)))
    settings = Settings("unused", ADMIN_CHAT_ID, WEBAPP_URL, tmp_db_path, viewer_ids=frozenset(viewer_ids))
    await bot_module.setup_commands(SimpleNamespace(set_my_commands=set_commands), settings)
    user_commands, admin_commands = bot_module.user_commands(), bot_module.admin_commands()
    assert set_commands.await_count == 2 + len(viewer_ids)
    assert set_commands.await_args_list[0] == call(user_commands, scope=BotCommandScopeDefault())
    assert set_commands.await_args_list[1] == call(admin_commands, scope=BotCommandScopeChat(chat_id=ADMIN_CHAT_ID))
    for viewer_id in settings.viewer_ids:
        assert call(admin_commands, scope=BotCommandScopeChat(chat_id=viewer_id)) in set_commands.await_args_list[2:]
    assert [command.command for command in user_commands] == ["start"]
    assert [command.command for command in admin_commands] == ["admin", "start", "stats", "export"]
    assert admin_commands[0].description == t("cmd_admin")
    assert all(command.description for command in user_commands + admin_commands)
    assert caplog.text.count("Could not set bot commands: RuntimeError") == failure_count


@pytest.mark.asyncio
async def test_start_source_and_unknown(configured, fake_user_factory):
    handlers, _ = configured
    handlers.settings = Settings("unused", ADMIN_CHAT_ID, WEBAPP_URL + "?a=1", handlers.settings.db_path)
    source_message = FakeMessage(fake_user_factory(), text="/start ig")
    await handlers.start(source_message)
    assert source_message.calls == ["photo", "answer"]
    assert len(source_message.photos) == 1
    assert len(source_message.answers) == 1
    photo, photo_kwargs = source_message.photos[0]
    assert isinstance(photo, FSInputFile)
    assert photo.path == bot_module.WELCOME_PHOTO
    assert photo_kwargs["caption"] == t("welcome_caption")
    assert isinstance(photo_kwargs["reply_markup"], InlineKeyboardMarkup)
    info_button = photo_kwargs["reply_markup"].inline_keyboard[0][0]
    assert info_button.text == t("more_info_button")
    assert info_button.url == "https://birjoyda.vercel.app/quantum-psychology"
    text, kwargs = source_message.answers[0]
    assert text == "👇"
    assert isinstance(kwargs["reply_markup"], ReplyKeyboardMarkup)
    button = kwargs["reply_markup"].keyboard[0][0]
    assert button.text == t("open_button")
    assert button.web_app.url == WEBAPP_URL + "?a=1&src=ig"
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
@pytest.mark.parametrize("argument, expected_source", [("ig", "ig"), ("unknown", None), ("", None)])
async def test_start_records_user_before_reply(configured, fake_user_factory, monkeypatch, argument, expected_source):
    handlers, storage = configured
    user = fake_user_factory(id=42, username=None, full_name="Test Person")
    message = FakeMessage(user, text=f"/start {argument}".strip())
    reply_calls_at_upsert = []

    async def record_user(*args):
        reply_calls_at_upsert.append(message.calls.copy())

    upsert = AsyncMock(side_effect=record_user)
    monkeypatch.setattr(storage, "upsert_user", upsert)
    before = datetime.now(timezone.utc)

    await handlers.start(message)

    upsert.assert_awaited_once()
    user_id, username, full_name, source, seen_at = upsert.await_args.args
    assert (user_id, username, full_name, source) == (user.id, user.username, user.full_name, expected_source)
    assert seen_at.tzinfo is timezone.utc
    assert before <= seen_at <= datetime.now(timezone.utc)
    assert reply_calls_at_upsert == [[]]
    assert message.calls == ["photo", "answer"]


@pytest.mark.asyncio
async def test_start_without_user_skips_upsert(configured, monkeypatch):
    handlers, storage = configured
    upsert = AsyncMock()
    monkeypatch.setattr(storage, "upsert_user", upsert)
    message = FakeMessage(None, text="/start")

    await handlers.start(message)

    upsert.assert_not_awaited()
    assert message.calls == ["photo", "answer"]


@pytest.mark.asyncio
async def test_start_upsert_error_still_replies(configured, fake_user_factory, monkeypatch, caplog):
    handlers, storage = configured
    upsert = AsyncMock(side_effect=RuntimeError("database unavailable"))
    monkeypatch.setattr(storage, "upsert_user", upsert)
    message = FakeMessage(fake_user_factory(), text="/start")

    await handlers.start(message)

    upsert.assert_awaited_once()
    assert message.calls == ["photo", "answer"]
    assert "Could not record Telegram user: RuntimeError" in caplog.text


@pytest.mark.asyncio
async def test_start_photo_error_still_sends_greeting(configured, fake_user_factory, caplog):
    handlers, _ = configured
    message = FakeMessage(fake_user_factory(), text="/start ig", photo_error=RuntimeError("photo unavailable"))

    await handlers.start(message)

    assert message.photos == []
    assert message.calls == ["answer", "answer"]
    assert len(message.answers) == 2
    assert message.answers[0][0] == t("welcome_caption")
    assert isinstance(message.answers[0][1]["reply_markup"], InlineKeyboardMarkup)
    info_button = message.answers[0][1]["reply_markup"].inline_keyboard[0][0]
    assert info_button.text == t("more_info_button")
    assert info_button.url == "https://birjoyda.vercel.app/quantum-psychology"
    assert message.answers[1][0] == "👇"
    assert isinstance(message.answers[1][1]["reply_markup"], ReplyKeyboardMarkup)
    button = message.answers[1][1]["reply_markup"].keyboard[0][0]
    assert button.text == t("open_button")
    assert button.web_app.url == WEBAPP_URL + "?src=ig"
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
    users = await storage.user_rows_since(datetime.fromisoformat(rows[0]["created_at"]))
    assert len(users) == 1
    user = message.from_user
    assert (users[0]["tg_user_id"], users[0]["tg_username"], users[0]["tg_full_name"], users[0]["source"]) == (
        user.id, user.username, user.full_name, None,
    )


@pytest.mark.asyncio
async def test_lead_keeps_start_source(configured, fake_user_factory):
    handlers, storage = configured
    user = fake_user_factory()
    before = datetime.now(timezone.utc)
    await handlers.start(FakeMessage(user, text="/start yt"))
    lead_user = fake_user_factory(id=user.id, username="updated")

    await handlers.web_app_data(FakeMessage(lead_user, data=payload(source="ig")), FakeBot())

    (row,) = await storage.user_rows_since(before)
    assert (row["source"], row["tg_username"]) == ("yt", lead_user.username)


@pytest.mark.asyncio
async def test_lead_upsert_error_still_delivers_and_thanks(configured, fake_user_factory, monkeypatch, caplog):
    handlers, storage = configured
    upsert = AsyncMock(side_effect=RuntimeError("database unavailable"))
    monkeypatch.setattr(storage, "upsert_user", upsert)
    message = FakeMessage(fake_user_factory(), data=payload())
    bot = FakeBot()

    await handlers.web_app_data(message, bot)

    upsert.assert_awaited_once()
    assert len(bot.sent) == 1
    assert (await storage.all_rows())[0]["delivered"] == 1
    assert message.answers[0][0] == t("thanks", "lat")
    assert "Could not record Telegram user: RuntimeError" in caplog.text


@pytest.mark.parametrize("send_error", [RuntimeError("Telegram unavailable"), asyncio.CancelledError()])
async def test_interrupted_delivery_preserves_user_and_pending_lead(configured, fake_user_factory, send_error):
    handlers, storage = configured
    message = FakeMessage(fake_user_factory(), data=payload())
    bot = SimpleNamespace(send_message=AsyncMock(side_effect=send_error))
    cancelled = isinstance(send_error, asyncio.CancelledError)
    with pytest.raises(asyncio.CancelledError) if cancelled else nullcontext():
        await handlers.web_app_data(message, bot)
    assert message.answers == ([] if cancelled else [(t("thanks", "lat"), {})])
    assert (await storage.all_rows())[0]["delivered"] == 0
    assert await storage.count_users() == 1
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


async def test_admin_menu_counts_empty_database_once(configured, monkeypatch):
    handlers, storage = configured
    count_users = AsyncMock(wraps=storage.count_users)
    monkeypatch.setattr(storage, "count_users", count_users)
    message = FakeMessage(None, text="/admin", chat_id=ADMIN_CHAT_ID)
    await handlers.admin_menu(message)
    count_users.assert_awaited_once_with()
    [(content, options)] = message.answers
    assert content.startswith("<b>Админ панел</b>\nФойдаланувчилар: 0\n")
    assert options == {"parse_mode": ParseMode.HTML, "reply_markup": admin_panel.panel_keyboard()}


@pytest.mark.parametrize("chat_id, chat_type, allowed", [
    (ADMIN_CHAT_ID, "group", True), (VIEWER_ID, "private", True),
    (VIEWER_ID, "group", False), (99, "private", False),
])
async def test_admin_commands_and_callback_chat_permissions(configured, fake_user_factory, monkeypatch,
                                                            chat_id, chat_type, allowed):
    handlers, storage = configured
    handlers.settings = replace(handlers.settings, viewer_ids=frozenset({VIEWER_ID}))
    bot = FakeBot()
    await handlers.web_app_data(FakeMessage(fake_user_factory(), data=payload()), bot)
    assert [destination for destination, _, _ in bot.sent] == [ADMIN_CHAT_ID]
    count_users = AsyncMock(wraps=storage.count_users)
    monkeypatch.setattr(storage, "count_users", count_users)
    message = FakeMessage(None, chat_id=chat_id, chat_type=chat_type)
    callback = FakeCallback(admin_panel.CB_OVERVIEW, message)
    await handlers.statistics(message)
    await handlers.export(message)
    await handlers.admin_menu(message)
    await handlers.admin_callback(callback)
    callback.answer.assert_awaited_once_with()
    if not allowed:
        count_users.assert_not_awaited()
        assert message.answers == message.documents == message.edits == []
        return
    [(report, _), (overview, options)] = message.answers
    [(document, _)] = message.documents
    assert "Жами: 1" in report
    assert isinstance(document, BufferedInputFile) and document.data.startswith(b"\xef\xbb\xbf")
    assert overview.startswith("<b>Админ панел</b>\nФойдаланувчилар: 1\n")
    assert options == {"parse_mode": ParseMode.HTML, "reply_markup": admin_panel.panel_keyboard()}
    assert message.edits == [(overview, options)]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "data, heading, read_names, days, keyboard",
    [
        (admin_panel.CB_OVERVIEW, "<b>Админ панел</b>",
         ("count_users", "user_rows_since", "count_lead_users", "rows_since", "count_undelivered"),
         admin_panel.LOOKBACK_DAYS, admin_panel.panel_keyboard),
        (admin_panel.CB_USERS, "<b>Фойдаланувчилар</b>", ("count_users", "user_rows_since"),
         admin_panel.LOOKBACK_DAYS, admin_panel.back_keyboard),
        (admin_panel.CB_LEADS, f"<b>Охирги {bot_module.stats.PERIOD_DAYS[0]} кун</b>", ("rows_since",),
         bot_module.STATS_DAYS, admin_panel.back_keyboard),
        (admin_panel.CB_DAILY, f"<b>{admin_panel.DAILY_DAYS} кунлик динамика</b>", ("user_rows_since", "rows_since"),
         admin_panel.LOOKBACK_DAYS, admin_panel.back_keyboard),
    ],
)
async def test_admin_callback_edits_report(configured, monkeypatch, data, heading, read_names, days, keyboard):
    handlers, storage = configured
    reads = {name: AsyncMock(wraps=getattr(storage, name)) for name in read_names}
    for name, read in reads.items():
        monkeypatch.setattr(storage, name, read)
    message = FakeMessage(None, chat_id=ADMIN_CHAT_ID)
    callback = FakeCallback(data, message)
    before = datetime.now(timezone.utc)

    await handlers.admin_callback(callback)

    [(content, options)] = message.edits
    assert content.splitlines()[0] == heading
    assert options == {"parse_mode": ParseMode.HTML, "reply_markup": keyboard()}
    assert message.answers == message.documents == []
    for name, read in reads.items():
        read.assert_awaited_once()
        if name.endswith("_since"):
            (since,) = read.await_args.args
            assert since.tzinfo is timezone.utc
            assert before <= since + timedelta(days=days) <= datetime.now(timezone.utc)
    callback.answer.assert_awaited_once_with()


@pytest.mark.parametrize("data, export_name, filename_prefix", [
    (admin_panel.CB_CSV_LEADS, "export_csv", "leads"),
    (admin_panel.CB_CSV_USERS, "export_users_csv", "users"),
])
async def test_admin_callback_sends_csv(configured, monkeypatch, data, export_name, filename_prefix):
    handlers, storage = configured
    csv_data = b"csv data\n"
    message = FakeMessage(None, chat_id=ADMIN_CHAT_ID)
    callback = FakeCallback(data, message)

    async def read_csv():
        callback.answer.assert_awaited_once_with()
        return csv_data

    export = AsyncMock(side_effect=read_csv)
    monkeypatch.setattr(storage, export_name, export)
    before = datetime.now(timezone.utc)
    await handlers.admin_callback(callback)

    export.assert_awaited_once_with()
    [(document, _)] = message.documents
    assert isinstance(document, BufferedInputFile)
    assert document.data == csv_data
    assert document.filename in {f"{filename_prefix}_{date:%Y%m%d}.csv" for date in (before, datetime.now(timezone.utc))}
    assert message.edits == message.answers == []
    callback.answer.assert_awaited_once_with()


@pytest.mark.parametrize("data, message", [
    (admin_panel.CB_CSV_USERS, FakeMessage(None, chat_id=99)),
    (admin_panel.CB_OVERVIEW, FakeMessage(None, chat_id=99)),
    (admin_panel.CB_OVERVIEW, None),
    (admin_panel.CB_OVERVIEW, SimpleNamespace(chat=SimpleNamespace(id=VIEWER_ID))),
    (admin_panel.CB_OVERVIEW, InaccessibleMessage(chat=Chat(id=ADMIN_CHAT_ID, type="group"), message_id=1, date=0)),
    ("adm:unknown", FakeMessage(None, chat_id=ADMIN_CHAT_ID)),
])
async def test_admin_callback_ignored_updates_only_answer(configured, monkeypatch, data, message):
    handlers, storage = configured
    handlers.settings = replace(handlers.settings, viewer_ids=frozenset({VIEWER_ID}))
    export = AsyncMock()
    count_users = AsyncMock()
    monkeypatch.setattr(storage, "export_users_csv", export)
    monkeypatch.setattr(storage, "count_users", count_users)
    callback = FakeCallback(data, message)

    await handlers.admin_callback(callback)

    callback.answer.assert_awaited_once_with()
    export.assert_not_awaited()
    count_users.assert_not_awaited()
    if isinstance(message, FakeMessage):
        assert message.edits == message.documents == message.answers == []


@pytest.mark.asyncio
async def test_admin_callback_accepts_unchanged_message(configured, monkeypatch, caplog):
    handlers, _ = configured
    message = FakeMessage(None, chat_id=ADMIN_CHAT_ID)
    error = TelegramBadRequest(EditMessageText(text="same"), "Bad Request: message is not modified")
    monkeypatch.setattr(message, "edit_text", AsyncMock(side_effect=error))
    callback = FakeCallback(admin_panel.CB_OVERVIEW, message)

    with caplog.at_level("INFO", logger=bot_module.logger.name):
        await handlers.admin_callback(callback)

    assert message.answers == message.documents == []
    assert any(record.levelname == "INFO" and "message is not modified" in record.message for record in caplog.records)
    callback.answer.assert_awaited_once_with()


@pytest.mark.parametrize("error_type", [TelegramNetworkError, ClientDecodeError])
@pytest.mark.parametrize("data, read_name, failing_send", [
    (None, "count_users", None), (admin_panel.CB_CSV_USERS, "export_users_csv", None),
    (None, None, "answer"), (None, "count_users", "answer"),
    (admin_panel.CB_OVERVIEW, None, "edit_text"), (admin_panel.CB_OVERVIEW, "count_users", "answer"),
    (admin_panel.CB_CSV_USERS, None, "answer_document"), (admin_panel.CB_OVERVIEW, None, "callback.answer"),
])
async def test_admin_read_and_transport_errors(configured, monkeypatch, caplog, data, read_name, failing_send, error_type):
    handlers, storage = configured
    message = FakeMessage(None, chat_id=ADMIN_CHAT_ID)
    callback = FakeCallback(data, message)
    if read_name:
        monkeypatch.setattr(storage, read_name, AsyncMock(side_effect=RuntimeError("database unavailable")))
    if failing_send:
        if error_type is ClientDecodeError:
            error = ClientDecodeError("synthetic-error-message", ValueError("Invalid response"), "synthetic-error-body")
        else:
            error = TelegramNetworkError(EditMessageText(text="panel"), "https://example.invalid/synthetic-error")
        send = AsyncMock(side_effect=error)
        target, method = (callback, "answer") if failing_send == "callback.answer" else (message, failing_send)
        monkeypatch.setattr(target, method, send)
    if data is None:
        await handlers.admin_menu(message)
    else:
        await handlers.admin_callback(callback)
        callback.answer.assert_awaited_once_with()

    if failing_send:
        send.assert_awaited_once()
        assert error_type.__name__ in caplog.text and "synthetic-error" not in caplog.text
        assert all(record.exc_info is None for record in caplog.records)
    assert message.answers == ([(t("admin_read_error"), {})] if read_name and not failing_send else [])
    assert len(message.edits) == int(failing_send == "callback.answer")
    assert message.documents == []
    if read_name:
        assert "Could not read admin panel data: RuntimeError" in caplog.text


@pytest.mark.asyncio
async def test_dispatcher_registers_admin_before_fallback_and_filters_callbacks(configured, monkeypatch):
    handlers, _ = configured
    dispatcher = build_dispatcher(handlers)
    registered = [handler.callback for handler in dispatcher.message.handlers]
    assert registered.index(handlers.admin_menu) < registered.index(handlers.fallback)
    assert dispatcher.resolve_used_update_types() == ["callback_query", "message"]
    answer = AsyncMock()
    monkeypatch.setattr(Message, "answer", answer)
    message = Message(message_id=1, date=datetime.now(timezone.utc), chat=Chat(id=ADMIN_CHAT_ID, type="group"), text="/admin")
    await dispatcher.message.trigger(message, bot=FakeBot())
    answer.assert_awaited_once()
    assert answer.await_args.kwargs["reply_markup"] == admin_panel.panel_keyboard()

    admin_callback = FakeCallback("adm:unknown", None)
    other_callback = FakeCallback("other:unknown", None)

    await dispatcher.callback_query.trigger(admin_callback)
    await dispatcher.callback_query.trigger(other_callback)

    admin_callback.answer.assert_awaited_once_with()
    other_callback.answer.assert_not_awaited()


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
    upsert = AsyncMock(wraps=storage.upsert_user)
    monkeypatch.setattr(storage, "upsert_user", upsert)

    async def fail_save(row):
        raise RuntimeError("disk unavailable")

    monkeypatch.setattr(storage, "save", fail_save)
    user = fake_user_factory()
    failed = FakeMessage(user, data=payload())
    await handlers.web_app_data(failed, FakeBot())
    assert failed.answers[0][0] == t("server_error", "lat")
    upsert.assert_not_awaited()
    monkeypatch.setattr(storage, "save", original_save)
    accepted = FakeMessage(user, data=payload())
    await handlers.web_app_data(accepted, FakeBot())
    assert accepted.answers[0][0] == t("thanks", "lat")


CREATED_AT_UTC = datetime(2026, 1, 1, 5, 0, tzinfo=timezone.utc)
CREATED_AT_TASHKENT_TEXT = "01.01.2026 10:00"


def make_row(user) -> dict:
    result = leads.parse_payload(payload())
    row = leads.lead_to_row(result, user)
    row["created_at"] = CREATED_AT_UTC
    return row


@pytest.mark.asyncio
async def test_admin_message_shows_created_at_for_new_lead(configured, fake_user_factory):
    handlers, storage = configured
    row = make_row(fake_user_factory())
    row["id"] = await storage.save(row)
    bot = FakeBot()
    await handlers._deliver(row, bot)
    assert CREATED_AT_TASHKENT_TEXT in bot.sent[0][1]


@pytest.mark.asyncio
async def test_admin_message_shows_created_at_on_retry(configured, fake_user_factory):
    handlers, storage = configured
    row = make_row(fake_user_factory())
    row["id"] = await storage.save(row)
    await handlers._deliver(row, FakeBot(fail=True))
    bot = FakeBot()
    await handlers.retry_undelivered_once(bot)
    assert len(bot.sent) == 1
    assert CREATED_AT_TASHKENT_TEXT in bot.sent[0][1]


@pytest.mark.asyncio
async def test_main_polling_keeps_pending_updates(monkeypatch, tmp_db_path):
    captured = {}

    async def fake_start_polling(self, *args, **kwargs):
        captured.update(kwargs)

    async def fake_setup_commands(bot, settings):
        return None

    settings = Settings("unused", ADMIN_CHAT_ID, WEBAPP_URL, tmp_db_path)
    monkeypatch.setattr(bot_module, "load_settings", lambda: settings)
    fake_bot = FakeBot()

    async def close_session():
        return None

    fake_bot.session = SimpleNamespace(close=close_session)
    monkeypatch.setattr(bot_module, "Bot", lambda token: fake_bot)
    monkeypatch.setattr(bot_module, "setup_commands", fake_setup_commands)
    monkeypatch.setattr(bot_module.Dispatcher, "start_polling", fake_start_polling)
    await bot_module.main()
    assert "drop_pending_updates" not in captured
    assert "allowed_updates" in captured
