"""Client-facing Telegram showcase sections and media file-id cache."""

import logging
from pathlib import Path

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto

import content


logger = logging.getLogger(__name__)


class Showcase:
    def __init__(
        self,
        reviews_dir: Path = content.REVIEWS_DIR,
        about_dir: Path = content.ABOUT_DIR,
        video_path: Path = content.COACHING_VIDEO,
    ) -> None:
        self.reviews_dir = reviews_dir
        self.about_dir = about_dir
        self.video_path = video_path
        self._file_ids: dict[str, str] = {}

    @staticmethod
    def _button(text: str, destination: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(text=text, callback_data=f"{content.SHOW_PREFIX}{destination}")

    async def _send_album(self, bot: Bot, chat_id: int, paths: list[Path], texts: dict) -> bool:
        cached = [str(path) for path in paths if str(path) in self._file_ids]

        async def send(use_cache: bool):
            media = [InputMediaPhoto(media=self._file_ids[str(path)] if use_cache and str(path) in self._file_ids
                                     else FSInputFile(path)) for path in paths]
            return await bot.send_media_group(chat_id=chat_id, media=media)

        try:
            try:
                messages = await send(use_cache=True)
            except TelegramBadRequest:
                if not cached:
                    raise
                for path in cached:
                    self._file_ids.pop(path, None)
                messages = await send(use_cache=False)
            for path, message in zip(paths, messages, strict=True):
                if message.photo:
                    self._file_ids[str(path)] = message.photo[-1].file_id
            return True
        except Exception as exc:
            logger.exception("Showcase album failed: %s", type(exc).__name__)
            await bot.send_message(chat_id=chat_id, text=texts["media_unavailable"])
            return False

    async def send_results(self, bot: Bot, chat_id: int, page: int | str | None, texts: dict) -> None:
        albums = content.pages(content.review_photos(self.reviews_dir))
        if not albums:
            logger.warning("Showcase reviews directory has no photos")
            await bot.send_message(chat_id=chat_id, text=texts["results_empty"])
            return
        total = len(albums)
        current = content.clamp_page(page, total)
        if current == 1:
            await bot.send_message(chat_id=chat_id, text=texts["results_intro"])
        if not await self._send_album(bot, chat_id, albums[current - 1], texts):
            return
        rows = []
        if current < total:
            next_page = current + 1
            rows.append([self._button(texts["results_more_button"].format(page=next_page, total=total),
                                      f"rev:{next_page}")])
        rows.append([self._button(texts["nav_coaching"], "video"),
                     self._button(texts["admin_phone_button"], "contact")])
        await bot.send_message(
            chat_id=chat_id,
            text=texts["results_footer"].format(page=current, total=total),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        )

    async def send_video(self, bot: Bot, chat_id: int, texts: dict) -> None:
        if not self.video_path.is_file():
            logger.warning("Showcase video is missing: %s", self.video_path)
            await bot.send_message(chat_id=chat_id, text=texts["media_unavailable"])
            return
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            self._button(texts["nav_results"], "rev:1"),
            self._button(texts["admin_phone_button"], "contact"),
        ]])
        key = str(self.video_path)
        async def send(use_cache: bool):
            return await bot.send_video(
                chat_id=chat_id,
                video=self._file_ids[key] if use_cache and key in self._file_ids else FSInputFile(self.video_path),
                caption=texts["coaching_caption"],
                width=content.COACHING_VIDEO_WIDTH,
                height=content.COACHING_VIDEO_HEIGHT,
                duration=content.COACHING_VIDEO_DURATION,
                supports_streaming=True,
                reply_markup=keyboard,
            )
        try:
            try:
                message = await send(use_cache=True)
            except TelegramBadRequest:
                if key not in self._file_ids:
                    raise
                self._file_ids.pop(key)
                message = await send(use_cache=False)
            if message.video:
                self._file_ids[key] = message.video.file_id
        except Exception as exc:
            logger.exception("Showcase video failed: %s", type(exc).__name__)
            await bot.send_message(chat_id=chat_id, text=texts["media_unavailable"])

    async def send_about(self, bot: Bot, chat_id: int, texts: dict) -> None:
        photos = content.about_photos(self.about_dir)[:content.ALBUM_MAX]
        if photos and not await self._send_album(bot, chat_id, photos, texts):
            return
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            self._button(texts["nav_results"], "rev:1"),
            self._button(texts["nav_coaching"], "video"),
        ]])
        await bot.send_message(chat_id=chat_id, text=texts["about_text"], reply_markup=keyboard)

    async def send_contact(self, bot: Bot, chat_id: int, texts: dict) -> None:
        await bot.send_contact(chat_id=chat_id, phone_number=content.ADMIN_PHONE,
                               first_name=content.ADMIN_CONTACT_NAME)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=texts["write_admin_button"], url=content.ADMIN_TELEGRAM_URL)
        ]])
        await bot.send_message(chat_id=chat_id, text=texts["contact_text"], reply_markup=keyboard)

    async def handle_callback(self, callback: CallbackQuery, texts: dict) -> None:
        try:
            data = callback.data or ""
            if not data.startswith(content.SHOW_PREFIX) or callback.message is None:
                return
            destination = data[len(content.SHOW_PREFIX):]
            bot = callback.bot
            chat_id = callback.message.chat.id
            if destination.startswith("rev:"):
                await self.send_results(bot, chat_id, destination[4:], texts)
            elif destination == "video":
                await self.send_video(bot, chat_id, texts)
            elif destination == "about":
                await self.send_about(bot, chat_id, texts)
            elif destination == "contact":
                await self.send_contact(bot, chat_id, texts)
        finally:
            await callback.answer()
