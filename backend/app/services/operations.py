from __future__ import annotations

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from math import sqrt
from statistics import fmean
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.errors import AppError
from app.models.enums import AuditEventType
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
from app.repositories.operations import OperationsRepository
from app.repositories.subscriber import SubscriberRepository
from app.schemas.operations import (
    AnomalyEvaluationRequest,
    CapacityEvaluationRequest,
    CapacityTrendRequest,
    HealthScoreRequest,
    IncidentCreate,
    IncidentUpdate,
    NotificationChannelCreate,
    NotificationRuleCreate,
)
from app.services.audit import AuditService


def calculate_health_score(payload: HealthScoreRequest) -> tuple[int, str, list[dict[str, Any]]]:
    components: list[dict[str, Any]] = []
    total = 0.0
    for name, weight in payload.weights.items():
        value = payload.components[name]
        contribution = value * weight / 100
        total += contribution
        components.append(
            {
                "component": name,
                "value": round(value, 2),
                "contribution": round(contribution, 2),
                "maximum": weight,
            }
        )
    score = max(0, min(100, round(total)))
    if score >= payload.thresholds["healthy"]:
        category = "HEALTHY"
    elif score >= payload.thresholds["good"]:
        category = "GOOD"
    elif score >= payload.thresholds["warning"]:
        category = "WARNING"
    else:
        category = "CRITICAL"
    return score, category, components


class HealthScoreService:
    def __init__(self, operations: OperationsRepository, subscribers: SubscriberRepository) -> None:
        self.operations = operations
        self.subscribers = subscribers

    async def evaluate(
        self, subscriber_id: str, payload: HealthScoreRequest
    ) -> SubscriberHealthScore:
        if await self.subscribers.get(subscriber_id) is None:
            raise AppError("SUBSCRIBER_NOT_FOUND", "Subscriber not found.", 404)
        score, category, components = calculate_health_score(payload)
        item = await self.operations.add_health_score(
            SubscriberHealthScore(
                subscriber_id=subscriber_id,
                score=score,
                category=category,
                components=components,
                weights=payload.weights,
                thresholds=payload.thresholds,
            )
        )
        await self.operations.commit()
        return item

    async def latest(self, subscriber_id: str) -> SubscriberHealthScore:
        item = await self.operations.latest_health_score(subscriber_id)
        if item is None:
            raise AppError("HEALTH_SCORE_NOT_FOUND", "No subscriber health score exists.", 404)
        return item


def anomaly_values(
    payload: AnomalyEvaluationRequest,
) -> tuple[float, float, bool, list[dict[str, Any]]]:
    baseline = fmean(payload.values)
    variance = fmean([(value - baseline) ** 2 for value in payload.values])
    standard_deviation = sqrt(variance)
    difference = payload.current_value - baseline
    measured = 0.0
    if payload.method == "Z_SCORE":
        measured = abs(difference) / standard_deviation if standard_deviation else 0.0
    elif payload.method == "EWMA":
        ewma = payload.values[0]
        for value in payload.values[1:]:
            ewma = 0.3 * value + 0.7 * ewma
        baseline, difference = ewma, payload.current_value - ewma
        measured = abs(difference) / standard_deviation if standard_deviation else 0.0
    elif payload.method == "RATE_OF_CHANGE":
        prior = payload.values[-1]
        measured = abs((payload.current_value - prior) / prior * 100) if prior else abs(difference)
    elif payload.method == "SEASONAL":
        seasonal = payload.values[-7:] if len(payload.values) >= 7 else payload.values
        baseline = fmean(seasonal)
        difference = payload.current_value - baseline
        measured = abs(difference) / standard_deviation if standard_deviation else 0.0
    else:
        measured = abs(difference)
    evidence = [
        {"fact": "current_value", "value": payload.current_value},
        {"fact": "historical_baseline", "value": round(baseline, 4)},
        {"fact": "rolling_average", "value": round(fmean(payload.values), 4)},
        {"fact": "rolling_standard_deviation", "value": round(standard_deviation, 4)},
        {"fact": "difference", "value": round(difference, 4)},
        {"fact": "threshold", "value": payload.threshold},
        {"fact": "duration_seconds", "value": payload.duration_seconds},
        {"fact": "measured_deviation", "value": round(measured, 4)},
    ]
    return baseline, difference, measured >= payload.threshold, evidence


