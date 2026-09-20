from uuid import uuid4

import pytest

from app.collectors.errors import CollectorConfigurationError
from app.collectors.icmp import IcmpCollector
from app.collectors.registry import CollectorRegistry
from app.collectors.reliability import FailureTracker
from app.collectors.runner import CollectorRunner
from app.collectors.scheduler import CollectorScheduler, PollingIntervals
from app.collectors.snmp import SnmpCollector, SnmpProfile
from app.collectors.status import StatusTracker
from app.collectors.syslog import normalize_syslog
from app.collectors.vendors.cisco import CiscoAdapter
from app.collectors.worker_service import CollectorWorkerService


async def _latency() -> float:
    return 4.2


@pytest.mark.asyncio
async def test_icmp_collector_normalizes_reachability() -> None:
    collector = IcmpCollector(uuid4(), "192.0.2.1", lambda _ip: _latency())
    health = await collector.collect_device_health()
    assert health.reachable is True
    assert health.latency_ms == 4.2
    assert health.packet_loss_percent == 0


@pytest.mark.asyncio
async def test_icmp_collector_measures_packet_loss() -> None:
    results: list[float | None] = [4.0, None, 8.0]

    async def probe(_ip: str) -> float | None:
        return results.pop(0)

    health = await IcmpCollector(uuid4(), "192.0.2.1", probe).collect_device_health()
    assert health.reachable is True
    assert health.latency_ms == 6
    assert health.packet_loss_percent == pytest.approx(100 / 3)


@pytest.mark.asyncio
async def test_icmp_failure_returns_unreachable_health() -> None:
    async def failed(_ip: str) -> float | None:
        return None

    health = await IcmpCollector(uuid4(), "192.0.2.1", failed).collect_device_health()
    assert health.reachable is False
    assert health.latency_ms is None
    assert health.packet_loss_percent == 100


def test_snmp_requires_v3_username() -> None:
    with pytest.raises(CollectorConfigurationError):
        SnmpCollector(uuid4(), SnmpProfile())


def test_syslog_normalization() -> None:
    event = normalize_syslog("<34> link down", "edge-1")
    assert event.facility == 4
    assert event.severity == 2
    assert event.message == "link down"
    auth_event = normalize_syslog("<34> authentication failure", "edge-1")
    assert auth_event.event_type == "security.authentication_failure"


def test_failure_threshold_requires_consecutive_failures() -> None:
    tracker = FailureTracker(threshold=3)
    assert tracker.record_failure() is False
    assert tracker.record_failure() is False
    assert tracker.record_failure() is True
    tracker.record_success()
    assert tracker.failures == 0


@pytest.mark.asyncio
async def test_runner_persists_success_status() -> None:
    collector = IcmpCollector(uuid4(), "192.0.2.1", lambda _ip: _latency())
    status = StatusTracker(FailureTracker())
    saved = False

    async def persist(_status: StatusTracker) -> None:
        nonlocal saved
        saved = True

    await CollectorRunner(collector, status, persist).poll()
    assert saved is True
    assert status.health == "HEALTHY"


def test_registry_registers_and_creates_collectors() -> None:
    registry = CollectorRegistry()
    registry.register("icmp", IcmpCollector)
    collector = registry.create(
        "ICMP",
        device_id=uuid4(),
        management_ip="192.0.2.1",
        probe=lambda _ip: _latency(),
    )
    assert collector.collector_type == "ICMP"


@pytest.mark.asyncio
async def test_snmp_collects_health_interface_counters_and_environment() -> None:
    values = {
        "1.3.6.1.2.1.1.3.0": 12000,
        "1.3.6.1.4.1.2021.11.9.0": 12,
        "1.3.6.1.4.1.2021.4.5.0": 100,
        "1.3.6.1.4.1.2021.4.6.0": 33,
        "1.3.6.1.2.1.2.2.1.7.1": 1,
        "1.3.6.1.2.1.2.2.1.8.1": 2,
        "1.3.6.1.2.1.2.2.1.10.1": 10,
        "1.3.6.1.2.1.2.2.1.16.1": 20,
        "1.3.6.1.2.1.2.2.1.14.1": 1,
        "1.3.6.1.2.1.2.2.1.20.1": 2,
        "1.3.6.1.2.1.2.2.1.13.1": 3,
        "1.3.6.1.2.1.2.2.1.19.1": 4,
    }

    async def query(oid: str) -> object | None:
        return values.get(oid, 55)

    collector = SnmpCollector(
        uuid4(), SnmpProfile(username="monitor"), query, [(1, "eth0")]
    )
    health = await collector.collect_device_health()
    interfaces = await collector.collect_interfaces()
    assert health.uptime_seconds == 120
    assert health.cpu_percent == 12
    assert health.memory_percent == 67
    assert interfaces[0].admin_status == "UP"
    assert interfaces[0].oper_status == "DOWN"
    assert interfaces[0].in_octets == 10
    assert interfaces[0].errors == 3
    assert interfaces[0].discards == 7
    assert len(await collector.collect_environment()) == 3
    assert await collector.collect_optical_metrics() == []
    assert await collector.collect_subscriber_sessions() == []


