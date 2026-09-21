from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest

from app.core.errors import AppError
from app.models.operations import CapacityThreshold, Incident, NotificationChannel, NotificationRule
from app.schemas.operations import (
    AnomalyEvaluationRequest,
    CapacityTrendRequest,
    HealthScoreRequest,
    IncidentCreate,
    IncidentUpdate,
)
from app.schemas.topology import EntityReference
from app.services.operations import (
    IncidentService,
    NotificationService,
    anomaly_values,
    calculate_health_score,
    capacity_category,
    linear_trend,
)


def test_health_score_is_configurable_bounded_and_explainable() -> None:
    payload = HealthScoreRequest(
        components={
            "optical_health": 50,
            "packet_loss": 75,
            "latency": 80,
            "disconnect_frequency": 40,
            "session_stability": 70,
            "bandwidth_performance": 70,
        }
    )
    score, category, components = calculate_health_score(payload)
    assert (score, category) == (62, "WARNING")
    assert sum(item["contribution"] for item in components) == pytest.approx(61.5)
    assert all({"component", "contribution", "maximum"} <= item.keys() for item in components)


@pytest.mark.parametrize(
    "method", ["ROLLING", "Z_SCORE", "EWMA", "RATE_OF_CHANGE", "BASELINE", "SEASONAL"]
)
def test_anomaly_methods_return_required_explanation(method: str) -> None:
    payload = AnomalyEvaluationRequest(
        entity_type="INTERFACE",
        entity_id="uplink-1",
        metric_name="utilization_percent",
        values=[10, 11, 9, 10, 10, 11, 9],
        current_value=40,
        method=method,  # type: ignore[arg-type]
        threshold=3,
        duration_seconds=600,
    )
    baseline, difference, anomalous, evidence = anomaly_values(payload)
    assert baseline >= 0
    assert difference > 0
    assert anomalous is True
    assert {item["fact"] for item in evidence} >= {
        "current_value",
        "historical_baseline",
        "rolling_average",
        "rolling_standard_deviation",
        "difference",
        "threshold",
        "duration_seconds",
    }


class FakeOperations:
    def __init__(self) -> None:
        self.incidents: list[Incident] = []
        self.events: list[Any] = []
        self.deliveries: list[Any] = []
        self.channels: dict[Any, NotificationChannel] = {}
        self.rules: list[NotificationRule] = []

    async def find_active_incident(
        self, category: str, entity_type: str, entity_id: str
    ) -> Incident | None:
        return next(
            (
                item
                for item in self.incidents
                if item.category == category
                and item.primary_entity_type == entity_type
                and item.primary_entity_id == entity_id
                and item.status in {"OPEN", "ACKNOWLEDGED", "INVESTIGATING"}
            ),
            None,
        )

    async def add_incident(self, item: Incident) -> Incident:
        item.id = uuid4()
        item.created_at = item.updated_at = datetime.now(UTC)
        self.incidents.append(item)
        return item

    async def add_event(self, event: Any) -> Any:
        event.id = uuid4()
        event.occurred_at = datetime.now(UTC)
        self.events.append(event)
        return event

    async def commit(self) -> None:
        return None

    async def get_incident(self, incident_id: object) -> Incident | None:
        return next((item for item in self.incidents if item.id == incident_id), None)

    async def list_incidents(self, *, status: str | None, limit: int) -> list[Incident]:
        return [item for item in self.incidents if status is None or item.status == status][:limit]

    async def list_events(self, incident_id: object) -> list[Any]:
        return [item for item in self.events if item.incident_id == incident_id]

    async def list_notification_rules(self) -> list[NotificationRule]:
        return self.rules

    async def get_channel(self, channel_id: object) -> NotificationChannel | None:
        return self.channels.get(channel_id)

    async def delivery_exists(self, fingerprint: str) -> bool:
        return any(item.fingerprint == fingerprint for item in self.deliveries)

    async def add_delivery(self, item: Any) -> Any:
        item.id = uuid4()
        self.deliveries.append(item)
        return item


@pytest.mark.asyncio
async def test_incidents_deduplicate_and_record_every_change_in_timeline() -> None:
    repository = FakeOperations()
    service = IncidentService(repository)  # type: ignore[arg-type]
    payload = IncidentCreate(
        category="PON_OUTAGE",
        severity="HIGH",
        title="PON outage",
        description="Multiple subscribers are offline.",
        primary_entity=EntityReference(entity_type="PON", entity_id="pon-7"),
        affected_subscribers=["SUB-1"],
        evidence=[{"fact": "pon_down", "value": True}],
    )
    first = await service.create_or_attach(payload)
    second = await service.create_or_attach(payload)
    assert first is second
    assert len(repository.incidents) == 1
    assert [item.event_type for item in repository.events] == [
        "INCIDENT_CREATED",
        "EVIDENCE_ATTACHED",
    ]
    await service.update(first.id, IncidentUpdate(status="ACKNOWLEDGED"), uuid4())
    assert first.status == "ACKNOWLEDGED"
    assert len(repository.events) == 3
    with pytest.raises(AppError):
        await service.update(first.id, IncidentUpdate(status="OPEN"), uuid4())


@pytest.mark.asyncio
async def test_notification_dispatch_aggregates_and_deduplicates_incident_alerts() -> None:
    repository = FakeOperations()
    channel = NotificationChannel(
        id=uuid4(), name="NOC dashboard", channel_type="DASHBOARD", enabled=True
    )
    repository.channels[channel.id] = channel
    repository.rules = [
        NotificationRule(
            id=uuid4(),
            name="PON routing",
            incident_category="PON_OUTAGE",
            minimum_severity="HIGH",
            teams=["NOC", "fiber"],
            channel_ids=[str(channel.id)],
            enabled=True,
        )
    ]
    service = NotificationService(repository)  # type: ignore[arg-type]
    incident = SimpleNamespace(
        id=uuid4(),
        title="PON outage",
        severity="HIGH",
        category="PON_OUTAGE",
        affected_subscribers=["SUB-1", "SUB-2"],
    )
    assert len(await service.dispatch(incident)) == 1  # type: ignore[arg-type]
    assert len(await service.dispatch(incident)) == 0  # type: ignore[arg-type]
    assert repository.deliveries[0].payload["affected_subscribers"] == 2  # type: ignore[attr-defined]


def test_capacity_requires_sustained_load_and_uses_configurable_thresholds() -> None:
    threshold = CapacityThreshold(
        name="uplink",
        entity_type="INTERFACE",
        metric_name="utilization_percent",
        informational_percent=70,
        warning_percent=80,
        critical_percent=90,
        duration_seconds=600,
        enabled=True,
    )
    assert capacity_category(95, threshold, 1) == "NORMAL"
    assert capacity_category(75, threshold, 600) == "INFORMATIONAL"
    assert capacity_category(85, threshold, 600) == "WARNING"
    assert capacity_category(95, threshold, 600) == "CRITICAL"


def test_capacity_trend_projects_crossing_and_discloses_assumptions() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    payload = CapacityTrendRequest(
        entity_type="INTERFACE",
        entity_id="uplink-1",
        metric_name="utilization_percent",
        observations=[
            (start, 50),
            (start + timedelta(days=30), 60),
            (start + timedelta(days=60), 70),
        ],
        threshold_percent=80,
    )
    slope, crossing, window_days, assumptions = linear_trend(payload)
    assert slope == pytest.approx(1 / 3)
    assert crossing == start + timedelta(days=90)
    assert window_days == 60
    assert any("not a certainty" in item for item in assumptions)
