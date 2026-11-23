"""Serve the admin Mini App and its Telegram-authenticated API."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from aiogram.exceptions import ClientDecodeError, TelegramAPIError
from aiogram.types import BufferedInputFile
from aiohttp import ClientError, HttpVersion11, hdrs, web
from aiohttp.http_exceptions import HttpProcessingError
from aiohttp.streams import StreamReader
from aiohttp.web_protocol import RequestHandler, RequestPayloadError, _ErrInfo
from aiohttp.web_urldispatcher import MatchInfoError
from multidict import CIMultiDict

import dashboard
import webapp_auth

if TYPE_CHECKING:
    from aiogram import Bot

    from bot import Settings
    from storage import Storage


_REPO_ROOT = Path(__file__).resolve().parent.parent
ADMIN_WEBAPP_DIR = _REPO_ROOT / "bot" / "admin_webapp"
WEBAPP_FONTS_DIR = _REPO_ROOT / "webapp" / "fonts"
PANEL_HOST = "127.0.0.1"
EXPORT_COOLDOWN_SECONDS = 10
ALLOWED_STATIC_SUFFIXES = {".html", ".js", ".css"}
_EXPORT_COOLDOWN = timedelta(seconds=EXPORT_COOLDOWN_SECONDS)
_PANEL_PORT = web.AppKey("panel_port", int)
_STATIC_TYPES = {
    ".html": "text/html",
    ".js": "text/javascript",
    ".css": "text/css",
}
_SECURITY_HEADERS = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self' https://telegram.org; "
        "style-src 'self'; font-src 'self'; img-src 'self' data:; connect-src 'self'; "
        "base-uri 'none'; object-src 'none'; frame-ancestors https://web.telegram.org"
    ),
}
_logger = logging.getLogger(__name__)


class _APIError(Exception):
    def __init__(self, status: HTTPStatus, code: str) -> None:
        super().__init__(code)
        self.status = status
        self.code = code


@web.middleware
async def _handle_errors(
    request: web.Request, handler: Callable[[web.Request], Awaitable[web.StreamResponse]]
) -> web.StreamResponse:
    try:
        # aiohttp only calls the expect handler when the first value is truthy.
        if request.headers.get(hdrs.EXPECT) == "":
            return await _reject_expect(request)
        if ".." in request.path.replace("\\", "/").split("/"):
            raise web.HTTPNotFound()
        response = await handler(request)
        if response.status >= HTTPStatus.INTERNAL_SERVER_ERROR:
            return _internal_error()
        return response
    except _APIError as exc:
        return web.json_response({"error": exc.code}, status=exc.status)
    except (RequestPayloadError, HttpProcessingError) as exc:
        _logger.warning("%s", type(exc).__name__)
        return _error_and_close(HTTPStatus.BAD_REQUEST)
    except Exception as exc:
        if isinstance(exc, web.HTTPException) and exc.status < HTTPStatus.INTERNAL_SERVER_ERROR:
            raise
        _logger.error("%s", type(exc).__name__)
        return _internal_error()


def _internal_error() -> web.Response:
    return web.json_response({"error": "internal"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)


def _error_and_close(status: HTTPStatus, code: str = "bad_request") -> web.Response:
    response = web.json_response({"error": code}, status=status)
    response.force_close()
    return response


async def _reject_expect(_request: web.Request) -> web.Response:
    return _error_and_close(HTTPStatus.EXPECTATION_FAILED)


class _ExpectFallback(web.PlainResource):
    """Reject Expect before aiohttp can use a 404 or 405 route's default handler."""

    def __init__(self) -> None:
        super().__init__("/")
        self._reject_route = self.add_route(hdrs.METH_ANY, _reject_expect, expect_handler=_reject_expect)

    async def resolve(self, request: web.Request) -> tuple[web.UrlMappingMatchInfo | None, set[str]]:
        if hdrs.EXPECT in request.headers:
            return web.UrlMappingMatchInfo({}, self._reject_route), set()
        return None, set()


async def _set_security_headers(request: web.Request, response: web.StreamResponse) -> None:
    response.headers.update(_SECURITY_HEADERS)


def _authorized_user(
    request: web.Request, token: str, allowed_ids: set[int], now: datetime
) -> int:
    values = request.headers.getall("Authorization", ())
    if len(values) != 1:
        raise _APIError(HTTPStatus.UNAUTHORIZED, "unauthorized")
    scheme, _, init_data = values[0].partition(" ")
    if scheme.lower() != "tma" or not init_data or any(char.isspace() for char in init_data):
        raise _APIError(HTTPStatus.UNAUTHORIZED, "unauthorized")

    try:
        user = webapp_auth.validate_init_data(init_data, token, now)
    except webapp_auth.InitDataError as exc:
        raise _APIError(HTTPStatus.UNAUTHORIZED, exc.code) from None
    user_id = user["id"]
    if user_id not in allowed_ids:
        raise _APIError(HTTPStatus.FORBIDDEN, "forbidden")
    return user_id


