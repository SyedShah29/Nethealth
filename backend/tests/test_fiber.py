from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from sqlalchemy import CheckConstraint, ForeignKeyConstraint

from app.api.dependencies.auth import get_current_user, get_fiber_service
from app.main import create_app
from app.models.enums import PermissionCode, RoleName
from app.models.fiber import OLT, ONU, PON, OpticalThreshold
from app.repositories.fiber import FiberRepository, OpticalThresholdRepository
from app.repositories.metrics import MetricRepository
from app.schemas.fiber import (
    OpticalClassification,
    OpticalHistoryWindow,
    OpticalThresholdCreate,
)
from app.schemas.metrics import MetricResolution
from app.services.audit import AuditService
from app.services.fiber import FiberService, OpticalThresholdService, classify
from tests.factories import make_role, make_user


def _fiber_records() -> tuple[OLT, PON, ONU]:
    olt_id = uuid4()
    pon_id = uuid4()
    now = datetime.now(UTC)
    olt = OLT(
        id=olt_id,
        device_id=uuid4(),
        vendor="Huawei",
        model="MA5800",
        frame_count=2,
        slot_information={"0": [1, 2]},
        uplinks=["XGigabitEthernet0/0/0"],
        created_at=now,
        updated_at=now,
    )
    pon = PON(
        id=pon_id,
        olt_id=olt_id,
        frame=0,
        slot=1,
        port=2,
        technology="GPON",
        status="UP",
        subscriber_count=1,
        configured_capacity=128,
    )
    onu = ONU(
        id=uuid4(),
        onu_identifier="ONU-001",
        serial_number="HWTC00000001",
        olt_id=olt_id,
        pon_id=pon_id,
        subscriber_id="SUB-10482",
        status="ONLINE",
        last_seen=now,
        registration_status="REGISTERED",
        rx_power=-18.0,
        tx_power=2.0,
        temperature=42.0,
        distance=750.0,
    )
    return olt, pon, onu


def _threshold(**values: Any) -> OpticalThreshold:
    defaults = {
        "id": uuid4(),
        "vendor": "HUAWEI",
        "technology": "GPON",
        "device_model": None,
        "metric_name": "RX_POWER",
        "unit": "DBM",
        "critical_low": -28.0,
        "warning_low": -24.0,
        "warning_high": None,
        "critical_high": None,
    }
    defaults.update(values)
    return OpticalThreshold(**defaults)


class FakeFiberRepository:
    def __init__(self, records: tuple[OLT, PON, ONU]) -> None:
        self.olt, self.pon, self.onu = records

    async def get_onu_context(self, _onu_id: UUID) -> tuple[ONU, PON, OLT]:
        return self.onu, self.pon, self.olt

    async def get_onu(self, _onu_id: UUID) -> ONU:
        return self.onu


class FakeThresholdRepository:
    def __init__(self, thresholds: list[OpticalThreshold]) -> None:
        self.thresholds = thresholds

    async def matching(self, **_kwargs: Any) -> list[OpticalThreshold]:
        return self.thresholds


class FakeMetricRepository:
    def __init__(self) -> None:
        self.query: Any = None

    async def query_aggregate(self, query: Any) -> list[dict[str, Any]]:
        self.query = query
        return [
            {
                "bucket": datetime.now(UTC),
                "metric_name": "rx_optical_power",
                "value_avg": -19.0,
                "value_min": -20.0,
                "value_max": -18.0,
                "unit": "dBm",
            },
            {
                "bucket": datetime.now(UTC),
                "metric_name": "online_state",
                "value_avg": 1.0,
                "value_min": 1.0,
                "value_max": 1.0,
                "unit": "state",
            },
        ]


def _service(
    records: tuple[OLT, PON, ONU],
    thresholds: list[OpticalThreshold] | None = None,
    metrics: FakeMetricRepository | None = None,
) -> FiberService:
    return FiberService(
        cast(FiberRepository, FakeFiberRepository(records)),
        cast(OpticalThresholdRepository, FakeThresholdRepository(thresholds or [])),
        cast(MetricRepository, metrics or FakeMetricRepository()),
    )


def test_optical_threshold_schema_requires_ordered_configurable_boundary() -> None:
    with pytest.raises(ValidationError):
        OpticalThresholdCreate(
            vendor="Huawei",
            technology="GPON",
            metric_name="rx_power",
            unit="dBm",
        )
    with pytest.raises(ValidationError):
        OpticalThresholdCreate(
            vendor="Huawei",
            technology="GPON",
            metric_name="rx_power",
            unit="dBm",
            critical_low=-20,
            warning_low=-25,
        )


