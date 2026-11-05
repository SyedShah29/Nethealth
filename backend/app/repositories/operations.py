from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.operations import (
    CapacityAssessment,
    CapacityThreshold,
    CapacityTrend,
    Incident,
    IncidentEvent,
    NotificationChannel,
    NotificationDelivery,
    NotificationRule,
    OperationalAnomaly,
    SubscriberHealthScore,
)

ACTIVE_INCIDENT_STATES = ("OPEN", "ACKNOWLEDGED", "INVESTIGATING")


class OperationsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_health_score(self, item: SubscriberHealthScore) -> SubscriberHealthScore:
        self.session.add(item)
        await self.session.flush()
        return item

    async def latest_health_score(self, subscriber_id: str) -> SubscriberHealthScore | None:
        result = await self.session.execute(
            select(SubscriberHealthScore)
            .where(SubscriberHealthScore.subscriber_id == subscriber_id)
            .order_by(SubscriberHealthScore.evaluated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def add_anomaly(self, item: OperationalAnomaly) -> OperationalAnomaly:
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_anomalies(self, limit: int = 100) -> list[OperationalAnomaly]:
        result = await self.session.execute(
            select(OperationalAnomaly).order_by(OperationalAnomaly.detected_at.desc()).limit(limit)
        )
        return list(result.scalars())

    async def add_incident(self, item: Incident) -> Incident:
        self.session.add(item)
        await self.session.flush()
        return item

    async def get_incident(self, incident_id: UUID) -> Incident | None:
        return await self.session.get(Incident, incident_id)

    async def find_active_incident(
        self, category: str, entity_type: str, entity_id: str
    ) -> Incident | None:
        result = await self.session.execute(
            select(Incident).where(
                Incident.category == category,
                Incident.primary_entity_type == entity_type,
                Incident.primary_entity_id == entity_id,
                Incident.status.in_(ACTIVE_INCIDENT_STATES),
            )
        )
        return result.scalar_one_or_none()

    async def active_incident_for_subscriber(self, subscriber_id: str) -> Incident | None:
        result = await self.session.execute(
            select(Incident)
            .where(Incident.status.in_(ACTIVE_INCIDENT_STATES))
            .order_by(Incident.last_seen.desc())
        )
        return next(
            (
                incident
                for incident in result.scalars()
                if subscriber_id in incident.affected_subscribers
                or (
                    incident.primary_entity_type == "SUBSCRIBER"
                    and incident.primary_entity_id == subscriber_id
                )
            ),
            None,
        )

    async def list_incidents(
        self, *, status: str | None = None, limit: int = 100
    ) -> list[Incident]:
        statement = select(Incident)
        if status is not None:
            statement = statement.where(Incident.status == status)
        result = await self.session.execute(
            statement.order_by(Incident.last_seen.desc()).limit(limit)
        )
        return list(result.scalars())

    async def add_event(self, event: IncidentEvent) -> IncidentEvent:
        self.session.add(event)
        await self.session.flush()
        return event

    async def list_events(self, incident_id: UUID) -> list[IncidentEvent]:
        result = await self.session.execute(
            select(IncidentEvent)
            .where(IncidentEvent.incident_id == incident_id)
            .order_by(IncidentEvent.occurred_at, IncidentEvent.id)
        )
        return list(result.scalars())

    async def add_channel(self, item: NotificationChannel) -> NotificationChannel:
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_channels(self) -> list[NotificationChannel]:
        result = await self.session.execute(
            select(NotificationChannel).order_by(NotificationChannel.name)
        )
        return list(result.scalars())

    async def get_channel(self, channel_id: UUID) -> NotificationChannel | None:
        return await self.session.get(NotificationChannel, channel_id)

    async def add_notification_rule(self, item: NotificationRule) -> NotificationRule:
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_notification_rules(self) -> list[NotificationRule]:
        result = await self.session.execute(
            select(NotificationRule).order_by(NotificationRule.name)
        )
        return list(result.scalars())

    async def add_delivery(self, item: NotificationDelivery) -> NotificationDelivery:
        self.session.add(item)
        await self.session.flush()
        return item

    async def delivery_exists(self, fingerprint: str) -> bool:
        result = await self.session.execute(
            select(NotificationDelivery.id).where(NotificationDelivery.fingerprint == fingerprint)
        )
        return result.scalar_one_or_none() is not None

    async def add_capacity_threshold(self, item: CapacityThreshold) -> CapacityThreshold:
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_capacity_thresholds(self) -> list[CapacityThreshold]:
        result = await self.session.execute(
            select(CapacityThreshold).order_by(CapacityThreshold.name)
        )
        return list(result.scalars())

    async def matching_capacity_threshold(
        self, entity_type: str, metric_name: str
    ) -> CapacityThreshold | None:
        result = await self.session.execute(
            select(CapacityThreshold).where(
                CapacityThreshold.entity_type == entity_type,
                CapacityThreshold.metric_name == metric_name,
                CapacityThreshold.enabled.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def add_capacity_assessment(self, item: CapacityAssessment) -> CapacityAssessment:
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_capacity_assessments(self, limit: int = 100) -> list[CapacityAssessment]:
        result = await self.session.execute(
            select(CapacityAssessment).order_by(CapacityAssessment.evaluated_at.desc()).limit(limit)
        )
        return list(result.scalars())

    async def add_capacity_trend(self, item: CapacityTrend) -> CapacityTrend:
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_capacity_trends(self, limit: int = 100) -> list[CapacityTrend]:
        result = await self.session.execute(
            select(CapacityTrend).order_by(CapacityTrend.created_at.desc()).limit(limit)
        )
        return list(result.scalars())

    async def commit(self) -> None:
        await self.session.commit()

    @staticmethod
    def now() -> datetime:
        return datetime.now(UTC)
