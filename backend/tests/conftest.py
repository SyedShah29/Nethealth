import os
import secrets
from collections.abc import AsyncIterator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

# Tests use unique ephemeral credentials and never connect to external services.
os.environ.setdefault("DATABASE_PASSWORD", secrets.token_urlsafe(32))
os.environ.setdefault("REDIS_PASSWORD", secrets.token_urlsafe(32))

from app.main import create_app  # noqa: E402
from app.security.passwords import PasswordHasher  # noqa: E402


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client


@pytest.fixture(scope="session")
def password_hasher() -> PasswordHasher:
    return PasswordHasher()


class FakeScalarResult:
    def scalar_one_or_none(self) -> str:
        return "2.19.3"


class FakeSession:
    async def execute(self, statement: Any) -> FakeScalarResult:
        return FakeScalarResult()


class FakeRedis:
    async def ping(self) -> bool:
        return True
