from base64 import b64encode
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.errors import AppError
from app.models.enums import RoleName
from app.models.operations import Incident, NotificationChannel
from app.models.workflows import EscalationPolicy, FieldTask, MaintenanceWindow
from app.schemas.inventory import CollectorProfileResponse
from app.schemas.operations import IncidentCreate, NotificationChannelResponse
from app.schemas.topology import EntityReference
from app.schemas.workflows import (
    EscalationPolicyCreate,
    FieldPhotoCreate,
    FieldTaskAction,
    MaintenanceWindowCreate,
)
from app.services.operations import IncidentService
from app.services.workflows import (
    AnalyticsService,
    EscalationService,
    FieldTaskService,
    ReportService,
    SearchService,
)


class FakeAudit:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    async def record(self, event_type: object, **values: Any) -> None:
        self.events.append({"event_type": event_type, **values})


class FakeWorkflowRepository:
    def __init__(self) -> None:
        self.tasks: dict[Any, FieldTask] = {}
        self.photos: dict[Any, Any] = {}
        self.policies: list[EscalationPolicy] = []
        self.escalations: list[Any] = []
        self.incident_items: list[Incident] = []
        self.maintenance: MaintenanceWindow | None = None
        self.upstream: Incident | None = None
        self.session = SimpleNamespace(rollback=self._noop)

    async def _noop(self) -> None:
        return None

    async def add_task(self, item: FieldTask) -> FieldTask:
        now = datetime.now(UTC)
        item.id = uuid4()
        item.created_at = item.updated_at = now
        self.tasks[item.id] = item
        return item

    async def get_task(self, task_id: object) -> FieldTask | None:
        return self.tasks.get(task_id)

    async def list_tasks(self, technician_id: object = None) -> list[FieldTask]:
        return [
            item
            for item in self.tasks.values()
            if technician_id is None or item.assigned_technician_id == technician_id
        ]

    async def add_photo(self, item: Any) -> Any:
        item.id = uuid4()
        item.created_at = datetime.now(UTC)
        self.photos[item.id] = item
        return item

    async def get_photo(self, photo_id: object) -> Any:
        return self.photos.get(photo_id)

    async def commit(self) -> None:
        return None

    async def active_maintenance(self, *_args: object) -> MaintenanceWindow | None:
        return self.maintenance

    async def upstream_active_incident(self, *_args: object) -> Incident | None:
        return self.upstream

    async def list_policies(self) -> list[EscalationPolicy]:
        return self.policies

    async def incidents(self) -> list[Incident]:
        return self.incident_items

    async def escalation_exists(self, incident_id: Any, policy_id: Any, step: int) -> bool:
        return any(
            item.incident_id == incident_id
            and item.policy_id == policy_id
            and item.step_index == step
            for item in self.escalations
        )

    async def add_escalation(self, item: Any) -> Any:
        item.id = uuid4()
        item.escalated_at = datetime.now(UTC)
        self.escalations.append(item)
        return item


class FakeOperations:
    def __init__(self) -> None:
        self.incidents: dict[Any, Incident] = {}
        self.events: list[Any] = []
        self.channels: dict[Any, NotificationChannel] = {}
        self.deliveries: list[Any] = []

    async def get_incident(self, incident_id: object) -> Incident | None:
        return self.incidents.get(incident_id)

    async def find_active_incident(self, *_args: object) -> Incident | None:
        return None

    async def add_incident(self, item: Incident) -> Incident:
        item.id = uuid4()
        item.created_at = item.updated_at = datetime.now(UTC)
        self.incidents[item.id] = item
        return item

    async def add_event(self, item: Any) -> Any:
        item.id = uuid4()
        item.occurred_at = datetime.now(UTC)
        self.events.append(item)
        return item

    async def commit(self) -> None:
        return None

    async def get_channel(self, channel_id: object) -> NotificationChannel | None:
        return self.channels.get(channel_id)

    async def delivery_exists(self, fingerprint: str) -> bool:
        return any(item.fingerprint == fingerprint for item in self.deliveries)

    async def add_delivery(self, item: Any) -> Any:
        item.id = uuid4()
        item.created_at = datetime.now(UTC)
        self.deliveries.append(item)
        return item


