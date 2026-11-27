"""Tests for admin panel wiring without opening a server or calling Telegram."""

import asyncio
import logging
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, call

import pytest
from aiogram.types import Chat, MenuButtonCommands

import admin_panel
import bot as bot_module
import panel_server
from bot import BotHandlers, Settings


ADMIN_CHAT_ID = 101
ADMIN_GROUP_ID = -100123
VIEWER_ID = 111
OTHER_VIEWER_ID = 222
WEBAPP_URL = "https://example.org/app"
PANEL_URL = "https://panel.example.org/admin/"


@pytest.fixture
def settings(tmp_db_path):
    return Settings(
        "unused", ADMIN_CHAT_ID, WEBAPP_URL, tmp_db_path,
        viewer_ids=frozenset({VIEWER_ID, OTHER_VIEWER_ID}), panel_url=PANEL_URL,
    )


@pytest.fixture
def panel_mocks(monkeypatch):
    create_app = Mock()
    start_panel = AsyncMock()
    monkeypatch.setattr(panel_server, "create_app", create_app)
    monkeypatch.setattr(panel_server, "start_panel", start_panel)
    return create_app, start_panel


async def test_start_panel_skips_empty_url(settings, panel_mocks):
    create_app, start_panel = panel_mocks
    result = await bot_module._start_panel_safely(replace(settings, panel_url=""), Mock(), Mock())
    assert result is None
    create_app.assert_not_called()
    start_panel.assert_not_awaited()


async def test_start_panel_returns_runner(settings, panel_mocks):
    create_app, start_panel = panel_mocks
    storage, bot = Mock(), Mock()
    result = await bot_module._start_panel_safely(settings, storage, bot)
    create_app.assert_called_once_with(settings, storage, bot)
    start_panel.assert_awaited_once_with(create_app.return_value)
    assert result is start_panel.return_value


async def test_start_panel_logs_only_oserror_type(settings, panel_mocks, caplog):
    _, start_panel = panel_mocks
    start_panel.side_effect = OSError("Address and port details")
    result = await bot_module._start_panel_safely(settings, Mock(), Mock())
    assert result is None
    start_panel.assert_awaited_once()
    assert caplog.record_tuples == [
        (bot_module.__name__, logging.ERROR, "Could not start admin panel: OSError"),
    ]
    assert caplog.records[0].exc_info is None


@pytest.mark.parametrize("port_busy", [False, True])
async def test_main_polls_after_panel_start_and_cleans_up(settings, panel_mocks, monkeypatch, port_busy):
    create_app, start_panel = panel_mocks
    runner = SimpleNamespace(cleanup=AsyncMock())
    start_panel.return_value = runner
    if port_busy:
        start_panel.side_effect = OSError("Port busy")
    storage = SimpleNamespace(init=AsyncMock(), close=AsyncMock())
    bot = SimpleNamespace(session=SimpleNamespace(close=AsyncMock()))
    poll = AsyncMock()
    dispatcher = SimpleNamespace(start_polling=poll, resolve_used_update_types=lambda: [])
    monkeypatch.setattr(bot_module, "load_settings", lambda: settings)
    monkeypatch.setattr(bot_module, "Storage", lambda path: storage)
    monkeypatch.setattr(bot_module, "Bot", lambda token: bot)
    monkeypatch.setattr(bot_module, "setup_commands", AsyncMock())
    monkeypatch.setattr(bot_module, "build_dispatcher", lambda handlers: dispatcher)
    lifecycle = Mock()
    lifecycle.attach_mock(start_panel, "start_panel")
    lifecycle.attach_mock(poll, "poll")
    lifecycle.attach_mock(runner.cleanup, "cleanup")
    lifecycle.attach_mock(storage.close, "close_storage")
    lifecycle.attach_mock(bot.session.close, "close_session")

    assert await bot_module.main() == 0

    expected_calls = [
        call.start_panel(create_app.return_value),
        call.poll(bot, allowed_updates=[], close_bot_session=False),
    ]
    if not port_busy:
        expected_calls.append(call.cleanup())
        runner.cleanup.assert_awaited_once_with()
    expected_calls.append(call.close_storage())
    expected_calls.append(call.close_session())
    assert lifecycle.mock_calls == expected_calls
    poll.assert_awaited_once()
    storage.close.assert_awaited_once_with()
    bot.session.close.assert_awaited_once_with()