class AnomalyService:
    def __init__(self, operations: OperationsRepository) -> None:
        self.operations = operations

    async def evaluate(self, payload: AnomalyEvaluationRequest) -> OperationalAnomaly:
        baseline, difference, anomalous, evidence = anomaly_values(payload)
        optical = payload.metric_name.lower() in {"rx_optical_power", "rx_power"} and difference < 0
        anomaly_type = (
            "OPTICAL_DEGRADATION_WARNING"
            if anomalous and optical
            else "TRAFFIC_ANOMALY"
            if anomalous
            else "NO_ANOMALY"
        )
        severity = "WARNING" if anomalous else "INFO"
        item = await self.operations.add_anomaly(
            OperationalAnomaly(
                entity_type=payload.entity_type.upper(),
                entity_id=payload.entity_id,
                metric_name=payload.metric_name,
                anomaly_type=anomaly_type,
                method=payload.method.value,
                current_value=payload.current_value,
                historical_baseline=baseline,
                difference=difference,
                threshold=payload.threshold,
                duration_seconds=payload.duration_seconds,
                severity=severity,
                evidence=evidence,
            )
        )
        await self.operations.commit()
        return item

    async def list(self, limit: int) -> list[OperationalAnomaly]:
        return await self.operations.list_anomalies(limit)


ALLOWED_TRANSITIONS = {
    "OPEN": {"ACKNOWLEDGED", "INVESTIGATING", "RESOLVED", "CLOSED"},
    "ACKNOWLEDGED": {"INVESTIGATING", "RESOLVED", "CLOSED"},
    "INVESTIGATING": {"RESOLVED", "CLOSED"},
    "RESOLVED": {"CLOSED", "OPEN"},
    "CLOSED": set(),
}