def make_incident() -> Incident:
    now = datetime.now(UTC)
    return Incident(
        id=uuid4(),
        category="PON_OUTAGE",
        severity="CRITICAL",
        title="PON down",
        description="Shared outage",
        status="OPEN",
        primary_entity_type="PON",
        primary_entity_id="pon-1",
        affected_subscribers=[],
        affected_topology=[],
        evidence=[],
        first_seen=now,
        last_seen=now,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_field_task_lifecycle_is_ordered_and_technician_scoped() -> None:
    workflows = FakeWorkflowRepository()
    operations = FakeOperations()
    incident = make_incident()
    operations.incidents[incident.id] = incident
    technician_id = uuid4()
    task = await workflows.add_task(
        FieldTask(
            incident_id=incident.id,
            current_status="ASSIGNED",
            assigned_technician_id=technician_id,
            status="ASSIGNED",
            notes=[],
            recommended_checks=[],
        )
    )
    service = FieldTaskService(workflows, operations, FakeAudit())  # type: ignore[arg-type]

    with pytest.raises(AppError):
        await service.action(
            task.id,
            FieldTaskAction(action="START_WORK"),
            technician_id,
            RoleName.FIELD_TECHNICIAN.value,
        )
    with pytest.raises(AppError):
        await service.action(
            task.id,
            FieldTaskAction(action="ACCEPT"),
            uuid4(),
            RoleName.FIELD_TECHNICIAN.value,
        )
    for action, expected in [
        ("ACCEPT", "ACCEPTED"),
        ("START_WORK", "IN_PROGRESS"),
        ("MARK_RESTORED", "RESTORED"),
        ("CLOSE", "CLOSED"),
    ]:
        updated = await service.action(
            task.id,
            FieldTaskAction(action=action),  # type: ignore[arg-type]
            technician_id,
            RoleName.FIELD_TECHNICIAN.value,
        )
        assert updated.status == expected


@pytest.mark.asyncio
async def test_field_photo_rejects_invalid_or_oversized_content() -> None:
    workflows = FakeWorkflowRepository()
    operations = FakeOperations()
    task = await workflows.add_task(
        FieldTask(
            incident_id=uuid4(),
            current_status="ASSIGNED",
            assigned_technician_id=uuid4(),
            status="ASSIGNED",
            notes=[],
            recommended_checks=[],
        )
    )
    service = FieldTaskService(workflows, operations, FakeAudit())  # type: ignore[arg-type]
    for encoded in ("not-base64", b64encode(b"x" * (5 * 1024 * 1024 + 1)).decode()):
        with pytest.raises(AppError):
            await service.upload_photo(
                task.id,
                FieldPhotoCreate(
                    filename="evidence.png", content_type="image/png", content_base64=encoded
                ),
                task.assigned_technician_id,
                RoleName.FIELD_TECHNICIAN.value,
            )


@pytest.mark.asyncio
async def test_maintenance_and_dependency_suppression_modify_incident_creation() -> None:
    workflows = FakeWorkflowRepository()
    operations = FakeOperations()
    payload = IncidentCreate(
        category="DEVICE_FAILURE",
        severity="HIGH",
        title="Access device down",
        description="Device is unreachable",
        primary_entity=EntityReference(entity_type="DEVICE", entity_id=str(uuid4())),
        evidence=[{"fact": "reachable", "value": False}],
    )
    now = datetime.now(UTC)
    workflows.maintenance = MaintenanceWindow(
        id=uuid4(),
        scope_type="DEVICE",
        scope_id=payload.primary_entity.entity_id,
        starts_at=now - timedelta(minutes=5),
        ends_at=now + timedelta(minutes=5),
        reason="Planned replacement",
        created_by=uuid4(),
    )
    service = IncidentService(operations, workflows=workflows)  # type: ignore[arg-type]
    incident = await service.create_or_attach(payload)
    assert incident.category == "EXPECTED_MAINTENANCE"
    assert incident.evidence[-1]["reason"] == "Planned replacement"

    workflows.maintenance = None
    upstream = make_incident()
    operations.incidents[upstream.id] = upstream
    workflows.upstream = upstream
    attached = await service.create_or_attach(payload)
    assert attached is upstream
    assert operations.events[-1].event_type == "DEPENDENCY_EFFECT_ATTACHED"


def test_workflow_validation_and_secret_response_redaction() -> None:
    now = datetime.now(UTC)
    with pytest.raises(ValidationError):
        MaintenanceWindowCreate(
            scope_type="DEVICE", scope_id="x", starts_at=now, ends_at=now, reason="invalid"
        )
    with pytest.raises(ValidationError):
        EscalationPolicyCreate(
            name="critical",
            minimum_severity="CRITICAL",
            steps=[
                {"delay_minutes": 10, "team": "manager", "channel_ids": [uuid4()]},
                {"delay_minutes": 5, "team": "lead", "channel_ids": [uuid4()]},
            ],
        )
    with pytest.raises(ValidationError):
        FieldPhotoCreate(
            filename="../evidence.png", content_type="image/png", content_base64="eA=="
        )

    collector = CollectorProfileResponse.model_validate(
        {
            "id": uuid4(),
            "name": "snmp",
            "collector_type": "SNMP",
            "configuration_key": "secret-key-name",
            "interval_seconds": 60,
            "failure_threshold": 3,
        }
    )
    channel = NotificationChannelResponse.model_validate(
        {
            "id": uuid4(),
            "name": "sms",
            "channel_type": "SMS",
            "configuration_key": "provider-secret-name",
        }
    )
    assert collector.model_dump() == {
        "name": "snmp",
        "description": None,
        "enabled": True,
        "collector_type": "SNMP",
        "interval_seconds": 60,
        "failure_threshold": 3,
        "id": collector.id,
        "credential_configured": True,
    }
    assert "configuration_key" not in channel.model_dump()
    assert channel.credential_configured is True


@pytest.mark.asyncio
async def test_escalation_policy_rejects_unknown_channel() -> None:
    with pytest.raises(AppError) as caught:
        await EscalationService(
            FakeWorkflowRepository(),
            FakeOperations(),  # type: ignore[arg-type]
        ).create_policy(
            EscalationPolicyCreate(
                name="critical",
                minimum_severity="CRITICAL",
                steps=[{"delay_minutes": 5, "team": "lead", "channel_ids": [uuid4()]}],
            )
        )
    assert caught.value.code == "NOTIFICATION_CHANNEL_NOT_FOUND"


@pytest.mark.asyncio
async def test_escalation_evaluation_obeys_delay_and_deduplicates_delivery() -> None:
    workflows = FakeWorkflowRepository()
    operations = FakeOperations()
    channel = NotificationChannel(
        id=uuid4(), name="NOC dashboard", channel_type="DASHBOARD", enabled=True
    )
    operations.channels[channel.id] = channel
    incident = make_incident()
    incident.first_seen = datetime.now(UTC) - timedelta(minutes=10)
    workflows.incident_items = [incident]
    workflows.policies = [
        EscalationPolicy(
            id=uuid4(),
            name="critical",
            minimum_severity="CRITICAL",
            steps=[{"delay_minutes": 5, "team": "lead", "channel_ids": [str(channel.id)]}],
            enabled=True,
        )
    ]
    service = EscalationService(workflows, operations)  # type: ignore[arg-type]

    assert len(await service.evaluate()) == 1
    assert len(await service.evaluate()) == 0
    assert len(operations.deliveries) == 1
    assert operations.deliveries[0].payload["escalated_to"] == "lead"


class AnalyticsRepository:
    def __init__(self, incident: Incident) -> None:
        self.incident = incident

    async def incidents(self) -> list[Incident]:
        return [self.incident]

    async def incident_events(self) -> list[Any]:
        return []

    async def anomalies(self) -> list[Any]:
        return []

    async def capacity(self) -> list[Any]:
        return []

    async def availability_metrics(self) -> list[Any]:
        return [SimpleNamespace(entity_id="device-1", value=1.0)]

    async def olt_health(self) -> list[Any]:
        return []


@pytest.mark.asyncio
async def test_analytics_and_csv_reports_use_persisted_operational_data() -> None:
    incident = make_incident()
    repository = AnalyticsRepository(incident)
    analytics = AnalyticsService(repository)  # type: ignore[arg-type]
    result = await analytics.get()
    assert result.outages_by_month == [{"month": incident.first_seen.strftime("%Y-%m"), "count": 1}]
    assert result.device_availability == [
        {"device_id": "device-1", "availability_percent": 100.0}
    ]

    report = ReportService(repository, analytics, SimpleNamespace())  # type: ignore[arg-type]
    csv_content = await report.csv("monthly-incidents")
    assert csv_content.splitlines() == [
        "month,count",
        f"{incident.first_seen.strftime('%Y-%m')},1",
    ]
    with pytest.raises(AppError):
        await report.csv("unknown")


class SearchRepository:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def search_subscribers(self, _query: str, _limit: int) -> list[Any]:
        self.calls.append("subscribers")
        return [
            SimpleNamespace(
                subscriber_id="SUB-10001", current_ip="192.0.2.10", mac_address=None
            )
        ]

    async def search_fiber(self, _query: str, _limit: int) -> list[Any]:
        self.calls.append("fiber")
        return [("ONU", "onu-1", "ONU-1")]

    async def search_inventory(self, _query: str, _limit: int) -> list[Any]:
        self.calls.append("inventory")
        return [("DEVICE", "device-1", "Core router")]

    async def search_incidents(self, _query: str, _limit: int) -> list[Any]:
        self.calls.append("incidents")
        return [make_incident()]


@pytest.mark.asyncio
async def test_global_search_queries_only_permitted_resource_domains() -> None:
    repository = SearchRepository()
    service = SearchService(repository)  # type: ignore[arg-type]
    results = await service.search("core", {"inventory:read"}, 25)
    assert repository.calls == ["inventory"]
    assert [item.result_type for item in results] == ["DEVICE"]


def test_production_configuration_requires_database_tls() -> None:
    with pytest.raises(ValidationError):
        Settings(
            app_env="production",
            postgres_sslmode="disable",
            database_password="database-password",
            redis_password="redis-password",
        )
    settings = Settings(
        app_env="production",
        postgres_sslmode="verify-full",
        database_password="database-password",
        redis_password="redis-password",
    )
    assert settings.database_url.endswith("?ssl=verify-full")