@pytest.mark.parametrize("runner_present, failing_stage", [
    (True, None),
    (True, "runner"),
    (True, "storage"),
    (False, None),
])
async def test_shutdown_closes_resources_in_order(runner_present, failing_stage):
    lifecycle = Mock()
    runner = SimpleNamespace(cleanup=AsyncMock()) if runner_present else None
    storage = SimpleNamespace(close=AsyncMock())
    bot = SimpleNamespace(session=SimpleNamespace(close=AsyncMock()))
    if runner is not None:
        lifecycle.attach_mock(runner.cleanup, "cleanup")
    lifecycle.attach_mock(storage.close, "close_storage")
    lifecycle.attach_mock(bot.session.close, "close_session")

    async def retry_forever():
        try:
            await asyncio.Event().wait()
        finally:
            lifecycle.retry_cancelled()

    retry_task = asyncio.create_task(retry_forever())
    await asyncio.sleep(0)
    failure = RuntimeError(f"{failing_stage} cleanup failed") if failing_stage else None
    if failing_stage == "runner":
        runner.cleanup.side_effect = failure
    elif failing_stage == "storage":
        storage.close.side_effect = failure

    if failure is None:
        await bot_module._shutdown(retry_task, runner, storage, bot)
    else:
        with pytest.raises(RuntimeError, match=str(failure)):
            await bot_module._shutdown(retry_task, runner, storage, bot)

    expected_calls = [call.retry_cancelled()]
    if runner is not None:
        expected_calls.append(call.cleanup())
    expected_calls.extend([call.close_storage(), call.close_session()])
    assert lifecycle.mock_calls == expected_calls
    assert retry_task.cancelled()


@pytest.mark.parametrize("chat_id, chat_type, panel_url, expected_urls", [
    (VIEWER_ID, "private", PANEL_URL, [PANEL_URL]),
    (ADMIN_GROUP_ID, "group", PANEL_URL, []),
    (VIEWER_ID, "private", "", []),
])
async def test_admin_overview_keyboard_only_shows_mini_app_in_private_chat(
    settings, monkeypatch, chat_id, chat_type, panel_url, expected_urls,
):
    handlers = BotHandlers(replace(settings, admin_chat_id=ADMIN_GROUP_ID, panel_url=panel_url), Mock())
    monkeypatch.setattr(handlers, "_admin_overview", AsyncMock(return_value="Overview"))
    message = SimpleNamespace(
        chat=Chat(id=chat_id, type=chat_type), answer=AsyncMock(), edit_text=AsyncMock(),
    )
    callback = SimpleNamespace(data=admin_panel.CB_OVERVIEW, message=message, answer=AsyncMock())

    await handlers.admin_menu(message)
    await handlers.admin_callback(callback)

    for send_overview in (message.answer, message.edit_text):
        send_overview.assert_awaited_once()
        keyboard = send_overview.await_args.kwargs["reply_markup"]
        assert [
            button.web_app.url for row in keyboard.inline_keyboard for button in row if button.web_app
        ] == expected_urls


@pytest.mark.parametrize("admin_chat_id, panel_url, expected_ids", [
    (ADMIN_CHAT_ID, PANEL_URL, {ADMIN_CHAT_ID, VIEWER_ID, OTHER_VIEWER_ID}),
    (ADMIN_GROUP_ID, PANEL_URL, {VIEWER_ID, OTHER_VIEWER_ID}),
    (ADMIN_CHAT_ID, "", {ADMIN_CHAT_ID, VIEWER_ID, OTHER_VIEWER_ID}),
])
async def test_setup_commands_sets_commands_menu_for_allowed_chats(settings, admin_chat_id, panel_url, expected_ids):
    bot = SimpleNamespace(set_my_commands=AsyncMock(), set_chat_menu_button=AsyncMock())
    await bot_module.setup_commands(bot, replace(settings, admin_chat_id=admin_chat_id, panel_url=panel_url))

    button = MenuButtonCommands()
    assert bot.set_chat_menu_button.await_count == len(expected_ids)
    bot.set_chat_menu_button.assert_has_awaits(
        [call(chat_id=chat_id, menu_button=button) for chat_id in expected_ids], any_order=True,
    )


async def test_setup_commands_continues_after_menu_button_failure(settings, caplog):
    error = RuntimeError("Private chat details")
    bot = SimpleNamespace(
        set_my_commands=AsyncMock(), set_chat_menu_button=AsyncMock(side_effect=[error, None, None]),
    )

    await bot_module.setup_commands(bot, settings)

    assert bot.set_chat_menu_button.await_count == 3
    assert {args.kwargs["chat_id"] for args in bot.set_chat_menu_button.await_args_list} == {
        ADMIN_CHAT_ID, VIEWER_ID, OTHER_VIEWER_ID,
    }
    assert caplog.record_tuples == [
        (bot_module.__name__, logging.ERROR, "Could not set chat menu button: RuntimeError"),
    ]
    assert caplog.records[0].exc_info is None