def _read_asset(directory: Path, filename: str) -> bytes:
    if any(char in filename for char in '/\\:\x00<>"|?*'):
        raise web.HTTPNotFound()
    path = directory / filename
    if path.is_symlink():
        raise web.HTTPNotFound()
    resolved = path.resolve()
    if resolved.parent != directory or not resolved.is_file():
        raise web.HTTPNotFound()
    try:
        return resolved.read_bytes()
    except (FileNotFoundError, IsADirectoryError):
        raise web.HTTPNotFound() from None


async def _asset_response(directory: Path, filename: str, content_type: str) -> web.Response:
    body = await asyncio.to_thread(_read_asset, directory, filename)
    return web.Response(body=body, content_type=content_type)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_app(
    settings: Settings,
    storage: Storage,
    bot: Bot,
    *,
    clock: Callable[[], datetime] | None = None,
    static_dir: Path = ADMIN_WEBAPP_DIR,
    fonts_dir: Path = WEBAPP_FONTS_DIR,
) -> web.Application:
    get_time = clock if clock is not None else _utc_now
    static_dir = static_dir.resolve()
    fonts_dir = fonts_dir.resolve()
    allowed_ids = set(settings.viewer_ids)
    if settings.admin_chat_id > 0:
        allowed_ids.add(settings.admin_chat_id)
    last_export: dict[int, datetime] = {}

    async def redirect_to_index(request: web.Request) -> web.Response:
        raise web.HTTPPermanentRedirect("/admin/")

    async def static_asset(request: web.Request) -> web.Response:
        filename = request.match_info.get("name", "index.html")
        suffix = Path(filename).suffix
        if suffix not in ALLOWED_STATIC_SUFFIXES:
            raise web.HTTPNotFound()
        return await _asset_response(static_dir, filename, _STATIC_TYPES[suffix])

    async def font_asset(request: web.Request) -> web.Response:
        filename = request.match_info["name"]
        if Path(filename).suffix != ".woff2":
            raise web.HTTPNotFound()
        return await _asset_response(fonts_dir, filename, "font/woff2")

    async def get_dashboard(request: web.Request) -> web.Response:
        now = get_time().astimezone(timezone.utc)
        _authorized_user(request, settings.token, allowed_ids, now)
        since = now - timedelta(days=dashboard.DAILY_DAYS)
        payload = dashboard.build_dashboard(
            total_users=await storage.count_users(),
            user_rows=await storage.user_rows_since(since),
            lead_user_count=await storage.count_lead_users(),
            lead_rows=await storage.rows_since(since),
            undelivered=await storage.count_undelivered(),
            recent_leads=await storage.recent_leads(dashboard.RECENT_LIMIT),
            recent_users=await storage.recent_users(dashboard.RECENT_LIMIT),
            now_utc=now,
        )
        return web.json_response(payload)

    async def expect_export(request: web.Request) -> web.Response | None:
        expectations = request.headers.getall(hdrs.EXPECT)
        if request.version != HttpVersion11 or len(expectations) != 1 or expectations[0].lower() != "100-continue":
            return await _reject_expect(request)

        try:
            now = get_time().astimezone(timezone.utc)
            _authorized_user(request, settings.token, allowed_ids, now)
            length = request.content_length
            limit = request.client_max_size
            # aiohttp 3.10 read() rejects a body that reaches the configured limit.
            if length is not None and limit and length >= limit:
                raise _APIError(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "bad_request")
        except _APIError as exc:
            return _error_and_close(exc.status, exc.code)

        status = HTTPStatus.CONTINUE
        await request.writer.write_headers(
            f"HTTP/1.1 {status.value} {status.phrase}", CIMultiDict(_SECURITY_HEADERS)
        )
        # aiohttp 3.12+ buffers headers until send_headers() is called.
        send_headers = getattr(request.writer, "send_headers", None)
        if send_headers is not None:
            send_headers()
        # aiohttp uses this counter to check whether the final response has started.
        request.writer.output_size = 0
        return None

    async def export_csv(request: web.Request) -> web.Response:
        now = get_time().astimezone(timezone.utc)
        user_id = _authorized_user(request, settings.token, allowed_ids, now)
        try:
            body = json.loads(await request.read())
        except (ValueError, RecursionError, web.HTTPRequestEntityTooLarge):
            raise _APIError(HTTPStatus.BAD_REQUEST, "bad_request") from None
        kind = body.get("kind") if isinstance(body, dict) else None
        if kind not in ("leads", "users"):
            raise _APIError(HTTPStatus.BAD_REQUEST, "bad_request")

        now = get_time().astimezone(timezone.utc)
        previous = last_export.get(user_id)
        if previous is not None and now - previous < _EXPORT_COOLDOWN:
            raise _APIError(HTTPStatus.TOO_MANY_REQUESTS, "too_many")
        # Reserve the attempt before I/O so concurrent requests share the same cooldown.
        last_export[user_id] = now

        data = await (storage.export_csv() if kind == "leads" else storage.export_users_csv())
        document = BufferedInputFile(data, filename=f"{kind}_{now:%Y%m%d}.csv")
        try:
            await bot.send_document(chat_id=user_id, document=document)
        except (TelegramAPIError, ClientError, ClientDecodeError) as exc:
            _logger.warning("%s", type(exc).__name__)
            raise _APIError(HTTPStatus.BAD_GATEWAY, "send_failed") from None
        return web.json_response({"ok": True})

    app = web.Application(middlewares=[_handle_errors])
    app.on_response_prepare.append(_set_security_headers)
    app[_PANEL_PORT] = settings.panel_port
    app.router.add_get("/admin", redirect_to_index, expect_handler=_reject_expect)
    app.router.add_get("/admin/", static_asset, expect_handler=_reject_expect)
    app.router.add_get("/admin/fonts/{name}", font_asset, expect_handler=_reject_expect)
    app.router.add_get("/admin/api/dashboard", get_dashboard, expect_handler=_reject_expect)
    app.router.add_post("/admin/api/export", export_csv, expect_handler=expect_export)
    app.router.add_get("/admin/{name}", static_asset, expect_handler=_reject_expect)
    app.router.register_resource(_ExpectFallback())
    return app


