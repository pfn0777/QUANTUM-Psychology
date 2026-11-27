"""Showcase behavior with local media and a recording Telegram bot."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import SendMediaGroup, SendVideo
from aiogram.types import FSInputFile

import content
from showcase import Showcase


JPEG = bytes.fromhex("ffd8ffd9")
TEXT_KEYS = (
    "results_intro", "results_footer", "results_more_button", "results_empty",
    "media_unavailable", "coaching_caption", "nav_results", "nav_coaching",
    "admin_phone_button", "about_text", "contact_text", "write_admin_button",
)
TEXTS = {key: key + " {page}/{total}" if key in {"results_footer", "results_more_button"} else key
         for key in TEXT_KEYS}


class FakeBot:
    def __init__(self):
        self.calls = []
        self.album_errors = []
        self.video_errors = []
        self.next_id = 0

    async def send_message(self, **kwargs):
        self.calls.append(("message", kwargs))

    async def send_media_group(self, **kwargs):
        self.calls.append(("album", kwargs))
        if self.album_errors:
            raise self.album_errors.pop(0)
        messages = []
        for _ in kwargs["media"]:
            self.next_id += 1
            messages.append(SimpleNamespace(photo=[SimpleNamespace(file_id=f"photo-{self.next_id}")]))
        return messages

    async def send_video(self, **kwargs):
        self.calls.append(("video", kwargs))
        if self.video_errors:
            raise self.video_errors.pop(0)
        self.next_id += 1
        return SimpleNamespace(video=SimpleNamespace(file_id=f"video-{self.next_id}"))

    async def send_contact(self, **kwargs):
        self.calls.append(("contact", kwargs))


def photos(directory: Path, count: int) -> None:
    directory.mkdir(exist_ok=True)
    for number in range(count):
        (directory / f"{number:02}.jpg").write_bytes(JPEG)


def buttons(call):
    return call[1]["reply_markup"].inline_keyboard


def bad_request(method):
    return TelegramBadRequest(method, "Bad Request: invalid file id")


@pytest.mark.asyncio
async def test_results_pages_and_invalid_pages(tmp_path):
    photos(tmp_path, content.ALBUM_MAX + 1)
    showcase = Showcase(reviews_dir=tmp_path)
    bot = FakeBot()
    await showcase.send_results(bot, 1, 1, TEXTS)
    assert [name for name, _ in bot.calls] == ["message", "album", "message"]
    assert bot.calls[0][1]["text"] == TEXTS["results_intro"]
    assert len(bot.calls[1][1]["media"]) == content.ALBUM_MAX
    assert buttons(bot.calls[-1])[0][0].callback_data == "show:rev:2"
    assert [button.callback_data for button in buttons(bot.calls[-1])[1]] == ["show:video", "show:contact"]
    bot.calls.clear()
    await showcase.send_results(bot, 1, 2, TEXTS)
    assert [name for name, _ in bot.calls] == ["album", "message"]
    assert len(buttons(bot.calls[-1])) == 1
    for invalid in ("abc", "99", None):
        bot.calls.clear()
        await showcase.send_results(bot, 1, invalid, TEXTS)
        assert bot.calls[0][1]["text"] == TEXTS["results_intro"]


@pytest.mark.asyncio
async def test_empty_results(tmp_path, caplog):
    bot = FakeBot()
    await Showcase(reviews_dir=tmp_path).send_results(bot, 1, 1, TEXTS)
    assert bot.calls[0][1]["text"] == TEXTS["results_empty"]
    assert "no photos" in caplog.text


@pytest.mark.asyncio
async def test_album_cache_retry_and_failure(tmp_path):
    photos(tmp_path, 2)
    showcase = Showcase(reviews_dir=tmp_path)
    bot = FakeBot()
    await showcase.send_results(bot, 1, 1, TEXTS)
    bot.calls.clear()
    await showcase.send_results(bot, 1, 1, TEXTS)
    assert all(isinstance(item.media, str) for item in bot.calls[1][1]["media"])
    bot.calls.clear()
    bot.album_errors = [bad_request(SendMediaGroup(chat_id=1, media=[]))]
    await showcase.send_results(bot, 1, 1, TEXTS)
    albums = [call for call in bot.calls if call[0] == "album"]
    assert len(albums) == 2
    assert all(isinstance(item.media, FSInputFile) for item in albums[-1][1]["media"])
    assert len(showcase._file_ids) == 2
    bot.calls.clear()
    bot.album_errors = [bad_request(SendMediaGroup(chat_id=1, media=[])),
                        bad_request(SendMediaGroup(chat_id=1, media=[]))]
    await showcase.send_results(bot, 1, 1, TEXTS)
    assert len([call for call in bot.calls if call[0] == "album"]) == 2
    assert bot.calls[-1][1]["text"] == TEXTS["media_unavailable"]


@pytest.mark.asyncio
async def test_video_missing_cache_and_retry(tmp_path):
    path = tmp_path / "video.mp4"
    showcase = Showcase(video_path=path)
    bot = FakeBot()
    await showcase.send_video(bot, 1, TEXTS)
    assert bot.calls[-1][1]["text"] == TEXTS["media_unavailable"]
    path.write_bytes(b"video")
    bot.calls.clear()
    await showcase.send_video(bot, 1, TEXTS)
    assert isinstance(bot.calls[-1][1]["video"], FSInputFile)
    assert bot.calls[-1][1]["supports_streaming"] is True
    bot.calls.clear()
    await showcase.send_video(bot, 1, TEXTS)
    assert bot.calls[-1][1]["video"] == "video-1"
    bot.calls.clear()
    bot.video_errors = [bad_request(SendVideo(chat_id=1, video="bad"))]
    await showcase.send_video(bot, 1, TEXTS)
    assert isinstance(bot.calls[-1][1]["video"], FSInputFile)
    bot.calls.clear()
    bot.video_errors = [bad_request(SendVideo(chat_id=1, video="bad")),
                        bad_request(SendVideo(chat_id=1, video="bad"))]
    await showcase.send_video(bot, 1, TEXTS)
    assert bot.calls[-1][1]["text"] == TEXTS["media_unavailable"]


@pytest.mark.asyncio
async def test_about_and_contact(tmp_path):
    photos(tmp_path, 2)
    bot = FakeBot()
    showcase = Showcase(about_dir=tmp_path)
    await showcase.send_about(bot, 1, TEXTS)
    assert [name for name, _ in bot.calls] == ["album", "message"]
    assert [button.callback_data for button in buttons(bot.calls[-1])[0]] == ["show:rev:1", "show:video"]
    bot.calls.clear()
    await showcase.send_contact(bot, 1, TEXTS)
    assert bot.calls[0][1]["phone_number"] == content.ADMIN_PHONE
    assert buttons(bot.calls[-1])[0][0].url == content.ADMIN_TELEGRAM_URL
    assert all(not button.callback_data or not button.callback_data.startswith("adm:")
               for call in bot.calls if "reply_markup" in call[1]
               for row in buttons(call) for button in row)


@pytest.mark.asyncio
async def test_callback_always_answered(tmp_path):
    showcase = Showcase(reviews_dir=tmp_path)
    bot = FakeBot()
    for data in ("show:rev:1", "show:video", "show:about", "show:contact", "show:unknown", "adm:other"):
        callback = SimpleNamespace(data=data, bot=bot, message=SimpleNamespace(chat=SimpleNamespace(id=1)),
                                   answer=AsyncMock())
        await showcase.handle_callback(callback, TEXTS)
        callback.answer.assert_awaited_once()
    callback = SimpleNamespace(data="show:contact", bot=bot,
                               message=SimpleNamespace(chat=SimpleNamespace(id=1)), answer=AsyncMock())
    bot.send_contact = AsyncMock(side_effect=RuntimeError("send failed"))
    with pytest.raises(RuntimeError, match="send failed"):
        await showcase.handle_callback(callback, TEXTS)
    callback.answer.assert_awaited_once()