class IncidentService:
    def __init__(
        self,
        operations: OperationsRepository,
        audit: AuditService | None = None,
        notifications: NotificationService | None = None,
    ) -> None:
        self.operations = operations
        self.audit = audit
        self.notifications = notifications

    async def create_or_attach(
        self, payload: IncidentCreate, actor_user_id: UUID | None = None
    ) -> Incident:
        entity_type = payload.primary_entity.entity_type.upper()
        existing = await self.operations.find_active_incident(
            payload.category.upper(), entity_type, payload.primary_entity.entity_id
        )
        now = datetime.now(UTC)
        if existing is not None:
            existing.last_seen = now
            existing.evidence = [*existing.evidence, *payload.evidence]
            existing.affected_subscribers = sorted(
                set(existing.affected_subscribers) | set(payload.affected_subscribers)
            )
            await self._event(
                existing,
                "EVIDENCE_ATTACHED",
                "New evidence was attached to the existing incident.",
                actor_user_id,
                {"deduplicated": True},
            )
            await self.operations.commit()
            if self.notifications is not None:
                await self.notifications.dispatch(existing)
            return existing
        incident = await self.operations.add_incident(
            Incident(
                category=payload.category.upper(),
                severity=payload.severity,
                status="OPEN",
                title=payload.title,
                description=payload.description,
                first_seen=now,
                last_seen=now,
                root_cause=payload.root_cause,
                primary_entity_type=entity_type,
                primary_entity_id=payload.primary_entity.entity_id,
                affected_subscribers=payload.affected_subscribers,
                affected_topology=[item.model_dump() for item in payload.affected_topology],
                evidence=payload.evidence,
                recommendations=payload.recommendations,
                assigned_team=payload.assigned_team,
                comments=[],
            )
        )
        await self._event(
            incident,
            "INCIDENT_CREATED",
            "Incident created.",
            actor_user_id,
            {"category": incident.category, "severity": incident.severity},
        )
        await self._audit(incident, "created", actor_user_id)
        await self.operations.commit()
        if self.notifications is not None:
            await self.notifications.dispatch(incident)
        return incident

    async def update(
        self, incident_id: UUID, payload: IncidentUpdate, actor_user_id: UUID
    ) -> Incident:
        incident = await self.get(incident_id)
        changes: dict[str, Any] = {}
        if payload.status is not None and payload.status.value != incident.status:
            if payload.status.value not in ALLOWED_TRANSITIONS[incident.status]:
                raise AppError(
                    "INVALID_INCIDENT_TRANSITION",
                    "Incident status transition is invalid.",
                    422,
                )
            changes["status"] = {"from": incident.status, "to": payload.status.value}
            incident.status = payload.status.value
            if incident.status == "RESOLVED":
                incident.resolved_at = datetime.now(UTC)
            elif incident.status == "OPEN":
                incident.resolved_at = None
        for field in ("severity", "root_cause", "assigned_team", "assigned_user_id"):
            value = getattr(payload, field)
            if value is not None and value != getattr(incident, field):
                changes[field] = {"from": str(getattr(incident, field)), "to": str(value)}
                setattr(incident, field, value)
        if payload.comment is not None:
            incident.comments = [
                *incident.comments,
                {
                    "actor_user_id": str(actor_user_id),
                    "message": payload.comment,
                    "at": datetime.now(UTC).isoformat(),
                },
            ]
            changes["comment"] = payload.comment
        incident.last_seen = datetime.now(UTC)
        await self._event(
            incident,
            "INCIDENT_UPDATED",
            "Incident state or assignment changed.",
            actor_user_id,
            changes,
        )
        await self._audit(incident, "updated", actor_user_id)
        await self.operations.commit()
        return incident

    async def get(self, incident_id: UUID) -> Incident:
        incident = await self.operations.get_incident(incident_id)
        if incident is None:
            raise AppError("INCIDENT_NOT_FOUND", "Incident not found.", 404)
        return incident

    async def list_incidents(self, status: str | None, limit: int) -> list[Incident]:
        return await self.operations.list_incidents(status=status, limit=limit)

    async def timeline(self, incident_id: UUID) -> list[IncidentEvent]:
        await self.get(incident_id)
        return await self.operations.list_events(incident_id)

    async def _event(
        self,
        incident: Incident,
        event_type: str,
        message: str,
        actor_user_id: UUID | None,
        details: dict[str, Any],
    ) -> None:
        await self.operations.add_event(
            IncidentEvent(
                incident_id=incident.id,
                event_type=event_type,
                message=message,
                actor_user_id=actor_user_id,
                details=details,
            )
        )

    async def _audit(self, incident: Incident, action: str, actor_user_id: UUID | None) -> None:
        if self.audit is not None:
            await self.audit.record(
                AuditEventType.INCIDENT_ACTION,
                success=True,
                actor_user_id=actor_user_id,
                event_metadata={"incident_id": str(incident.id), "action": action},
            )


SEVERITY_RANK = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


class NotificationAdapter(Protocol):
    async def deliver(self, payload: dict[str, Any]) -> str: ...


class DashboardNotificationAdapter:
    async def deliver(self, payload: dict[str, Any]) -> str:
        return "DELIVERED"


class QueuedNotificationAdapter:
    async def deliver(self, payload: dict[str, Any]) -> str:
        return "QUEUED"


