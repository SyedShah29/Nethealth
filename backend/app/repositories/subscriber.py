from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscriber import Subscriber, SubscriberSession


class SubscriberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_subscribers(
        self,
        *,
        search: str | None = None,
        status: str | None = None,
        nas_id: str | None = None,
        olt_id: str | None = None,
        pon_id: str | None = None,
        onu_id: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Subscriber]:
        statement = select(Subscriber)
        if search:
            pattern = f"%{search}%"
            statement = statement.where(
                or_(
                    Subscriber.subscriber_id.ilike(pattern),
                    Subscriber.external_reference.ilike(pattern),
                )
            )
        for column, value in (
            (Subscriber.status, status),
            (Subscriber.nas_id, nas_id),
            (Subscriber.olt_id, olt_id),
            (Subscriber.pon_id, pon_id),
            (Subscriber.onu_id, onu_id),
        ):
            if value is not None:
                statement = statement.where(column == value)
        result = await self.session.execute(
            statement.order_by(Subscriber.subscriber_id).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def get(self, subscriber_id: str) -> Subscriber | None:
        return await self.session.get(Subscriber, subscriber_id)

    async def get_by_external_reference(
        self, external_reference: str
    ) -> Subscriber | None:
        result = await self.session.execute(
            select(Subscriber).where(
                Subscriber.external_reference == external_reference
            )
        )
        return result.scalar_one_or_none()

    async def list_sessions(
        self, subscriber_id: str, *, limit: int = 100
    ) -> list[SubscriberSession]:
        result = await self.session.execute(
            select(SubscriberSession)
            .where(SubscriberSession.subscriber_id == subscriber_id)
            .order_by(SubscriberSession.session_start.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
