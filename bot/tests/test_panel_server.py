"""HTTP contract for the admin Mini App using local servers and signed init data."""

import asyncio
import hmac
import json
import logging
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.client import parse_headers
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, create_autospec
from urllib.parse import urlencode

import pytest
from aiogram.exceptions import ClientDecodeError, TelegramAPIError
from aiogram.methods import SendDocument
from aiogram.types import BufferedInputFile
from aiohttp import ClientError, ClientResponse, web, web_protocol
from aiohttp.http_parser import HttpRequestParserC, HttpRequestParserPy
from aiohttp.test_utils import TestClient, TestServer
from yarl import URL

from dashboard import RECENT_LIMIT
from panel_server import EXPORT_COOLDOWN_SECONDS, create_app, start_panel
from storage import Storage
from webapp_auth import INIT_DATA_MAX_AGE

TOKEN = "test-signing-key"
NOW = datetime(2026, 11, 22, 19, tzinfo=timezone.utc)
VIEWER_ID = 1001
ADMIN_ID = 1002
FOREIGN_ID = 1003
GROUP_ID = -1002345
DASHBOARD_URL = "/admin/api/dashboard"
EXPORT_URL = "/admin/api/export"
RAW_HTTP_TIMEOUT = 5
STATIC_ASSETS = {
    "index.html": (b"<html>Panel</html>", "text/html"),
    "app.js": (b"export const panel = true;", "text/javascript"),
    "format.js": (b"export const format = String;", "text/javascript"),
    "styles.css": (b"body { color: black; }", "text/css"),
    "extra.js": (b"export const extra = true;", "text/javascript"),
}
FONT_BYTES = b"wOF2-test-data"


def auth_headers(
    user_id: int = VIEWER_ID, *, auth_date: datetime = NOW, token: str = TOKEN
) -> dict[str, str]:
    fields = {
        "auth_date": str(int(auth_date.timestamp())),
        "query_id": "test-query",
        "user": json.dumps({"id": user_id, "first_name": "Fake User"}),
    }
    check_string = "\n".join(f"{key}={fields[key]}" for key in sorted(fields))
    signing_key = hmac.digest(b"WebAppData", token.encode(), "sha256")
    fields["hash"] = hmac.digest(signing_key, check_string.encode(), "sha256").hex()
    return {"Authorization": f"tma {urlencode(fields)}"}


def assert_security_headers(headers: Mapping[str, str]) -> None:
    assert headers["Cache-Control"] == "no-store"
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["Referrer-Policy"] == "no-referrer"
    directives = headers["Content-Security-Policy"].split("; ")
    assert "default-src 'self'" in directives
    assert "script-src 'self' https://telegram.org" in directives
    assert "frame-ancestors https://web.telegram.org" in directives


async def assert_error(response: ClientResponse, status: int, code: str) -> None:
    assert response.status == status
    assert await response.json() == {"error": code}
    assert_security_headers(response.headers)


@dataclass
class FixedClock:
    now: datetime = NOW

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock()


@pytest.fixture
def settings(request: pytest.FixtureRequest) -> SimpleNamespace:
    return SimpleNamespace(
        token=TOKEN,
        admin_chat_id=getattr(request, "param", ADMIN_ID),
        viewer_ids=frozenset({VIEWER_ID}),
        panel_port=0,
    )


@pytest.fixture
def storage() -> Mock:
    fake = create_autospec(Storage, instance=True)
    fake.count_users.return_value = 7
    fake.user_rows_since.return_value = []
    fake.count_lead_users.return_value = 3
    fake.rows_since.return_value = []
    fake.count_undelivered.return_value = 2
    fake.recent_leads.return_value = []
    fake.recent_users.return_value = []
    fake.export_csv.return_value = b"lead,csv\r\n"
    fake.export_users_csv.return_value = b"user,csv\r\n"
    return fake


@pytest.fixture
def bot() -> SimpleNamespace:
    return SimpleNamespace(send_document=AsyncMock())