def test_fiber_model_enforces_capacity_and_pon_olt_consistency() -> None:
    pon_checks = {
        str(constraint.sqltext)
        for constraint in PON.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }
    onu_foreign_keys = {
        constraint.name
        for constraint in ONU.__table__.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    }
    assert "subscriber_count <= configured_capacity" in pon_checks
    assert "configured_capacity > 0" in pon_checks
    assert "fk_onus_pon_olt" in onu_foreign_keys


def test_optical_classification_covers_all_roadmap_states() -> None:
    threshold = _threshold(warning_high=3.0, critical_high=5.0)
    assert classify(None, threshold) == OpticalClassification.UNKNOWN
    assert classify(-29, threshold) == OpticalClassification.CRITICAL
    assert classify(-25, threshold) == OpticalClassification.WARNING
    assert classify(-18, threshold) == OpticalClassification.GOOD


async def test_current_optical_status_uses_vendor_technology_thresholds() -> None:
    records = _fiber_records()
    status = await _service(records, [_threshold()]).optical_status(records[2].id)
    rx = next(metric for metric in status.metrics if metric.metric_name == "RX_POWER")
    temperature = next(
        metric for metric in status.metrics if metric.metric_name == "TEMPERATURE"
    )
    assert rx.classification == OpticalClassification.GOOD
    assert temperature.classification == OpticalClassification.UNKNOWN


async def test_optical_history_uses_window_downsampling_and_filters_state() -> None:
    records = _fiber_records()
    metrics = FakeMetricRepository()
    history = await _service(records, metrics=metrics).optical_history(
        records[2].id, OpticalHistoryWindow.DAYS_7
    )
    assert metrics.query.resolution == MetricResolution.HOURLY
    assert [point.metric_name for point in history.points] == ["rx_optical_power"]


async def test_current_optical_history_uses_onu_current_values() -> None:
    records = _fiber_records()
    history = await _service(records).optical_history(
        records[2].id, OpticalHistoryWindow.CURRENT
    )
    assert history.resolution == "current"
    assert {point.metric_name for point in history.points} == set(
        ("RX_POWER", "TX_POWER", "TEMPERATURE", "DISTANCE")
    )


async def test_fiber_api_enforces_rbac_and_returns_olts() -> None:
    olt, _pon, _onu = _fiber_records()
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: make_user(
        role=make_role(
            RoleName.NOC_ENGINEER,
            permissions=(PermissionCode.OPERATIONAL_READ,),
        )
    )
    app.dependency_overrides[get_fiber_service] = lambda: SimpleNamespace(
        list_olts=lambda: _async_result([olt])
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/olts")
    assert response.status_code == 200
    assert response.json()[0]["model"] == "MA5800"


async def test_fiber_api_rejects_missing_authentication(client: AsyncClient) -> None:
    assert (await client.get("/api/olts")).status_code == 401
    assert (await client.get("/api/pons")).status_code == 401
    assert (await client.get("/api/onus")).status_code == 401


class FakeSession:
    async def flush(self) -> None:
        pass

    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass


class FakeThresholdManagementRepository:
    def __init__(self) -> None:
        self.session = FakeSession()
        self.threshold: OpticalThreshold | None = None

    async def add(self, threshold: OpticalThreshold) -> OpticalThreshold:
        threshold.id = uuid4()
        self.threshold = threshold
        return threshold

    async def get(self, _threshold_id: UUID) -> OpticalThreshold | None:
        return self.threshold

    async def delete(self, _threshold: OpticalThreshold) -> None:
        self.threshold = None


class FakeAuditService:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    async def record(self, _event: Any, **values: Any) -> None:
        self.events.append(values)


async def test_optical_threshold_configuration_is_audited() -> None:
    repository = FakeThresholdManagementRepository()
    audit = FakeAuditService()
    service = OpticalThresholdService(
        cast(OpticalThresholdRepository, repository),
        cast(AuditService, audit),
    )
    created = await service.create(
        OpticalThresholdCreate(
            vendor="Huawei",
            technology="GPON",
            metric_name="RX_POWER",
            unit="dBm",
            critical_low=-28,
            warning_low=-24,
        ),
        uuid4(),
    )
    assert created.vendor == "HUAWEI"
    assert audit.events[0]["event_metadata"]["action"] == "created"
    await service.delete(created.id, uuid4())
    assert repository.threshold is None
    assert audit.events[-1]["event_metadata"]["action"] == "deleted"


async def _async_result(value: Any) -> Any:
    return value
