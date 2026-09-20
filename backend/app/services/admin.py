from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.auth import AuditLog, Permission, Role, User
from app.models.enums import AuditEventType, PermissionCode, RoleName
from app.repositories.audit import AuditLogRepository
from app.repositories.auth import PermissionRepository, RoleRepository
from app.services.audit import AuditService


class AdminService:
    def __init__(
        self,
        session: AsyncSession,
        roles: RoleRepository,
        permissions: PermissionRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self.session = session
        self.roles = roles
        self.permissions = permissions
        self.audit_logs = audit_logs
        self.audit = AuditService(audit_logs)

    async def list_roles(self) -> list[Role]:
        return await self.roles.list()

    async def list_permissions(self) -> list[Permission]:
        return await self.permissions.list()

    async def update_role(
        self,
        role_id: UUID,
        *,
        description: str | None,
        permission_codes: list[str] | None,
        actor: User,
    ) -> Role:
        role = await self.roles.get_by_id(role_id)
        if role is None:
            raise AppError("ROLE_NOT_FOUND", "The requested role does not exist.", 404)
        if description is not None:
            role.description = description
        if permission_codes is not None:
            requested = set(permission_codes)
            permissions = await self.permissions.get_by_codes(requested)
            if {permission.code for permission in permissions} != requested:
                raise AppError(
                    "PERMISSION_NOT_FOUND",
                    "A requested permission does not exist.",
                    400,
                )
            if role.name == RoleName.ADMIN.value:
                required = {
                    PermissionCode.USERS_MANAGE.value,
                    PermissionCode.ROLES_MANAGE.value,
                    PermissionCode.AUDIT_READ.value,
                }
                if not required <= requested:
                    raise AppError(
                        "ADMIN_PERMISSIONS_REQUIRED",
                        "The administrator role must retain core administration permissions.",
                        409,
                    )
            role.permissions = permissions
        await self.audit.record(
            AuditEventType.CONFIGURATION_CHANGED,
            success=True,
            actor_user_id=actor.id,
            event_metadata={
                "resource_type": "Role",
                "resource_id": str(role.id),
                "action": "updated",
            },
        )
        await self.session.commit()
        return role

    async def list_audit_logs(self, *, limit: int) -> list[AuditLog]:
        return await self.audit_logs.list(limit=limit)
