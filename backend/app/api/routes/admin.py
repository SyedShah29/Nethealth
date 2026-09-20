from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies.auth import get_admin_service, require_permission
from app.models.auth import AuditLog, Role, User
from app.models.enums import PermissionCode
from app.schemas.auth import AuditLogResponse, RoleResponse
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


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def list_audit_logs(
    service: Annotated[AdminService, Depends(get_admin_service)],
    _actor: Annotated[
        User, Depends(require_permission(PermissionCode.AUDIT_READ.value))
    ],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[AuditLog]:
    return await service.list_audit_logs(limit=limit)
