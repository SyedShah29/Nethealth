from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import AuditLog


class AuditLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, audit_log: AuditLog) -> AuditLog:
        self.session.add(audit_log)
        await self.session.flush()
        return audit_log

    async def list(self, *, limit: int = 100) -> list[AuditLog]:
        result = await self.session.execute(
            select(AuditLog).order_by(AuditLog.occurred_at.desc()).limit(limit)
        )
        return list(result.scalars())
