from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.dependencies.auth import get_subscriber_service, require_permission
from app.models.auth import User
from app.models.enums import PermissionCode
from app.models.subscriber import Subscriber, SubscriberSession
from app.schemas.subscriber import SubscriberResponse, SubscriberSessionResponse
from app.services.subscriber import SubscriberService

router = APIRouter(prefix="/subscribers")
read_subscribers = require_permission(PermissionCode.SUBSCRIBERS_READ.value)


@router.get("", response_model=list[SubscriberResponse])
async def list_subscribers(
    service: Annotated[SubscriberService, Depends(get_subscriber_service)],
    _user: Annotated[User, Depends(read_subscribers)],
    search: Annotated[str | None, Query(max_length=255)] = None,
    status: Annotated[str | None, Query(max_length=32)] = None,
    nas_id: Annotated[str | None, Query(max_length=120)] = None,
    olt_id: Annotated[str | None, Query(max_length=120)] = None,
    pon_id: Annotated[str | None, Query(max_length=120)] = None,
    onu_id: Annotated[str | None, Query(max_length=120)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[Subscriber]:
    return await service.list_subscribers(
        search=search,
        status=status,
        nas_id=nas_id,
        olt_id=olt_id,
        pon_id=pon_id,
        onu_id=onu_id,
        offset=offset,
        limit=limit,
    )


@router.get("/resolve", response_model=SubscriberResponse)
async def resolve_external_reference(
    external_reference: Annotated[str, Query(min_length=1, max_length=255)],
    service: Annotated[SubscriberService, Depends(get_subscriber_service)],
    _user: Annotated[User, Depends(read_subscribers)],
) -> Subscriber:
    return await service.resolve_external_reference(external_reference)


@router.get("/{subscriber_id}", response_model=SubscriberResponse)
async def get_subscriber(
    subscriber_id: Annotated[str, Path(min_length=1, max_length=120)],
    service: Annotated[SubscriberService, Depends(get_subscriber_service)],
    _user: Annotated[User, Depends(read_subscribers)],
) -> Subscriber:
    return await service.get_subscriber(subscriber_id)


@router.get(
    "/{subscriber_id}/sessions",
    response_model=list[SubscriberSessionResponse],
)
async def list_subscriber_sessions(
    subscriber_id: Annotated[str, Path(min_length=1, max_length=120)],
    service: Annotated[SubscriberService, Depends(get_subscriber_service)],
    _user: Annotated[User, Depends(read_subscribers)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[SubscriberSession]:
    return await service.list_sessions(subscriber_id, limit=limit)
