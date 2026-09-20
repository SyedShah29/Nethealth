# ruff: noqa
from typing import Any
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from app.core.errors import AppError
from app.models.inventory import CollectorAssignment, CollectorProfile, Device, Interface, Site
from app.repositories.inventory import InventoryRepository

class InventoryService:
    def __init__(self, repo: InventoryRepository): self.repo = repo
    async def list(self, model: Any, filters: list[Any] | None = None) -> list[Any]: return await self.repo.list(model, filters=filters)
    async def get(self, model: Any, item_id: UUID) -> Any:
        item = await self.repo.get(model, item_id)
        if item is None: raise AppError("NOT_FOUND", "Inventory item not found.", 404)
        return item
    async def create(self, model: Any, data: dict[str, Any]) -> Any:
        try: return await self.repo.add(model(**data))
        except IntegrityError as exc: raise AppError("CONFLICT", "Inventory item conflicts with existing data.", 409) from exc
    async def update(self, model: Any, item_id: UUID, data: dict[str, Any]) -> Any:
        item = await self.get(model, item_id)
        for key, value in data.items(): setattr(item, key, value)
        await self.repo.session.flush(); return item
    async def delete(self, model: Any, item_id: UUID) -> None: await self.repo.delete(await self.get(model, item_id))
