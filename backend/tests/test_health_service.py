import pytest

from app.core.errors import AppError
from app.services.health import check_database, check_redis
from tests.conftest import FakeRedis, FakeSession


class MissingTimescaleSession(FakeSession):
    async def execute(self, statement: object) -> object:
        class MissingResult:
            def scalar_one_or_none(self) -> None:
                return None

        return MissingResult()


class UnavailableRedis(FakeRedis):
    async def ping(self) -> bool:
        raise ConnectionError("secret connection details must not escape")


async def test_database_requires_timescaledb() -> None:
    with pytest.raises(AppError, match="TimescaleDB extension is not enabled") as error:
        await check_database(MissingTimescaleSession())  # type: ignore[arg-type]
    assert error.value.code == "TIMESCALEDB_UNAVAILABLE"


async def test_redis_failure_is_sanitized() -> None:
    with pytest.raises(AppError, match="Redis health check failed") as error:
        await check_redis(UnavailableRedis())  # type: ignore[arg-type]
    assert error.value.code == "REDIS_UNAVAILABLE"
    assert "secret" not in error.value.message
