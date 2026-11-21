"""Telegram handlers for consultation applications from the Mini App."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    BufferedInputFile,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from dotenv import dotenv_values

import catalog
import leads
import stats
import texts
from storage import Storage


logger = logging.getLogger(__name__)
BOT_DIR = Path(__file__).resolve().parent
WELCOME_PHOTO = BOT_DIR / "assets" / "welcome.png"
DEFAULT_DB_PATH = BOT_DIR / "data" / "leads.db"
STATS_DAYS = max(stats.PERIOD_DAYS)


class ConfigError(Exception):
    """Invalid operator configuration."""


@dataclass(frozen=True)
class Settings:
    token: str
    admin_chat_id: int
    webapp_url: str
    db_path: Path


def load_settings(env: dict[str, str] | None = None, dotenv_path: Path | None = None) -> Settings:
    """Read bot-local dotenv values with process variables taking precedence."""
    path = dotenv_path if dotenv_path is not None else BOT_DIR / ".env"
    values = {key: value for key, value in dotenv_values(path).items() if value is not None}
    values.update(os.environ if env is None else env)

    def required(key: str) -> str:
        value = values.get(key, "").strip()
        if not value:
            raise ConfigError(f"Missing required setting: {key}")
        return value

    token = required("BOT_TOKEN")
    raw_admin_id = required("ADMIN_CHAT_ID")
    try:
        admin_chat_id = int(raw_admin_id)
    except ValueError as exc:
        raise ConfigError("ADMIN_CHAT_ID must be an integer") from exc
    webapp_url = required("WEBAPP_URL")
    try:
        url_parts = urlsplit(webapp_url)
        valid_webapp_url = url_parts.scheme == "https" and bool(url_parts.netloc and url_parts.hostname)
    except ValueError as exc:
        raise ConfigError("WEBAPP_URL must be an HTTPS URL with a host") from exc
    if not valid_webapp_url:
        raise ConfigError("WEBAPP_URL must be an HTTPS URL with a host")
    raw_db_path = values.get("DB_PATH", "").strip()
    db_path = Path(raw_db_path) if raw_db_path else DEFAULT_DB_PATH
    if not db_path.is_absolute():
        db_path = BOT_DIR / db_path
    return Settings(token, admin_chat_id, webapp_url, db_path)


def webapp_url(settings: Settings, source: str | None = None) -> str:
    url = settings.webapp_url
    if source in catalog.DEEP_LINK_SOURCES:
        parts = urlsplit(url)
        query = parse_qsl(parts.query, keep_blank_values=True)
        query.append(("src", source))
        url = urlunsplit(parts._replace(query=urlencode(query)))
    return url


def keyboard(settings: Settings, source: str | None = None) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=texts.t("open_button"), web_app=WebAppInfo(url=webapp_url(settings, source)))]],
        resize_keyboard=True,
        is_persistent=True,
    )


def inline_keyboard(settings: Settings, source: str | None = None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=texts.t("open_button"), web_app=WebAppInfo(url=webapp_url(settings, source)))]
        ]
    )


class BotHandlers:
    """Handler logic with injected storage and a testable bot transport."""

    def __init__(self, settings: Settings, storage: Storage) -> None:
        self.settings = settings
        self.storage = storage
        self._accepted_at: dict[int, float] = {}
        self._user_locks: dict[int, asyncio.Lock] = {}
        self._delivering_ids: set[int] = set()

    async def start(self, message: Message) -> None:
        parts = (message.text or "").split(maxsplit=1)
        source = parts[1].strip() if len(parts) > 1 else None
        try:
            await message.answer_photo(
                FSInputFile(WELCOME_PHOTO),
                caption=texts.t("welcome_caption"),
                reply_markup=inline_keyboard(self.settings, source),
            )
        except Exception as exc:
            logger.error("Could not send welcome photo: %s", type(exc).__name__)
        await message.answer(texts.t("start_greeting"), reply_markup=keyboard(self.settings, source))

    async def web_app_data(self, message: Message, bot: Bot) -> None:
        user = message.from_user
        if user is None:
            logger.warning("Mini App application without a Telegram user")
            return
        result = leads.parse_payload(message.web_app_data.data)
        if isinstance(result, leads.Rejected):
            await message.answer(texts.t(result.error_key, result.script))
            return

        async with self._user_locks.setdefault(user.id, asyncio.Lock()):
            now = time.monotonic()
            last = self._accepted_at.get(user.id)
            if last is not None and now - last < catalog.COOLDOWN_SECONDS:
                await message.answer(texts.t("cooldown", result.script))
                return

            row = leads.lead_to_row(result, user)
            row["created_at"] = datetime.now(timezone.utc)
            try:
                lead_id = await self.storage.save(row)
            except Exception as exc:
                logger.error("Could not save application: %s", type(exc).__name__)
                await message.answer(texts.t("server_error", result.script))
                return
            self._accepted_at[user.id] = time.monotonic()
            row["id"] = lead_id
            await self._deliver(row, bot)
            await message.answer(texts.t("thanks", result.script))

    async def _deliver(self, row: dict, bot: Bot) -> None:
        lead_id = row["id"]
        if lead_id in self._delivering_ids:
            return
        self._delivering_ids.add(lead_id)
        try:
            try:
                await bot.send_message(
                    self.settings.admin_chat_id,
                    leads.render_admin(row, datetime.now(timezone.utc)),
                    parse_mode=ParseMode.HTML,
                )
            except Exception as exc:
                logger.error("Could not deliver application id=%s: %s", lead_id, type(exc).__name__)
                return
            try:
                await self.storage.mark_delivered(lead_id)
            except Exception:
                logger.exception("Could not mark application delivered id=%s", lead_id)
        finally:
            self._delivering_ids.discard(lead_id)

    async def retry_undelivered_once(self, bot: Bot) -> None:
        try:
            rows = await self.storage.undelivered()
        except Exception as exc:
            logger.error("Could not read undelivered applications: %s", type(exc).__name__)
            return
        for row in rows:
            if row["id"] in self._delivering_ids:
                continue
            try:
                pending_ids = {pending["id"] for pending in await self.storage.undelivered()}
            except Exception as exc:
                logger.error("Could not recheck undelivered applications: %s", type(exc).__name__)
                return
            if row["id"] not in pending_ids:
                continue
            await self._deliver(row, bot)

    async def retry_forever(self, bot: Bot) -> None:
        while True:
            await asyncio.sleep(catalog.RETRY_INTERVAL_SECONDS)
            await self.retry_undelivered_once(bot)

    async def export(self, message: Message) -> None:
        if message.chat.id != self.settings.admin_chat_id:
            return
        data = await self.storage.export_csv()
        filename = f"leads_{datetime.now(timezone.utc):%Y%m%d}.csv"
        await message.answer_document(BufferedInputFile(data, filename=filename))

    async def statistics(self, message: Message) -> None:
        if message.chat.id != self.settings.admin_chat_id:
            return
        now_utc = datetime.now(timezone.utc)
        rows = await self.storage.rows_since(now_utc - timedelta(days=STATS_DAYS))
        await message.answer(stats.build_stats(rows, now_utc), parse_mode=ParseMode.HTML)

    async def fallback(self, message: Message) -> None:
        await message.answer(texts.t("fallback_hint"), reply_markup=keyboard(self.settings))


def build_dispatcher(handlers: BotHandlers) -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.message.register(handlers.start, CommandStart())
    dispatcher.message.register(handlers.export, Command("export"))
    dispatcher.message.register(handlers.statistics, Command("stats"))
    dispatcher.message.register(handlers.web_app_data, F.web_app_data)
    dispatcher.message.register(handlers.fallback, F.text)
    return dispatcher


async def main() -> int:
    try:
        settings = await asyncio.to_thread(load_settings)
    except ConfigError as exc:
        print(f"Configuration error: {exc}")
        return 1
    logging.basicConfig(level=logging.INFO)
    storage = Storage(settings.db_path)
    await storage.init()
    bot = Bot(settings.token)
    handlers = BotHandlers(settings, storage)
    dispatcher = build_dispatcher(handlers)
    retry_task = asyncio.create_task(handlers.retry_forever(bot))
    try:
        await dispatcher.start_polling(
            bot,
            drop_pending_updates=True,
            allowed_updates=dispatcher.resolve_used_update_types(),
        )
    finally:
        retry_task.cancel()
        try:
            await retry_task
        except asyncio.CancelledError:
            pass
        await storage.close()
        await bot.session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