class NotificationService:
    def __init__(
        self, operations: OperationsRepository, audit: AuditService | None = None
    ) -> None:
        self.operations = operations
        self.audit = audit

    async def create_channel(
        self, payload: NotificationChannelCreate, actor_user_id: UUID
    ) -> NotificationChannel:
        try:
            item = await self.operations.add_channel(NotificationChannel(**payload.model_dump()))
            await self._audit("NotificationChannel", item.id, "created", actor_user_id)
            await self.operations.commit()
            return item
        except IntegrityError as exc:
            await self.operations.session.rollback()
            raise AppError(
                "NOTIFICATION_CHANNEL_CONFLICT",
                "Notification channel name already exists.",
                409,
            ) from exc

    async def list_channels(self) -> list[NotificationChannel]:
        return await self.operations.list_channels()

    async def create_rule(
        self, payload: NotificationRuleCreate, actor_user_id: UUID
    ) -> NotificationRule:
        for channel_id in payload.channel_ids:
            if await self.operations.get_channel(channel_id) is None:
                raise AppError(
                    "NOTIFICATION_CHANNEL_NOT_FOUND",
                    "Notification channel not found.",
                    404,
                )
        try:
            item = await self.operations.add_notification_rule(
                NotificationRule(
                    **payload.model_dump(exclude={"channel_ids"}),
                    channel_ids=[str(item) for item in payload.channel_ids],
                )
            )
            await self._audit("NotificationRule", item.id, "created", actor_user_id)
            await self.operations.commit()
            return item
        except IntegrityError as exc:
            await self.operations.session.rollback()
            raise AppError(
                "NOTIFICATION_RULE_CONFLICT",
                "Notification rule name already exists.",
                409,
            ) from exc

    async def list_rules(self) -> list[NotificationRule]:
        return await self.operations.list_notification_rules()

    async def dispatch(self, incident: Incident) -> list[NotificationDelivery]:
        rules = await self.operations.list_notification_rules()
        deliveries: list[NotificationDelivery] = []
        for rule in rules:
            if (
                not rule.enabled
                or rule.incident_category != incident.category
                or SEVERITY_RANK[incident.severity] < SEVERITY_RANK[rule.minimum_severity]
            ):
                continue
            for raw_channel_id in rule.channel_ids:
                channel = await self.operations.get_channel(UUID(raw_channel_id))
                if channel is None or not channel.enabled:
                    continue
                fingerprint = sha256(f"{incident.id}:{channel.id}".encode()).hexdigest()
                if await self.operations.delivery_exists(fingerprint):
                    continue
                payload = {
                    "incident_id": str(incident.id),
                    "title": incident.title,
                    "severity": incident.severity,
                    "category": incident.category,
                    "affected_subscribers": len(incident.affected_subscribers),
                    "teams": rule.teams,
                }
                adapter: NotificationAdapter = (
                    DashboardNotificationAdapter()
                    if channel.channel_type == "DASHBOARD"
                    else QueuedNotificationAdapter()
                )
                delivery = await self.operations.add_delivery(
                    NotificationDelivery(
                        incident_id=incident.id,
                        channel_id=channel.id,
                        fingerprint=fingerprint,
                        status=await adapter.deliver(payload),
                        payload=payload,
                    )
                )
                deliveries.append(delivery)
        await self.operations.commit()
        return deliveries

    async def _audit(
        self, resource_type: str, resource_id: UUID, action: str, actor_user_id: UUID
    ) -> None:
        if self.audit is not None:
            await self.audit.record(
                AuditEventType.CONFIGURATION_CHANGED,
                success=True,
                actor_user_id=actor_user_id,
                event_metadata={
                    "resource_type": resource_type,
                    "resource_id": str(resource_id),
                    "action": action,
                },
            )


def capacity_category(value: float, threshold: CapacityThreshold, duration: int) -> str:
    if duration < threshold.duration_seconds:
        return "NORMAL"
    if value >= threshold.critical_percent:
        return "CRITICAL"
    if value >= threshold.warning_percent:
        return "WARNING"
    if value >= threshold.informational_percent:
        return "INFORMATIONAL"
    return "NORMAL"