class _PanelRequestHandler(RequestHandler):
    _last_payload: StreamReader | None = None

    def data_received(self, data: bytes) -> None:
        request_count = self._request_count
        super().data_received(data)
        if self._request_count == request_count:
            return

        message, payload = self._messages[-1]
        if isinstance(message, _ErrInfo):
            # The C parser drops its payload on a framing error. aiohttp queues
            # the error behind the request that is still waiting for that payload.
            if self._last_payload is not None and not self._last_payload.is_eof():
                self._last_payload.set_exception(message.exc)
                self._messages.pop()
            self._last_payload = None
        else:
            self._last_payload = payload if not payload.is_eof() else None

    def handle_error(
        self,
        request: web.BaseRequest,
        status: int = HTTPStatus.INTERNAL_SERVER_ERROR,
        exc: BaseException | None = None,
        message: str | None = None,
    ) -> web.StreamResponse:
        # aiohttp's parser supplies the raw request fragment as the error message.
        if status == HTTPStatus.BAD_REQUEST:
            if exc is not None:
                _logger.warning("%s", type(exc).__name__)
            return _error_and_close(HTTPStatus.BAD_REQUEST)
        return super().handle_error(request, status, exc, message)


class _PanelServer(web.Server):
    def __call__(self) -> RequestHandler:
        return _PanelRequestHandler(self, loop=self._loop, **self._kwargs)


class _PanelRunner(web.AppRunner):
    async def _make_server(self) -> web.Server:
        server = await super()._make_server()
        make_request = server.request_factory
        # aiohttp 3.10 skips routing for parser errors. Seed the application
        # context so these responses still dispatch on_response_prepare.
        unrouted = MatchInfoError(web.HTTPBadRequest())
        unrouted.add_app(self.app)
        unrouted.freeze()

        def make_panel_request(*args: Any) -> web.Request:
            request = cast(web.Request, make_request(*args))
            request._match_info = unrouted
            return request

        return _PanelServer(
            server.request_handler,
            request_factory=make_panel_request,
            handler_cancellation=server.handler_cancellation,
            **server._kwargs,
        )


async def start_panel(
    app: web.Application, *, host: str = PANEL_HOST, port: int | None = None
) -> web.AppRunner:
    if host != PANEL_HOST:
        raise ValueError(f"Panel host must be {PANEL_HOST}")
    # Parser logs can contain raw request headers and have no application-level filtering.
    protocol_logger = logging.Logger(f"{__name__}.protocol")  # noqa: LOG001
    protocol_logger.addHandler(logging.NullHandler())
    # Clients receiving an early rejection may never send the advertised body.
    runner = _PanelRunner(app, access_log=None, logger=protocol_logger, lingering_time=0)
    try:
        await runner.setup()
        await web.TCPSite(runner, PANEL_HOST, app[_PANEL_PORT] if port is None else port).start()
    except BaseException:
        await runner.cleanup()
        raise
    return runner
