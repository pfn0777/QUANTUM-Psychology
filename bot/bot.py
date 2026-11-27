"""Telegram handlers for consultation applications from the Mini App."""

from __future__ import annotations

import asyncio
import ipaddress
import logging
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlsplit, urlunsplit

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.exceptions import ClientDecodeError, TelegramAPIError, TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    BotCommand,
    BotCommandScopeChat,
    BotCommandScopeDefault,
    BufferedInputFile,
    CallbackQuery,
    Chat,
    FSInputFile,
    InaccessibleMessage,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    MenuButtonCommands,
    Message,
    ReplyKeyboardMarkup,
    User,
    WebAppInfo,
)
from aiohttp import web
from dotenv import dotenv_values

import admin_panel
import callbacks
import catalog
import content
import leads
import panel_server
import showcase
import stats
import texts
from storage import Storage


logger = logging.getLogger(__name__)
BOT_DIR = Path(__file__).resolve().parent
WELCOME_PHOTO = BOT_DIR / "assets" / "welcome.png"
MORE_INFO_URL = "https://birjoyda.vercel.app/quantum-psychology"
DEFAULT_DB_PATH = BOT_DIR / "data" / "leads.db"
DEFAULT_PANEL_PORT = 8090
MIN_PANEL_PORT = 1
MAX_PANEL_PORT = 65535
MAX_DNS_NAME_LENGTH = 253
MAX_DNS_LABEL_LENGTH = 63
DNS_LABEL_PATTERN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?")
STATS_DAYS = max(stats.PERIOD_DAYS)


class ConfigError(Exception):
    """Invalid operator configuration."""


@dataclass(frozen=True)
class Settings:
    token: str
    admin_chat_id: int
    webapp_url: str
    db_path: Path
    viewer_ids: frozenset[int] = frozenset()
    panel_url: str = ""
    panel_port: int = DEFAULT_PANEL_PORT


def user_commands() -> list[BotCommand]:
    return [BotCommand(command="start", description=texts.t("cmd_start"))]


def admin_commands() -> list[BotCommand]:
    return [
        BotCommand(command="admin", description=texts.t("cmd_admin")),
        BotCommand(command="start", description=texts.t("cmd_start")),
        BotCommand(command="stats", description=texts.t("cmd_stats")),
        BotCommand(command="export", description=texts.t("cmd_export")),
    ]


async def setup_commands(bot: Bot, settings: Settings) -> None:
    try:
        await bot.set_my_commands(user_commands(), scope=BotCommandScopeDefault())
    except Exception as exc:
        logger.error("Could not set bot commands: %s", type(exc).__name__)
    for chat_id in (settings.admin_chat_id, *settings.viewer_ids):
        try:
            await bot.set_my_commands(admin_commands(), scope=BotCommandScopeChat(chat_id=chat_id))
        except Exception as exc:
            logger.error("Could not set bot commands: %s", type(exc).__name__)
    menu_chat_ids = set(settings.viewer_ids)
    if settings.admin_chat_id > 0:
        menu_chat_ids.add(settings.admin_chat_id)
    menu_button = MenuButtonCommands()
    for chat_id in menu_chat_ids:
        try:
            await bot.set_chat_menu_button(chat_id=chat_id, menu_button=menu_button)
        except Exception as exc:
            logger.error("Could not set chat menu button: %s", type(exc).__name__)


