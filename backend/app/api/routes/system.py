from typing import Annotated

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import require_permission
from app.cache.redis import get_redis_client
from app.db.session import get_db_session
from app.models.auth import User
from app.models.enums import PermissionCode
from app.schemas.system import PlatformHealthResponse
from app.services.system import PlatformHealthService

router = APIRouter(prefix="/system")
dashboards_read = require_permission(PermissionCode.DASHBOARDS_READ.value)


@router.get("/platform-health", response_model=PlatformHealthResponse)
async def platform_health(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Redis, Depends(get_redis_client)],
    _user: Annotated[User, Depends(dashboards_read)],
) -> PlatformHealthResponse:
    return await PlatformHealthService(session, redis).get()
