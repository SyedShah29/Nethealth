from typing import Any
from uuid import UUID

from app.models.auth import AuditLog
from app.models.enums import AuditEventType
from app.repositories.audit import AuditLogRepository


class AuditService:
    def __init__(self, repository: AuditLogRepository) -> None:
        self.repository = repository

    async def record(
        self,
        event_type: AuditEventType,
        *,
        success: bool,
        actor_user_id: UUID | None = None,
        target_user_id: UUID | None = None,
        request_id: str | None = None,
        subject_fingerprint: str | None = None,
        event_metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        return await self.repository.add(
            AuditLog(
                event_type=event_type.value,
                actor_user_id=actor_user_id,
                target_user_id=target_user_id,
                success=success,
                request_id=request_id,
                subject_fingerprint=subject_fingerprint,
                event_metadata=event_metadata or {},
            )
        )