def _is_valid_panel_host(host: str | None) -> bool:
    if not host:
        return False
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return len(host) <= MAX_DNS_NAME_LENGTH and all(
            len(label) <= MAX_DNS_LABEL_LENGTH and DNS_LABEL_PATTERN.fullmatch(label)
            for label in host.split(".")
        )
    return True


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

    panel_url = values.get("PANEL_URL", "")
    if panel_url:
        panel_url_error = "PANEL_URL must be an HTTPS URL with a host, no whitespace, and a valid port if specified"
        if any(character.isspace() for character in panel_url):
            raise ConfigError(panel_url_error)
        try:
            parsed = urlparse(panel_url)
            _ = parsed.port  # Access validates the port syntax and range.
        except ValueError as exc:
            raise ConfigError(panel_url_error) from exc
        if parsed.scheme != "https" or not _is_valid_panel_host(parsed.hostname):
            raise ConfigError(panel_url_error)

    viewer_ids: frozenset[int] = frozenset()
    raw_viewer_ids = values.get("STATS_VIEWER_IDS", "").strip()
    if raw_viewer_ids:
        viewer_error = "STATS_VIEWER_IDS must be comma-separated positive integers"
        items = [item.strip() for item in raw_viewer_ids.removesuffix(",").split(",")]
        if not all(item.isdecimal() for item in items):
            raise ConfigError(viewer_error)
        try:
            viewer_ids = frozenset(int(item) for item in items)
        except ValueError as exc:
            raise ConfigError(viewer_error) from exc
        if 0 in viewer_ids:
            raise ConfigError(viewer_error)

    port_error = f"PANEL_PORT must be an integer between {MIN_PANEL_PORT} and {MAX_PANEL_PORT}"
    try:
        panel_port = int(values.get("PANEL_PORT", str(DEFAULT_PANEL_PORT)))
    except ValueError as exc:
        raise ConfigError(port_error) from exc
    if not MIN_PANEL_PORT <= panel_port <= MAX_PANEL_PORT:
        raise ConfigError(port_error)

    raw_db_path = values.get("DB_PATH", "").strip()
    db_path = Path(raw_db_path) if raw_db_path else DEFAULT_DB_PATH
    if not db_path.is_absolute():
        db_path = BOT_DIR / db_path
    return Settings(
        token, admin_chat_id, webapp_url, db_path,
        viewer_ids=viewer_ids, panel_url=panel_url, panel_port=panel_port,
    )


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
        keyboard=[
            [KeyboardButton(text=texts.t("open_button"), web_app=WebAppInfo(url=webapp_url(settings, source)))],
            [KeyboardButton(text=texts.t("results_button")), KeyboardButton(text=texts.t("coaching_button"))],
            [KeyboardButton(text=texts.t("about_button")), KeyboardButton(text=texts.t("contact_button"))],
            [KeyboardButton(text=texts.t("callback_button"), request_contact=True)],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def more_info_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=texts.t("more_info_button"), url=MORE_INFO_URL)]],
    )