@pytest.fixture
def app(
    settings: SimpleNamespace, storage: Mock, bot: SimpleNamespace, clock: FixedClock, tmp_path: Path
) -> web.Application:
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    for filename, (content, _) in STATIC_ASSETS.items():
        (static_dir / filename).write_bytes(content)
    (static_dir / "tests").mkdir()
    (static_dir / "tests" / "preview.html").write_bytes(b"private test fixture")
    (static_dir / "fixture.json").write_bytes(b'{"asset": true}')
    (static_dir / "assets").mkdir()
    (static_dir / "assets" / "sample.js").write_bytes(b"nested asset")
    (static_dir / "directory.js").mkdir()
    (tmp_path / "outside.js").write_bytes(b"outside the static directory")

    fonts_dir = tmp_path / "fonts"
    fonts_dir.mkdir()
    (fonts_dir / "panel.woff2").write_bytes(FONT_BYTES)
    (fonts_dir / "panel.woff").write_bytes(b"other font")
    (fonts_dir / "notes.txt").write_bytes(b"non-font")

    return create_app(settings, storage, bot, clock=clock, static_dir=static_dir, fonts_dir=fonts_dir)


@pytest.fixture
async def client(app: web.Application) -> AsyncIterator[TestClient]:
    async with TestClient(TestServer(app), raise_for_status=False) as test_client:
        yield test_client


@asynccontextmanager
async def panel_connection(
    app: web.Application,
) -> AsyncIterator[tuple[asyncio.StreamReader, asyncio.StreamWriter]]:
    runner = await start_panel(app)
    try:
        [(host, port)] = runner.addresses
        async with asyncio.timeout(RAW_HTTP_TIMEOUT):
            reader, writer = await asyncio.open_connection(host, port)
            try:
                yield reader, writer
            finally:
                writer.close()
                await writer.wait_closed()
    finally:
        await runner.cleanup()


async def read_response_head(reader: asyncio.StreamReader) -> tuple[int, dict[str, str]]:
    head = await reader.readuntil(b"\r\n\r\n")
    status_line, raw_headers = head.split(b"\r\n", 1)
    return int(status_line.split()[1]), dict(parse_headers(BytesIO(raw_headers)).items())


@pytest.mark.parametrize(
    ("headers", "code"),
    [
        ({}, "unauthorized"),
        ({"Authorization": "Bearer unsupported"}, "unauthorized"),
        ({"Authorization": "tma"}, "unauthorized"),
        (auth_headers(token="different-test-key"), "unauthorized"),
        (auth_headers(auth_date=NOW - INIT_DATA_MAX_AGE - timedelta(seconds=1)), "expired"),
    ],
)
async def test_dashboard_rejects_invalid_auth(
    client: TestClient, storage: Mock, headers: dict[str, str], code: str
) -> None:
    await assert_error(await client.get(DASHBOARD_URL, headers=headers), 401, code)
    storage.count_users.assert_not_awaited()


async def test_export_checks_auth_before_reading_body(client: TestClient, bot: SimpleNamespace) -> None:
    await assert_error(await client.post(EXPORT_URL, data=b"invalid JSON"), 401, "unauthorized")
    bot.send_document.assert_not_awaited()


async def test_foreign_user_is_forbidden(client: TestClient, storage: Mock) -> None:
    headers = auth_headers(FOREIGN_ID)
    await assert_error(await client.get(DASHBOARD_URL, headers=headers), 403, "forbidden")
    await assert_error(
        await client.post(EXPORT_URL, headers=headers, json={"kind": "leads"}), 403, "forbidden"
    )
    storage.count_users.assert_not_awaited()
    storage.export_csv.assert_not_awaited()


@pytest.mark.parametrize("settings", [GROUP_ID], indirect=True)
async def test_group_admin_chat_id_is_forbidden(client: TestClient, storage: Mock) -> None:
    response = await client.get(DASHBOARD_URL, headers=auth_headers(GROUP_ID))
    await assert_error(response, 403, "forbidden")
    storage.count_users.assert_not_awaited()