@pytest.mark.asyncio
async def test_vendor_oid_overrides_drive_optical_and_subscriber_collection() -> None:
    queried: list[str] = []

    async def query(oid: str) -> object | None:
        queried.append(oid)
        return 7

    collector = CiscoAdapter(
        uuid4(), SnmpProfile(username="monitor"), query, [(5, "Gi0/1")]
    )
    optical = await collector.collect_optical_metrics()
    sessions = await collector.collect_subscriber_sessions()
    assert len(optical) == 2
    assert optical[0].interface_name == "Gi0/1"
    assert any(oid.endswith(".5") for oid in queried)
    assert sessions[0]["active_sessions"] == 7


@pytest.mark.asyncio
async def test_snmp_table_walk_discovers_interfaces() -> None:
    async def query(_oid: str) -> object | None:
        return 1

    async def walk(_oid: str) -> list[tuple[str, object]]:
        return [("1.3.6.1.2.1.2.2.1.2.7", "uplink")]

    collector = SnmpCollector(uuid4(), SnmpProfile(username="monitor"), query, walk=walk)
    assert (await collector.collect_interfaces())[0].name == "uplink"


@pytest.mark.asyncio
async def test_configured_onu_and_subscriber_tables_are_normalized() -> None:
    onu_id_oid = "1.2.3.1"
    subscriber_id_oid = "1.2.4.1"

    async def query(oid: str) -> object | None:
        return {
            "1.2.3.2.7": -19.5,
            "1.2.3.3.7": 1,
            "1.2.4.2.9": 1,
            "1.2.4.3.9": 600,
        }.get(oid)

    async def walk(oid: str) -> list[tuple[str, object]]:
        if oid == onu_id_oid:
            return [(f"{onu_id_oid}.7", "ONU-007")]
        if oid == subscriber_id_oid:
            return [(f"{subscriber_id_oid}.9", "SUB-009")]
        return []

    collector = SnmpCollector(
        uuid4(),
        SnmpProfile(
            username="monitor",
            oid_overrides={
                "onu_identifier": onu_id_oid,
                "onu_rx_power": "1.2.3.2",
                "onu_status": "1.2.3.3",
                "subscriber_identifier": subscriber_id_oid,
                "subscriber_session_state": "1.2.4.2",
                "subscriber_session_uptime": "1.2.4.3",
            },
        ),
        query,
        walk=walk,
    )

    optical = await collector.collect_optical_metrics()
    sessions = await collector.collect_subscriber_sessions()
    assert {(item.metric, item.entity_id) for item in optical} == {
        ("rx_optical_power", "ONU-007"),
        ("online_state", "ONU-007"),
    }
    assert sessions == [
        {"subscriber_id": "SUB-009", "session_state": 1, "session_uptime": 600}
    ]


@pytest.mark.asyncio
async def test_worker_service_executes_assignments() -> None:
    saved: list[str] = []

    async def persist(_device: object, collector_type: str, _status: object) -> None:
        saved.append(collector_type)

    def factory(device_id: object, _collector_type: str) -> IcmpCollector:
        return IcmpCollector(  # type: ignore[arg-type]
            device_id, "192.0.2.1", lambda _ip: _latency()
        )

    await CollectorWorkerService(persist).poll_assignments([(uuid4(), "ICMP")], factory)
    assert saved == ["ICMP"]


def test_scheduler_includes_optical_default(monkeypatch: pytest.MonkeyPatch) -> None:
    scheduler = CollectorScheduler()
    intervals: list[float] = []

    def capture(_operation: object, interval: float) -> None:
        intervals.append(interval)

    monkeypatch.setattr(scheduler, "schedule", capture)

    async def operation() -> None:
        return None

    scheduler.schedule_defaults(
        operation,
        operation,
        operation,
        operation,
        operation,
        PollingIntervals(),
    )
    assert intervals == [30, 60, 60, 180, 1800]
