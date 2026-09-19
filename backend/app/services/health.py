from dataclasses import dataclass

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError


@dataclass(frozen=True, slots=True)
class DatabaseHealth:
    version: str


async def check_database(session: AsyncSession) -> DatabaseHealth:
    try:
        await session.execute(text("SELECT 1"))
        result = await session.execute(
            text("SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'")
        )
        version = result.scalar_one_or_none()
    except Exception as exc:
        raise AppError(
            code="DATABASE_UNAVAILABLE",
            message="Database health check failed.",
            status_code=503,
        ) from exc
    if version is None:
        raise AppError(
            code="TIMESCALEDB_UNAVAILABLE",
            message="TimescaleDB extension is not enabled.",
            status_code=503,
        )
    return DatabaseHealth(version=str(version))


async def check_redis(client: Redis) -> None:
    try:
        healthy = await client.ping()
    except Exception as exc:
        raise AppError(
            code="REDIS_UNAVAILABLE",
            message="Redis health check failed.",
            status_code=503,
        ) from exc
    if not healthy:
        raise AppError(
            code="REDIS_UNAVAILABLE",
            message="Redis health check failed.",
            status_code=503,
        )