@pytest.mark.parametrize("user_id", [VIEWER_ID, ADMIN_ID])
async def test_dashboard_returns_data_for_allowed_users(
    client: TestClient, storage: Mock, user_id: int
) -> None:
    response = await client.get(DASHBOARD_URL, headers=auth_headers(user_id))
    assert response.status == 200
    assert_security_headers(response.headers)
    payload = await response.json()
    assert payload["generated_at"] == NOW.isoformat()
    assert payload["totals"]["users"] == 7
    assert payload["totals"]["lead_users"] == 3
    assert payload["totals"]["undelivered"] == 2
    assert len(payload["daily"]) == 30
    since = NOW - timedelta(days=30)
    storage.count_users.assert_awaited_once_with()
    storage.user_rows_since.assert_awaited_once_with(since)
    storage.count_lead_users.assert_awaited_once_with()
    storage.rows_since.assert_awaited_once_with(since)
    storage.count_undelivered.assert_awaited_once_with()
    storage.recent_leads.assert_awaited_once_with(RECENT_LIMIT)
    storage.recent_users.assert_awaited_once_with(RECENT_LIMIT)


@pytest.mark.parametrize(("kind", "export_method"), [("leads", "export_csv"), ("users", "export_users_csv")])
async def test_export_sends_csv_to_requesting_user(
    client: TestClient, storage: Mock, bot: SimpleNamespace, kind: str, export_method: str
) -> None:
    response = await client.post(EXPORT_URL, headers=auth_headers(), json={"kind": kind})
    assert response.status == 200
    assert await response.json() == {"ok": True}
    assert_security_headers(response.headers)
    export = getattr(storage, export_method)
    export.assert_awaited_once_with()
    bot.send_document.assert_awaited_once()
    sent = bot.send_document.await_args.kwargs
    assert sent["chat_id"] == VIEWER_ID
    document = sent["document"]
    assert isinstance(document, BufferedInputFile)
    assert document.filename == f"{kind}_20261122.csv"
    assert document.data == export.return_value


async def test_export_cooldown_is_per_user_and_expires_at_ten_seconds(
    client: TestClient, clock: FixedClock, bot: SimpleNamespace
) -> None:
    assert EXPORT_COOLDOWN_SECONDS == 10
    viewer = auth_headers()
    assert (await client.post(EXPORT_URL, headers=viewer, json={"kind": "leads"})).status == 200
    clock.now += timedelta(seconds=EXPORT_COOLDOWN_SECONDS - 1)
    await assert_error(
        await client.post(EXPORT_URL, headers=viewer, json={"kind": "users"}), 429, "too_many"
    )
    admin = auth_headers(ADMIN_ID)
    assert (await client.post(EXPORT_URL, headers=admin, json={"kind": "users"})).status == 200
    clock.now += timedelta(seconds=1)
    assert (await client.post(EXPORT_URL, headers=viewer, json={"kind": "users"})).status == 200
    assert [call.kwargs["chat_id"] for call in bot.send_document.await_args_list] == [
        VIEWER_ID, ADMIN_ID, VIEWER_ID
    ]


async def test_cooldown_reserves_slot_before_export_io(client: TestClient, storage: Mock) -> None:
    export_started = asyncio.Event()
    release_export = asyncio.Event()

    async def make_csv() -> bytes:
        export_started.set()
        await release_export.wait()
        return storage.export_csv.return_value

    storage.export_csv.side_effect = make_csv
    headers = auth_headers()
    async with asyncio.TaskGroup() as tasks:
        first_request = tasks.create_task(client.post(EXPORT_URL, headers=headers, json={"kind": "leads"}))
        try:
            await asyncio.wait_for(export_started.wait(), timeout=5)
            second = await client.post(EXPORT_URL, headers=headers, json={"kind": "users"})
            await assert_error(second, 429, "too_many")
            storage.export_users_csv.assert_not_awaited()
        finally:
            release_export.set()
    assert first_request.result().status == 200


