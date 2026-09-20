from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.api.dependencies.auth import get_current_user, get_metric_service
from app.collectors.schemas import (
    DeviceHealth,
    EnvironmentReading,
    InterfaceHealth,
    OpticalMetric,
)
from app.main import create_app
from app.models.enums import PermissionCode, RoleName
from app.models.inventory import Interface
from app.repositories.metrics import MetricRepository
from app.schemas.metrics import MetricEntityType, MetricQuery, MetricResolution
from app.services.metrics import MetricService
from tests.factories import make_role, make_user


class FakeMetricRepository:
    def __init__(self, previous: dict[str, Any] | None = None) -> None:
        self.previous = previous or {}
        self.saved: list[Any] = []

    async def add_many(self, samples: list[Any]) -> None:
        self.saved.extend(samples)

    async def latest_value(
        self,
        _entity_type: str,
        _entity_id: str,
        metric_name: str,
        _before: datetime,
    ) -> Any:
        return self.previous.get(metric_name)


def _service(repository: FakeMetricRepository) -> MetricService:
    return MetricService(cast(MetricRepository, repository))


async def test_collection_normalizes_all_phase_four_entity_metrics() -> None:
    now = datetime.now(UTC)
    interface = Interface(id=uuid4(), device_id=uuid4(), name="uplink", speed=1_000)
    repository = FakeMetricRepository(
        {
            "inbound_octets_total": SimpleNamespace(
                value=100, timestamp=now - timedelta(seconds=8)
            ),
            "outbound_octets_total": SimpleNamespace(
                value=200, timestamp=now - timedelta(seconds=8)
            ),
        }
    )
    service = _service(repository)

    samples = await service.persist_collection(
        timestamp=now,
        source="SNMP",
        health=DeviceHealth(uuid4(), True, 2.5, 0.0, 600, 20.0, 30.0),
        interfaces=[InterfaceHealth(interface.device_id, "uplink", "UP", "UP", 200, 300, 2, 3)],
        inventory_interfaces={"uplink": interface},
        optical=[
            OpticalMetric(
                interface.device_id,
                "pon-1/1",
                "rx_optical_power",
                -18.2,
                "dBm",
                entity_type="ONU",
                entity_id="ONU-001",
            )
        ],
        environment=[EnvironmentReading(interface.device_id, "temperature", 44.0, "celsius")],
        subscriber_sessions=[
            {
                "subscriber_id": "SUB-001",
                "session_state": "ONLINE",
                "session_uptime": 120,
                "download_rate": 500,
                "upload_rate": 50,
                "disconnect_events": 1,
            }
        ],
    )

    keys = {(sample.entity_type.value, sample.entity_id, sample.metric_name) for sample in samples}
    assert ("DEVICE", str(samples[0].entity_id), "cpu_percent") in keys
    assert ("INTERFACE", str(interface.id), "inbound_bps") in keys
    assert ("INTERFACE", str(interface.id), "inbound_utilization_percent") in keys
    assert ("ONU", "ONU-001", "rx_optical_power") in keys
    assert ("SUBSCRIBER", "SUB-001", "session_state") in keys
    assert repository.saved == samples


def test_metric_query_requires_forward_time_window() -> None:
    now = datetime.now(UTC)
    with pytest.raises(ValidationError):
        MetricQuery(start=now, end=now, resolution=MetricResolution.RAW)


def test_metric_entity_types_cover_roadmap_entities() -> None:
    assert {item.value for item in MetricEntityType} == {
        "DEVICE",
        "INTERFACE",
        "ONU",
        "SUBSCRIBER",
    }


class FakeMetricService:
    def __init__(self) -> None:
        self.query: MetricQuery | None = None

    async def execute(self, query: MetricQuery) -> list[Any]:
        self.query = query
        return []


async def test_metrics_api_requires_permission_and_accepts_bounded_query() -> None:
    app = create_app()
    service = FakeMetricService()
    user = make_user(
        role=make_role(
            RoleName.VIEWER,
            permissions=(PermissionCode.METRICS_READ,),
        )
    )
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_metric_service] = lambda: SimpleNamespace(
        query=service.execute
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/metrics",
            params={
                "start": "2026-09-20T00:00:00Z",
                "end": "2026-09-20T01:00:00Z",
                "entity_type": "DEVICE",
                "resolution": "5m",
            },
        )
    assert response.status_code == 200
    assert service.query is not None
    assert service.query.resolution == MetricResolution.FIVE_MINUTES


async def test_metrics_api_rejects_missing_authentication(client: AsyncClient) -> None:
    response = await client.get(
        "/api/metrics",
        params={
            "start": "2026-09-20T00:00:00Z",
            "end": "2026-09-20T01:00:00Z",
        },
    )
    assert response.status_code == 401
