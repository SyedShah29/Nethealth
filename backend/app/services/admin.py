from app.models.auth import AuditLog, Role
from app.repositories.audit import AuditLogRepository
from app.repositories.auth import RoleRepository


class AdminService:
    def __init__(
        self,
        roles: RoleRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self.roles = roles
        self.audit_logs = audit_logs

    async def list_roles(self) -> list[Role]:
        return await self.roles.list()

    async def list_audit_logs(self, *, limit: int) -> list[AuditLog]:
        return await self.audit_logs.list(limit=limit)