@pytest.mark.parametrize("body", [b"{", b"\xff", b"[]", b"{}", b'{"kind":[]}', b'{"kind":"other"}'])
async def test_invalid_export_body_does_not_consume_cooldown(
    client: TestClient, storage: Mock, bot: SimpleNamespace, body: bytes
) -> None:
    headers = auth_headers()
    await assert_error(await client.post(EXPORT_URL, headers=headers, data=body), 400, "bad_request")
    storage.export_csv.assert_not_awaited()
    storage.export_users_csv.assert_not_awaited()
    bot.send_document.assert_not_awaited()
    assert (await client.post(EXPORT_URL, headers=headers, json={"kind": "leads"})).status == 200


async def test_invalid_export_payload_returns_bad_request(
    app: web.Application, storage: Mock, bot: SimpleNamespace, caplog: pytest.LogCaptureFixture
) -> None:
    body = b"invalid gzip data"
    authorization = auth_headers()["Authorization"]
    async with panel_connection(app) as (reader, writer):
        writer.write(
            (
                f"POST {EXPORT_URL} HTTP/1.1\r\nHost: localhost\r\n"
                f"Authorization: {authorization}\r\nContent-Encoding: gzip\r\n"
                f"Content-Length: {len(body)}\r\n\r\n"
            ).encode("ascii") + body
        )
        await writer.drain()
        status, headers = await read_response_head(reader)
        assert status == HTTPStatus.BAD_REQUEST
        assert_security_headers(headers)
        assert json.loads(await reader.read()) == {"error": "bad_request"}
    storage.export_csv.assert_not_awaited()
    bot.send_document.assert_not_awaited()
    assert caplog.messages == ["RequestPayloadError"]
    assert caplog.records[0].exc_info is None


