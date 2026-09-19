import json

import pytest
from httpx import AsyncClient
from starlette.requests import Request

from app.core import exception_handlers


async def test_not_found_uses_standard_error_shape(client: AsyncClient) -> None:
    response = await client.get("/api/does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "HTTP_404"
    assert body["error"]["message"] == "Not Found"
    assert body["error"]["request_id"] == response.headers["X-Request-ID"]


async def test_unhandled_error_does_not_log_or_return_exception_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[tuple[str, dict[str, object]]] = []

    class SafeLogger:
        def error(self, event: str, **fields: object) -> None:
            events.append((event, fields))

    monkeypatch.setattr(exception_handlers, "logger", SafeLogger())
    request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})
    secret = "database_password=must-not-escape"

    response = await exception_handlers.unhandled_error_handler(request, RuntimeError(secret))
    body = json.loads(response.body)

    assert response.status_code == 500
    assert secret not in response.body.decode()
    assert events == [("unhandled_exception", {"exception_type": "RuntimeError"})]
    assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
