from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.errors import AppError
from app.models.enums import AuditEventType
from app.repositories.inventory import InventoryRepository
from app.services.audit import AuditService


class InventoryService:
    def __init__(self, repo: InventoryRepository, audit: AuditService) -> None:
        self.repo = repo
        self.audit = audit

    async def list(self, model: Any, filters: list[Any] | None = None) -> list[Any]:
        return await self.repo.list(model, filters=filters)

    async def get(self, model: Any, item_id: UUID) -> Any:
        item = await self.repo.get(model, item_id)
        if item is None:
            raise AppError("NOT_FOUND", "Inventory item not found.", 404)
        return item

    async def create(self, model: Any, data: dict[str, Any], actor_user_id: UUID) -> Any:
        try:
            item = await self.repo.add(model(**data))
            await self._audit(model, item.id, "created", actor_user_id)
            await self.repo.session.commit()
            return item
        except IntegrityError as exc:
            await self.repo.session.rollback()
            raise AppError(
                "CONFLICT", "Inventory item conflicts with existing data.", 409
            ) from exc

    async def update(
        self,
        model: Any,
        item_id: UUID,
        data: dict[str, Any],
        actor_user_id: UUID,
    ) -> Any:
        item = await self.get(model, item_id)
        for key, value in data.items():
            setattr(item, key, value)
        await self.repo.session.flush()
        await self._audit(model, item_id, "updated", actor_user_id)
        await self.repo.session.commit()
        return item

    async def delete(self, model: Any, item_id: UUID, actor_user_id: UUID) -> None:
        await self.repo.delete(await self.get(model, item_id))
        await self._audit(model, item_id, "deleted", actor_user_id)
        await self.repo.session.commit()

    async def _audit(
        self,
        model: Any,
        item_id: UUID,
        action: str,
        actor_user_id: UUID,
    ) -> None:
        await self.audit.record(
            AuditEventType.CONFIGURATION_CHANGED,
            success=True,
            actor_user_id=actor_user_id,
            event_metadata={
                "resource_type": model.__name__,
                "resource_id": str(item_id),
                "action": action,
            },
        )
