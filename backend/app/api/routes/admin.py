from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies.auth import (
    get_admin_service,
    require_permission,
    require_trusted_origin,
)
from app.models.auth import AuditLog, Permission, Role, User
from app.models.enums import PermissionCode
from app.schemas.auth import (
    AuditLogResponse,
    PermissionResponse,
    RoleResponse,
    RoleUpdateRequest,
)
from app.services.admin import AdminService

router = APIRouter(prefix="/admin")


@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(
    service: Annotated[AdminService, Depends(get_admin_service)],
    _actor: Annotated[
        User, Depends(require_permission(PermissionCode.ROLES_READ.value))
    ],
) -> list[Role]:
    return await service.list_roles()


@router.get("/permissions", response_model=list[PermissionResponse])
async def list_permissions(
    service: Annotated[AdminService, Depends(get_admin_service)],
    _actor: Annotated[
        User, Depends(require_permission(PermissionCode.ROLES_READ.value))
    ],
) -> list[Permission]:
    return await service.list_permissions()


@router.patch(
    "/roles/{role_id}",
    response_model=RoleResponse,
    dependencies=[Depends(require_trusted_origin)],
)
async def update_role(
    role_id: UUID,
    payload: RoleUpdateRequest,
    service: Annotated[AdminService, Depends(get_admin_service)],
    actor: Annotated[
        User, Depends(require_permission(PermissionCode.ROLES_MANAGE.value))
    ],
) -> Role:
    return await service.update_role(
        role_id,
        description=payload.description,
        permission_codes=payload.permissions,
        actor=actor,
    )


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def list_audit_logs(
    service: Annotated[AdminService, Depends(get_admin_service)],
    _actor: Annotated[
        User, Depends(require_permission(PermissionCode.AUDIT_READ.value))
    ],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[AuditLog]:
    return await service.list_audit_logs(limit=limit)
