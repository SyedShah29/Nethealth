# ruff: noqa
from typing import Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.inventory import CollectorAssignment, CollectorProfile, Device, Interface, Site


class InventoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, model: Any, *, filters: list[Any] | None = None) -> list[Any]:
        result = await self.session.execute(
            select(model)
            .where(*(filters or []))
            .order_by(model.name if hasattr(model, "name") else model.id)
        )
        return list(result.scalars().all())

    async def get(self, model: Any, item_id: UUID) -> Any | None:
        return await self.session.get(model, item_id)

    async def add(self, item: Any) -> Any:
        self.session.add(item)
        await self.session.flush()
        return item

    async def delete(self, item: Any) -> None:
        await self.session.delete(item)
        await self.session.flush()
