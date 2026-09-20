from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.api.dependencies.auth import (
    get_user_service,
    require_permission,
    require_trusted_origin,
)
from app.models.auth import User
from app.models.enums import PermissionCode
from app.schemas.auth import UserCreateRequest, UserResponse, UserUpdateRequest
from app.services.users import UserService

router = APIRouter(prefix="/users")
manage_users = require_permission(PermissionCode.USERS_MANAGE.value)


@router.get("", response_model=list[UserResponse])
async def list_users(
    service: Annotated[UserService, Depends(get_user_service)],
    _actor: Annotated[User, Depends(manage_users)],
) -> list[User]:
    return await service.list_users()


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_trusted_origin)],
)
async def create_user(
    payload: UserCreateRequest,
    request: Request,
    service: Annotated[UserService, Depends(get_user_service)],
    actor: Annotated[User, Depends(manage_users)],
) -> User:
    return await service.create_user(
        name=payload.name,
        email=payload.email,
        password=payload.password,
        role_name=payload.role,
        actor=actor,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_trusted_origin)],
)
async def update_user(
    user_id: UUID,
    payload: UserUpdateRequest,
    request: Request,
    service: Annotated[UserService, Depends(get_user_service)],
    actor: Annotated[User, Depends(manage_users)],
) -> User:
    return await service.update_user(
        user_id,
        name=payload.name,
        role_name=payload.role,
        active=payload.active,
        actor=actor,
        request_id=getattr(request.state, "request_id", None),
    )