async def test_invalid_chunked_export_payload_returns_bad_request(
    app: web.Application,
    storage: Mock,
    bot: SimpleNamespace,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The Python parser exposes invalid chunk framing to request.read() as a payload error.
    monkeypatch.setattr(web_protocol, "HttpRequestParser", HttpRequestParserPy)
    authorization = auth_headers()["Authorization"]
    async with panel_connection(app) as (reader, writer):
        writer.write(
            (
                f"POST {EXPORT_URL} HTTP/1.1\r\nHost: localhost\r\n"
                f"Authorization: {authorization}\r\nTransfer-Encoding: chunked\r\n\r\n"
            ).encode("ascii") + b"Z\r\n"
        )
        await writer.drain()
        status, headers = await read_response_head(reader)
        assert status == HTTPStatus.BAD_REQUEST
        assert_security_headers(headers)
        assert json.loads(await reader.readexactly(int(headers["Content-Length"]))) == {
            "error": "bad_request"
        }
    storage.export_csv.assert_not_awaited()
    bot.send_document.assert_not_awaited()
    assert caplog.messages == ["RequestPayloadError"]
    assert caplog.records[0].exc_info is None


@pytest.mark.parametrize("use_python_parser", [False, True], ids=["default-c", "python"])
async def test_invalid_chunk_after_body_read_starts_returns_bad_request(
    app: web.Application,
    storage: Mock,
    bot: SimpleNamespace,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    use_python_parser: bool,
) -> None:
    if use_python_parser:
        monkeypatch.setattr(web_protocol, "HttpRequestParser", HttpRequestParserPy)
    else:
        assert web_protocol.HttpRequestParser is HttpRequestParserC

    read_started = asyncio.Event()
    original_read = web.Request.read

    async def notify_read(request: web.Request) -> bytes:
        read_started.set()
        return await original_read(request)

    monkeypatch.setattr(web.Request, "read", notify_read)
    authorization = auth_headers()["Authorization"]
    async with panel_connection(app) as (reader, writer):
        writer.write(
            (
                f"POST {EXPORT_URL} HTTP/1.1\r\nHost: localhost\r\n"
                f"Authorization: {authorization}\r\nTransfer-Encoding: chunked\r\n\r\n"
            ).encode("ascii")
        )
        await writer.drain()
        await read_started.wait()
        writer.write(b"invalid-chunk-test-marker\r\n")
        await writer.drain()

        status, headers = await read_response_head(reader)
        assert status == HTTPStatus.BAD_REQUEST
        assert_security_headers(headers)
        assert json.loads(await reader.read()) == {"error": "bad_request"}

    storage.export_csv.assert_not_awaited()
    bot.send_document.assert_not_awaited()
    assert caplog.messages == ["TransferEncodingError" if use_python_parser else "BadHttpMessage"]
    assert caplog.records[0].exc_info is None


@pytest.mark.parametrize(
    "error",
    [
        TelegramAPIError(SendDocument(chat_id=VIEWER_ID, document="test"), "private API detail"),
        ClientError("private client detail"),
        ClientDecodeError("private decode detail", ValueError("invalid payload"), "private payload"),
    ],
    ids=["api-error", "client-error", "decode-error"],
)
async def test_failed_telegram_send_returns_502_and_keeps_cooldown(
    client: TestClient, bot: SimpleNamespace, caplog: pytest.LogCaptureFixture, error: Exception
) -> None:
    bot.send_document.side_effect = error
    headers = auth_headers()
    await assert_error(
        await client.post(EXPORT_URL, headers=headers, json={"kind": "leads"}), 502, "send_failed"
    )
    await assert_error(
        await client.post(EXPORT_URL, headers=headers, json={"kind": "leads"}), 429, "too_many"
    )
    bot.send_document.assert_awaited_once()
    assert caplog.messages == [type(error).__name__]
    assert caplog.records[0].exc_info is None


@pytest.mark.parametrize("error_type", [RuntimeError, web.HTTPInternalServerError, web.HTTPServiceUnavailable])
async def test_internal_error_logs_only_exception_type(
    client: TestClient, storage: Mock, caplog: pytest.LogCaptureFixture, error_type: type[Exception]
) -> None:
    headers = auth_headers()
    private_detail = f"Fake User 555-0100 {TOKEN} {headers['Authorization']}"
    if issubclass(error_type, web.HTTPException):
        error = error_type(text=private_detail, reason=private_detail)
    else:
        error = error_type(private_detail)
    storage.count_users.side_effect = error
    with caplog.at_level(logging.ERROR):
        response = await client.get(DASHBOARD_URL, headers=headers)
        await assert_error(response, 500, "internal")
    assert private_detail not in response.reason
    assert caplog.messages == [error_type.__name__]
    assert caplog.records[0].exc_info is None


async def test_raised_client_error_keeps_body_reason_and_headers(client: TestClient, storage: Mock) -> None:
    storage.count_users.side_effect = web.HTTPBadRequest(
        text="original response", reason="Invalid request", headers={"X-Test-Header": "original"}
    )
    response = await client.get(DASHBOARD_URL, headers=auth_headers())
    assert response.status == 400
    assert response.reason == "Invalid request"
    assert response.headers["X-Test-Header"] == "original"
    assert await response.text() == "original response"
    assert_security_headers(response.headers)


async def test_returned_internal_error_response_is_sanitized(app: web.Application) -> None:
    async def fail(request: web.Request) -> web.Response:
        return web.Response(status=500, text="private failure detail")

    app.router.add_get("/test-error", fail)
    async with TestClient(TestServer(app), raise_for_status=False) as client:
        await assert_error(await client.get("/test-error"), 500, "internal")


async def test_static_redirect(client: TestClient) -> None:
    response = await client.get("/admin", allow_redirects=False)
    assert response.status in (301, 308)
    assert response.headers["Location"] == "/admin/"
    assert_security_headers(response.headers)


@pytest.mark.parametrize("filename", ["", *STATIC_ASSETS])
async def test_static_assets_are_served_without_auth(client: TestClient, filename: str) -> None:
    response = await client.get(f"/admin/{filename}")
    expected_body, expected_type = STATIC_ASSETS[filename or "index.html"]
    assert response.status == 200
    assert response.content_type == expected_type
    assert await response.read() == expected_body
    assert_security_headers(response.headers)


@pytest.mark.parametrize(
    "path",
    [
        "/admin/tests/",
        "/admin/tests/preview.html",
        "/admin/tests%2fpreview.html",
        "/admin/assets",
        "/admin/assets/",
        "/admin/assets/sample.js",
        "/admin/assets%5csample.js",
        "/admin/directory.js",
        "/admin/fixture.json",
        "/admin/../outside.js",
        "/admin/../admin/app.js",
        "/admin/%2e%2e/outside.js",
        "/admin/%2e%2e%5coutside.js",
        "/admin/fonts/%2e%2e/panel.woff2",
        "/admin/fonts/panel.woff",
        "/admin/fonts/notes.txt",
        "/admin/fonts/missing.woff2",
    ],
)
async def test_private_or_missing_files_return_404(client: TestClient, path: str) -> None:
    # Keep dot segments and encoded separators intact on the wire.
    url = URL(f"{client.make_url('').origin()}{path}", encoded=True)
    response = await client.session.get(url)
    assert response.status == 404
    assert_security_headers(response.headers)


async def test_static_symlink_cannot_serve_files_outside_directory(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    link = tmp_path / "static" / "linked.js"
    target = tmp_path / "outside.js"
    try:
        link.symlink_to(target)
    except OSError as exc:
        if getattr(exc, "winerror", None) != 1314:
            raise
        # Simulate Windows link resolution when symlink creation requires extra privileges.
        original_resolve = Path.resolve

        def resolve(path: Path, strict: bool = False) -> Path:
            return target if path == link else original_resolve(path, strict=strict)

        monkeypatch.setattr(Path, "resolve", resolve)
        link.write_bytes(b"link placeholder")

    response = await client.get("/admin/linked.js")
    assert response.status == 404
    assert_security_headers(response.headers)


async def test_woff2_from_fonts_directory(client: TestClient) -> None:
    response = await client.get("/admin/fonts/panel.woff2")
    assert response.status == 200
    assert response.content_type == "font/woff2"
    assert await response.read() == FONT_BYTES
    assert_security_headers(response.headers)


async def test_early_http_error_has_security_headers(client: TestClient) -> None:
    response = await client.get(DASHBOARD_URL, headers={"Expect": "unknown-expect-test-marker"})
    await assert_error(response, HTTPStatus.EXPECTATION_FAILED, "bad_request")


@pytest.mark.parametrize(
    ("method", "path", "expect"),
    [
        ("GET", DASHBOARD_URL, "100-continue"),
        ("GET", EXPORT_URL, "100-continue"),
        ("HEAD", "/admin/", "100-continue"),
        ("GET", "/unknown-path", "100-continue"),
        ("PUT", DASHBOARD_URL, "100-continue"),
        ("OPTIONS", "*", "100-continue"),
        ("POST", EXPORT_URL, "unknown-expect-test-marker"),
        ("POST", EXPORT_URL, ""),
        ("POST", EXPORT_URL, "100-continue\r\nExpect: unknown-expect-test-marker"),
    ],
)
async def test_unexpected_expect_returns_generic_error_without_continue(
    app: web.Application, method: str, path: str, expect: str
) -> None:
    async with panel_connection(app) as (reader, writer):
        writer.write(
            (
                f"{method} {path} HTTP/1.1\r\nHost: localhost\r\n"
                f"Expect: {expect}\r\nContent-Length: {len(b'unsent')}\r\n\r\n"
            ).encode("ascii")
        )
        await writer.drain()
        status, headers = await read_response_head(reader)
        assert status == HTTPStatus.EXPECTATION_FAILED
        assert_security_headers(headers)
        assert headers["Connection"] == "close"
        body = await reader.read()
        if method == "HEAD":
            assert body == b""
        else:
            assert json.loads(body) == {"error": "bad_request"}


async def test_export_continue_and_final_response_have_security_headers(app: web.Application) -> None:
    body = b'{"kind":"leads"}'
    authorization = auth_headers()["Authorization"]
    async with panel_connection(app) as (reader, writer):
        writer.write(
            (
                f"POST {EXPORT_URL} HTTP/1.1\r\nHost: localhost\r\n"
                f"Authorization: {authorization}\r\nExpect: 100-continue\r\n"
                f"Content-Length: {len(body)}\r\n\r\n"
            ).encode("ascii")
        )
        await writer.drain()
        status, headers = await read_response_head(reader)
        assert status == HTTPStatus.CONTINUE
        assert_security_headers(headers)
        assert "Content-Length" not in headers
        assert "Transfer-Encoding" not in headers

        writer.write(body)
        await writer.drain()
        status, headers = await read_response_head(reader)
        assert status == HTTPStatus.OK
        assert_security_headers(headers)
        assert json.loads(await reader.readexactly(int(headers["Content-Length"]))) == {"ok": True}


@pytest.mark.parametrize(
    ("authorization", "oversize", "expected_status", "error"),
    [
        ({}, False, HTTPStatus.UNAUTHORIZED, "unauthorized"),
        (auth_headers(FOREIGN_ID), True, HTTPStatus.FORBIDDEN, "forbidden"),
        (auth_headers(), True, HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "bad_request"),
    ],
)
async def test_export_rejects_expect_before_sending_continue(
    app: web.Application,
    bot: SimpleNamespace,
    authorization: dict[str, str],
    oversize: bool,
    expected_status: HTTPStatus,
    error: str,
) -> None:
    content_length = app._client_max_size + 1 if oversize else len(b'{"kind":"leads"}')
    auth_line = "".join(f"{name}: {value}\r\n" for name, value in authorization.items())
    async with panel_connection(app) as (reader, writer):
        writer.write(
            (
                f"POST {EXPORT_URL} HTTP/1.1\r\nHost: localhost\r\n"
                f"{auth_line}Expect: 100-continue\r\nContent-Length: {content_length}\r\n\r\n"
            ).encode("ascii")
        )
        await writer.drain()
        status, headers = await read_response_head(reader)
        assert status == expected_status
        assert_security_headers(headers)
        assert headers["Connection"] == "close"
        assert json.loads(await reader.readexactly(int(headers["Content-Length"]))) == {"error": error}
        assert await reader.read() == b""
    bot.send_document.assert_not_awaited()


@pytest.mark.parametrize(
    ("method", "path", "status"),
    [("GET", "/unknown-path", 404), ("PUT", DASHBOARD_URL, 405)],
)
async def test_router_errors_have_security_headers(client: TestClient, method: str, path: str, status: int) -> None:
    response = await client.request(method, path)
    assert response.status == status
    assert_security_headers(response.headers)


async def test_parser_error_has_generic_body_and_security_headers(app: web.Application) -> None:
    marker = b"malformed-header-test-marker"
    prepared = AsyncMock()
    app.on_response_prepare.append(prepared)
    async with panel_connection(app) as (reader, writer):
        writer.write(b"GET /admin/ HTTP/1.1\r\nHost: localhost\r\nInvalid " + marker + b"\r\n\r\n")
        await writer.drain()
        status, headers = await read_response_head(reader)
        assert status == HTTPStatus.BAD_REQUEST
        assert_security_headers(headers)
        body = await reader.read()
        assert marker not in body
        assert json.loads(body) == {"error": "bad_request"}
    prepared.assert_awaited_once()


async def test_start_panel_binds_loopback_and_returns_cleanable_runner(app: web.Application) -> None:
    runner = await start_panel(app)
    try:
        assert isinstance(runner, web.AppRunner)
        [(address, port)] = runner.addresses
        assert address == "127.0.0.1"
        assert port > 0
    finally:
        await runner.cleanup()
    assert not runner.addresses


async def test_start_panel_rejects_non_loopback_host_before_startup(app: web.Application) -> None:
    startup = AsyncMock()
    app.on_startup.append(startup)
    with pytest.raises(ValueError, match="127.0.0.1"):
        runner = await start_panel(app, host="0.0.0.0")
        await runner.cleanup()
    startup.assert_not_awaited()
