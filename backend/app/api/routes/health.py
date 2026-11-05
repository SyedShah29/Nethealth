from typing import Annotated

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis import get_redis_client
from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.schemas.health import DependencyHealthResponse, HealthResponse
from app.services.health import check_database, check_redis

router = APIRouter(prefix="/health")


@router.get("", response_model=HealthResponse)
async def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    return HealthResponse(status="healthy", service=settings.service_name)


@router.get("/database", response_model=DependencyHealthResponse)
async def database_health(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DependencyHealthResponse:
    result = await check_database(session)
    return DependencyHealthResponse(status="healthy", dependency="database", version=result.version)


@router.get("/redis", response_model=DependencyHealthResponse)
async def redis_health(
    client: Annotated[Redis, Depends(get_redis_client)],
) -> DependencyHealthResponse:
    await check_redis(client)
    return DependencyHealthResponse(status="healthy", dependency="redis")
