from collections.abc import AsyncIterator

from fastapi import FastAPI
from httpx import AsyncClient

from app.cache.redis import get_redis_client
from app.db.session import get_db_session
from tests.conftest import FakeRedis, FakeSession


async def override_db() -> AsyncIterator[FakeSession]:
    yield FakeSession()


async def override_redis() -> AsyncIterator[FakeRedis]:
    yield FakeRedis()


async def test_application_health(client: AsyncClient) -> None:
    response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "nethealth-api"}
    assert "X-Request-ID" in response.headers


async def test_database_health(client: AsyncClient) -> None:
    app = client._transport.app  # type: ignore[attr-defined]
    assert isinstance(app, FastAPI)
    app.dependency_overrides[get_db_session] = override_db

    response = await client.get("/api/health/database")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "dependency": "database",
        "version": "2.19.3",
    }


async def test_redis_health(client: AsyncClient) -> None:
    app = client._transport.app  # type: ignore[attr-defined]
    assert isinstance(app, FastAPI)
    app.dependency_overrides[get_redis_client] = override_redis

    response = await client.get("/api/health/redis")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "dependency": "redis",
        "version": None,
    }