class BotHandlers:
    """Handler logic with injected storage and a testable bot transport."""

    def __init__(self, settings: Settings, storage: Storage, showcase_instance: showcase.Showcase | None = None) -> None:
        self.settings = settings
        self.storage = storage
        self.showcase = showcase_instance if showcase_instance is not None else showcase.Showcase()
        self._accepted_at: dict[int, float] = {}
        self._callback_accepted_at: dict[int, float] = {}
        self._user_locks: dict[int, asyncio.Lock] = {}
        self._delivering_ids: set[int] = set()
        self._delivering_callback_ids: set[int] = set()

    async def start(self, message: Message) -> None:
        parts = (message.text or "").split(maxsplit=1)
        source = parts[1].strip() if len(parts) > 1 else None
        if message.from_user is not None:
            user_source = source if source in catalog.DEEP_LINK_SOURCES else None
            await self._record_user(message.from_user, user_source)
        try:
            await message.answer_photo(
                FSInputFile(WELCOME_PHOTO),
                caption=texts.t("welcome_caption"),
                reply_markup=more_info_keyboard(),
            )
        except Exception as exc:
            logger.error("Could not send welcome photo: %s", type(exc).__name__)
            await message.answer(texts.t("welcome_caption"), reply_markup=more_info_keyboard())
        await message.answer(texts.t("start_greeting"), reply_markup=keyboard(self.settings, source))
        try:
            await self.showcase.send_video(message.bot, message.chat.id, texts.TEXTS["cyr"])
        except Exception as exc:
            logger.error("Could not send start video: %s", type(exc).__name__)

    async def results(self, message: Message) -> None:
        await self.showcase.send_results(message.bot, message.chat.id, 1, texts.TEXTS["cyr"])

    async def coaching(self, message: Message) -> None:
        await self.showcase.send_video(message.bot, message.chat.id, texts.TEXTS["cyr"])

    async def about(self, message: Message) -> None:
        await self.showcase.send_about(message.bot, message.chat.id, texts.TEXTS["cyr"])

    async def contact_info(self, message: Message) -> None:
        await self.showcase.send_contact(message.bot, message.chat.id, texts.TEXTS["cyr"])

    async def showcase_callback(self, callback: CallbackQuery) -> None:
        await self.showcase.handle_callback(callback, texts.TEXTS["cyr"])

    async def contact(self, message: Message, bot: Bot) -> None:
        user = message.from_user
        phone = callbacks.own_contact_phone(message.contact, user.id if user is not None else None)
        if phone is None:
            await message.answer(texts.t("callback_not_own"))
            return

        assert user is not None
        async with self._user_locks.setdefault(user.id, asyncio.Lock()):
            now = time.monotonic()
            last = self._callback_accepted_at.get(user.id)
            if last is not None and now - last < catalog.COOLDOWN_SECONDS:
                await message.answer(texts.t("callback_cooldown"))
                return

            row = callbacks.callback_row(user, phone, datetime.now(timezone.utc))
            try:
                callback_id = await self.storage.save_callback(row)
            except Exception as exc:
                logger.error("Could not save callback request: %s", type(exc).__name__)
                await message.answer(texts.t("server_error"))
                return
            self._callback_accepted_at[user.id] = time.monotonic()
            row["id"] = callback_id
            self._delivering_callback_ids.add(callback_id)
            try:
                await self._record_user(user, None)
            finally:
                self._delivering_callback_ids.discard(callback_id)
            await self._deliver_callback(row, bot)
            await message.answer(texts.t("callback_thanks"), reply_markup=keyboard(self.settings))

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
            # Keep the retry loop from delivering the lead while the user is being recorded.
            self._delivering_ids.add(lead_id)
            try:
                await self._record_user(user, None)
            finally:
                self._delivering_ids.discard(lead_id)
            await self._deliver(row, bot)
            await message.answer(texts.t("thanks", result.script))

    async def _record_user(self, user: User, source: str | None) -> None:
        try:
            await self.storage.upsert_user(
                user.id, user.username, user.full_name, source, datetime.now(timezone.utc)
            )
        except Exception as exc:
            logger.error("Could not record Telegram user: %s", type(exc).__name__)

    async def _deliver(self, row: dict, bot: Bot) -> None:
        lead_id = row["id"]
        if lead_id in self._delivering_ids:
            return
        self._delivering_ids.add(lead_id)
        try:
            try:
                await bot.send_message(
                    self.settings.admin_chat_id,
                    leads.render_admin(row, _created_at(row)),
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

    async def _deliver_callback(self, row: dict, bot: Bot) -> None:
        callback_id = row["id"]
        if callback_id in self._delivering_callback_ids:
            return
        self._delivering_callback_ids.add(callback_id)
        try:
            try:
                await bot.send_message(
                    self.settings.admin_chat_id,
                    callbacks.render_callback_admin(row, _created_at(row)),
                    parse_mode=ParseMode.HTML,
                )
                await self.storage.mark_callback_delivered(callback_id)
            except Exception as exc:
                logger.error("Could not deliver callback request id=%s: %s", callback_id, type(exc).__name__)
        finally:
            self._delivering_callback_ids.discard(callback_id)

    async def retry_undelivered_once(self, bot: Bot) -> None:
        try:
            rows = await self.storage.undelivered()
        except Exception as exc:
            logger.error("Could not read undelivered applications: %s", type(exc).__name__)
            rows = []
        for row in rows:
            if row["id"] in self._delivering_ids:
                continue
            try:
                pending_ids = {pending["id"] for pending in await self.storage.undelivered()}
            except Exception as exc:
                logger.error("Could not recheck undelivered applications: %s", type(exc).__name__)
                break
            if row["id"] not in pending_ids:
                continue
            await self._deliver(row, bot)

        try:
            callback_rows = await self.storage.undelivered_callbacks()
        except Exception as exc:
            logger.error("Could not read undelivered callback requests: %s", type(exc).__name__)
            return
        for row in callback_rows:
            if row["id"] in self._delivering_callback_ids:
                continue
            try:
                pending_ids = {pending["id"] for pending in await self.storage.undelivered_callbacks()}
            except Exception as exc:
                logger.error("Could not recheck undelivered callback requests: %s", type(exc).__name__)
                break
            if row["id"] not in pending_ids:
                continue
            await self._deliver_callback(row, bot)

    async def retry_forever(self, bot: Bot) -> None:
        while True:
            await asyncio.sleep(catalog.RETRY_INTERVAL_SECONDS)
            await self.retry_undelivered_once(bot)

    def _can_view(self, chat: Chat) -> bool:
        return chat.id == self.settings.admin_chat_id or (
            getattr(chat, "type", None) == "private" and chat.id in self.settings.viewer_ids
        )

    async def export(self, message: Message) -> None:
        if not self._can_view(message.chat):
            return
        data = await self.storage.export_csv()
        filename = f"leads_{datetime.now(timezone.utc):%Y%m%d}.csv"
        await message.answer_document(BufferedInputFile(data, filename=filename))

    async def statistics(self, message: Message) -> None:
        if not self._can_view(message.chat):
            return
        now_utc = datetime.now(timezone.utc)
        rows = await self.storage.rows_since(now_utc - timedelta(days=STATS_DAYS))
        await message.answer(stats.build_stats(rows, now_utc), parse_mode=ParseMode.HTML)

    async def _admin_overview(self, now_utc: datetime) -> str:
        since = now_utc - timedelta(days=admin_panel.LOOKBACK_DAYS)
        return admin_panel.build_overview(
            await self.storage.count_users(),
            await self.storage.user_rows_since(since),
            await self.storage.count_lead_users(),
            await self.storage.rows_since(since),
            await self.storage.count_undelivered(),
            now_utc,
        )

    def _admin_keyboard(self, chat: Chat) -> InlineKeyboardMarkup:
        if chat.type == "private" and self.settings.panel_url:
            return admin_panel.panel_keyboard(self.settings.panel_url)
        return admin_panel.panel_keyboard()

    async def admin_menu(self, message: Message) -> None:
        if not self._can_view(message.chat):
            return
        try:
            try:
                overview = await self._admin_overview(datetime.now(timezone.utc))
            except Exception as exc:
                logger.error("Could not read admin panel data: %s", type(exc).__name__)
                await message.answer(texts.t("admin_read_error"))
                return
            await message.answer(overview, parse_mode=ParseMode.HTML, reply_markup=self._admin_keyboard(message.chat))
        except (TelegramAPIError, ClientDecodeError) as exc:
            logger.error("Could not send admin panel menu: %s", type(exc).__name__)

    async def _admin_content(self, data: str | None, now_utc: datetime) -> str | BufferedInputFile | None:
        if data == admin_panel.CB_OVERVIEW:
            return await self._admin_overview(now_utc)
        since = now_utc - timedelta(days=admin_panel.LOOKBACK_DAYS)
        if data == admin_panel.CB_USERS:
            return admin_panel.build_users(
                await self.storage.count_users(), await self.storage.user_rows_since(since), now_utc
            )
        if data == admin_panel.CB_LEADS:
            rows = await self.storage.rows_since(now_utc - timedelta(days=STATS_DAYS))
            return stats.build_stats(rows, now_utc)
        if data == admin_panel.CB_DAILY:
            return admin_panel.build_daily(
                await self.storage.user_rows_since(since), await self.storage.rows_since(since), now_utc
            )
        if data == admin_panel.CB_CSV_LEADS:
            return BufferedInputFile(await self.storage.export_csv(), filename=f"leads_{now_utc:%Y%m%d}.csv")
        if data == admin_panel.CB_CSV_USERS:
            return BufferedInputFile(await self.storage.export_users_csv(), filename=f"users_{now_utc:%Y%m%d}.csv")
        return None

    async def admin_callback(self, callback: CallbackQuery) -> None:
        try:
            await callback.answer()
        except (TelegramAPIError, ClientDecodeError) as exc:
            logger.error("Could not answer admin panel callback: %s", type(exc).__name__)
        message = callback.message
        if message is None or isinstance(message, InaccessibleMessage) or not self._can_view(message.chat):
            return
        try:
            try:
                content = await self._admin_content(callback.data, datetime.now(timezone.utc))
            except Exception as exc:
                logger.error("Could not read admin panel data: %s", type(exc).__name__)
                await message.answer(texts.t("admin_read_error"))
                return
            if isinstance(content, BufferedInputFile):
                await message.answer_document(content)
            elif content is not None:
                reply_markup = (
                    self._admin_keyboard(message.chat)
                    if callback.data == admin_panel.CB_OVERVIEW
                    else admin_panel.back_keyboard()
                )
                try:
                    await message.edit_text(content, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
                except TelegramBadRequest as exc:
                    if "message is not modified" not in exc.message.lower():
                        raise
                    logger.info("Admin panel message is not modified")
        except (TelegramAPIError, ClientDecodeError) as exc:
            logger.error("Could not send admin panel response: %s", type(exc).__name__)

    async def fallback(self, message: Message) -> None:
        await message.answer(texts.t("fallback_hint"), reply_markup=keyboard(self.settings))


def _created_at(row: dict) -> datetime:
    value = row["created_at"]
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return value


def build_dispatcher(handlers: BotHandlers) -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.message.register(handlers.start, CommandStart())
    dispatcher.message.register(handlers.export, Command("export"))
    dispatcher.message.register(handlers.statistics, Command("stats"))
    dispatcher.message.register(handlers.admin_menu, Command("admin"))
    dispatcher.message.register(handlers.web_app_data, F.web_app_data)
    for key, handler in (
        ("results_button", handlers.results),
        ("coaching_button", handlers.coaching),
        ("about_button", handlers.about),
        ("contact_button", handlers.contact_info),
    ):
        dispatcher.message.register(
            handler, F.text.in_({texts.TEXTS["cyr"][key], texts.TEXTS["lat"][key]})
        )
    dispatcher.message.register(handlers.contact, F.contact)
    dispatcher.message.register(handlers.fallback, F.text)
    dispatcher.callback_query.register(handlers.showcase_callback, F.data.startswith(content.SHOW_PREFIX))
    dispatcher.callback_query.register(handlers.admin_callback, F.data.startswith(admin_panel.CALLBACK_PREFIX))
    return dispatcher


async def _start_panel_safely(settings: Settings, storage: Storage, bot: Bot) -> web.AppRunner | None:
    if not settings.panel_url:
        return None
    try:
        return await panel_server.start_panel(panel_server.create_app(settings, storage, bot))
    except OSError as exc:
        logger.error("Could not start admin panel: %s", type(exc).__name__)
        return None


async def _shutdown(retry_task: asyncio.Task, runner: web.AppRunner | None, storage: Storage, bot: Bot) -> None:
    retry_task.cancel()
    try:
        try:
            await retry_task
        except asyncio.CancelledError:
            pass
    finally:
        try:
            if runner is not None:
                await runner.cleanup()
        finally:
            try:
                await storage.close()
            finally:
                await bot.session.close()


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
    await setup_commands(bot, settings)
    handlers = BotHandlers(settings, storage)
    dispatcher = build_dispatcher(handlers)
    retry_task = asyncio.create_task(handlers.retry_forever(bot))
    runner = None
    try:
        runner = await _start_panel_safely(settings, storage, bot)
        await dispatcher.start_polling(
            bot,
            allowed_updates=dispatcher.resolve_used_update_types(),
            close_bot_session=False,
        )
    finally:
        await _shutdown(retry_task, runner, storage, bot)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