def linear_trend(payload: CapacityTrendRequest) -> tuple[float, datetime | None, int, list[str]]:
    ordered = sorted(payload.observations, key=lambda item: item[0])
    origin = ordered[0][0]
    x = [(observed_at - origin).total_seconds() / 86400 for observed_at, _ in ordered]
    y = [value for _, value in ordered]
    x_mean, y_mean = fmean(x), fmean(y)
    denominator = sum((value - x_mean) ** 2 for value in x)
    numerator = sum(
        (xv - x_mean) * (yv - y_mean)
        for xv, yv in zip(x, y, strict=True)
    )
    slope = numerator / denominator if denominator else 0.0
    intercept = y_mean - slope * x_mean
    projected: datetime | None = None
    if slope > 0:
        crossing_days = (payload.threshold_percent - intercept) / slope
        if crossing_days >= x[-1]:
            projected = origin + timedelta(days=crossing_days)
    window_days = max(1, round(x[-1] - x[0]))
    assumptions = [
        "Ordinary least-squares linear trend over the supplied observations.",
        "The recent growth rate is assumed to continue unchanged.",
        "The projection is an estimate, not a certainty.",
    ]
    return slope, projected, window_days, assumptions


class CapacityService:
    def __init__(
        self, operations: OperationsRepository, audit: AuditService | None = None
    ) -> None:
        self.operations = operations
        self.audit = audit

    async def create_threshold(
        self, data: dict[str, Any], actor_user_id: UUID
    ) -> CapacityThreshold:
        try:
            item = await self.operations.add_capacity_threshold(CapacityThreshold(**data))
            if self.audit is not None:
                await self.audit.record(
                    AuditEventType.THRESHOLD_CHANGED,
                    success=True,
                    actor_user_id=actor_user_id,
                    event_metadata={
                        "resource_type": "CapacityThreshold",
                        "resource_id": str(item.id),
                        "action": "created",
                    },
                )
            await self.operations.commit()
            return item
        except IntegrityError as exc:
            await self.operations.session.rollback()
            raise AppError(
                "CAPACITY_THRESHOLD_CONFLICT",
                "Capacity threshold name already exists.",
                409,
            ) from exc

    async def list_thresholds(self) -> list[CapacityThreshold]:
        return await self.operations.list_capacity_thresholds()

    async def list_assessments(self, limit: int) -> list[CapacityAssessment]:
        return await self.operations.list_capacity_assessments(limit)

    async def list_trends(self, limit: int) -> list[CapacityTrend]:
        return await self.operations.list_capacity_trends(limit)

    async def evaluate(self, payload: CapacityEvaluationRequest) -> CapacityAssessment:
        threshold = await self.operations.matching_capacity_threshold(
            payload.entity_type.upper(), payload.metric_name
        )
        if threshold is None:
            raise AppError("CAPACITY_THRESHOLD_NOT_FOUND", "Capacity threshold not found.", 404)
        sustained = fmean(payload.samples)
        category = capacity_category(sustained, threshold, payload.duration_seconds)
        item = await self.operations.add_capacity_assessment(
            CapacityAssessment(
                entity_type=payload.entity_type.upper(),
                entity_id=payload.entity_id,
                metric_name=payload.metric_name,
                current_percent=payload.samples[-1],
                sustained_percent=sustained,
                duration_seconds=payload.duration_seconds,
                category=category,
                evidence=[
                    {"fact": "sample_count", "value": len(payload.samples)},
                    {"fact": "sustained_average", "value": round(sustained, 4)},
                    {"fact": "required_duration_seconds", "value": threshold.duration_seconds},
                    {"fact": "thresholds", "value": {
                        "informational": threshold.informational_percent,
                        "warning": threshold.warning_percent,
                        "critical": threshold.critical_percent,
                    }},
                ],
            )
        )
        await self.operations.commit()
        return item

    async def trend(self, payload: CapacityTrendRequest) -> CapacityTrend:
        slope, projected, window_days, assumptions = linear_trend(payload)
        item = await self.operations.add_capacity_trend(
            CapacityTrend(
                entity_type=payload.entity_type.upper(),
                entity_id=payload.entity_id,
                metric_name=payload.metric_name,
                window_days=window_days,
                sample_count=len(payload.observations),
                slope_per_day=slope,
                threshold_percent=payload.threshold_percent,
                projected_crossing_at=projected,
                assumptions=assumptions,
            )
        )
        await self.operations.commit()
        return item
