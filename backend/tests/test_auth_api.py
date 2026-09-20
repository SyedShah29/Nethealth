from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import FastAPI
from httpx import AsyncClient

from app.api.dependencies.auth import get_auth_service, get_current_user, get_user_service
from app.models.enums import RoleName
from app.services.auth import LoginResult
from tests.factories import make_role, make_user


class FakeAuthService:
    def __init__(self) -> None:
        self.user = make_user()
        self.logout_token: str | None = None

    async def login(self, *_args: Any, **_kwargs: Any) -> LoginResult:
        return LoginResult(
            user=self.user,
            token="opaque-session-token",
            expires_at=datetime.now(UTC) + timedelta(hours=8),
        )

    async def logout(self, token: str | None, **_kwargs: Any) -> None:
        self.logout_token = token


class FakeUserService:
    def __init__(self) -> None:
        self.users = [make_user()]

    async def list_users(self) -> list[Any]:
        return self.users


async def test_login_sets_http_only_strict_session_cookie(client: AsyncClient) -> None:
    app = client._transport.app  # type: ignore[attr-defined]
    assert isinstance(app, FastAPI)
    service = FakeAuthService()
    app.dependency_overrides[get_auth_service] = lambda: service

    response = await client.post(
        "/api/auth/login",
        json={"email": "user@example.test", "password": "a secure test password"},
    )

    assert response.status_code == 200
    cookie = response.headers["set-cookie"]
    assert "nethealth_session=opaque-session-token" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=strict" in cookie
    assert response.json()["user"]["email"] == "user@example.test"
    assert "password" not in response.text


async def test_missing_session_is_rejected(client: AsyncClient) -> None:
    response = await client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert response.headers["www-authenticate"] == "Session"


async def test_login_rejects_untrusted_browser_origin(client: AsyncClient) -> None:
    response = await client.post(
        "/api/auth/login",
        headers={"Origin": "http://127.0.0.1:9999"},
        json={"email": "user@example.test", "password": "a secure test password"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "UNTRUSTED_ORIGIN"


async def test_users_endpoint_allows_admin_role(client: AsyncClient) -> None:
    app = client._transport.app  # type: ignore[attr-defined]
    assert isinstance(app, FastAPI)
    service = FakeUserService()
    app.dependency_overrides[get_current_user] = lambda: make_user()
    app.dependency_overrides[get_user_service] = lambda: service

    response = await client.get("/api/users")

    assert response.status_code == 200
    assert response.json()[0]["email"] == "user@example.test"


async def test_users_endpoint_rejects_viewer_role(client: AsyncClient) -> None:
    app = client._transport.app  # type: ignore[attr-defined]
    assert isinstance(app, FastAPI)
    viewer = make_user(role=make_role(RoleName.VIEWER, permissions=()))
    app.dependency_overrides[get_current_user] = lambda: viewer
    app.dependency_overrides[get_user_service] = FakeUserService

    response = await client.get("/api/users")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
