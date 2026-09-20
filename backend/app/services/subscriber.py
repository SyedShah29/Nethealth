from app.core.errors import AppError
from app.models.subscriber import Subscriber, SubscriberSession
from app.repositories.subscriber import SubscriberRepository


class SubscriberService:
    def __init__(self, repository: SubscriberRepository) -> None:
        self.repository = repository

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
        return await self.repository.list_subscribers(
            search=_clean(search),
            status=_clean(status),
            nas_id=_clean(nas_id),
            olt_id=_clean(olt_id),
            pon_id=_clean(pon_id),
            onu_id=_clean(onu_id),
            offset=offset,
            limit=limit,
        )

    async def get_subscriber(self, subscriber_id: str) -> Subscriber:
        subscriber = await self.repository.get(subscriber_id)
        return self._require_subscriber(subscriber)

    async def resolve_external_reference(self, external_reference: str) -> Subscriber:
        normalized = external_reference.strip()
        if not normalized:
            raise AppError(
                "INVALID_EXTERNAL_REFERENCE",
                "External reference must not be blank.",
                422,
            )
        subscriber = await self.repository.get_by_external_reference(normalized)
        return self._require_subscriber(subscriber)

    async def list_sessions(
        self, subscriber_id: str, *, limit: int = 100
    ) -> list[SubscriberSession]:
        await self.get_subscriber(subscriber_id)
        return await self.repository.list_sessions(subscriber_id, limit=limit)

    @staticmethod
    def _require_subscriber(subscriber: Subscriber | None) -> Subscriber:
        if subscriber is None:
            raise AppError("SUBSCRIBER_NOT_FOUND", "Subscriber not found.", 404)
        return subscriber


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None
