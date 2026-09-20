from uuid import uuid4

import pytest

from app.collectors.errors import CollectorConfigurationError, CollectorTransportError
from app.collectors.icmp import IcmpCollector
from app.collectors.reliability import FailureTracker
from app.collectors.runner import CollectorRunner
from app.collectors.status import StatusTracker
from app.collectors.registry import CollectorRegistry
from app.collectors.snmp import SnmpCollector, SnmpProfile
from app.collectors.worker_service import CollectorWorkerService
from app.collectors.snmp import SnmpCollector, SnmpProfile
from app.collectors.syslog import normalize_syslog


@pytest.mark.asyncio
async def test_icmp_collector_normalizes_reachability() -> None:
    collector = IcmpCollector(uuid4(), "192.0.2.1", lambda _ip: _latency())
    health = await collector.collect_device_health()
    assert health.reachable is True
    assert health.latency_ms == 4.2


async def _latency() -> float:
    return 4.2


@pytest.mark.asyncio
async def test_icmp_failure_is_transport_error() -> None:
    async def failed(_ip: str) -> float | None:
        return None

    with pytest.raises(CollectorTransportError):
        await IcmpCollector(uuid4(), "192.0.2.1", failed).collect_device_health()


def test_snmp_requires_v3_username() -> None:
    with pytest.raises(CollectorConfigurationError):
        SnmpCollector(uuid4(), SnmpProfile())


def test_syslog_normalization() -> None:
    event = normalize_syslog("<34> link down", "edge-1")
    assert event.facility == 4
    assert event.severity == 2
    assert event.message == "link down"
    assert normalize_syslog("<34> authentication failure", "edge-1").event_type == "security.authentication_failure"


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
    collector = registry.create("ICMP", device_id=uuid4(), management_ip="192.0.2.1", probe=lambda _ip: _latency())
    assert collector.collector_type == "ICMP"


@pytest.mark.asyncio
async def test_snmp_collects_interface_counters_and_environment() -> None:
    values = {"1.3.6.1.2.1.1.3.0": 120, "1.3.6.1.2.1.2.2.1.10.1": 10, "1.3.6.1.2.1.2.2.1.16.1": 20, "1.3.6.1.2.1.2.2.1.14.1": 1, "1.3.6.1.2.1.2.2.1.19.1": 2}
    async def query(oid: str) -> object | None: return values.get(oid, 55)
    collector = SnmpCollector(uuid4(), SnmpProfile(username="monitor"), query, [(1, "eth0")])
    interfaces = await collector.collect_interfaces()
    assert interfaces[0].in_octets == 10
    assert len(await collector.collect_environment()) == 5
    assert len(await collector.collect_optical_metrics()) == 2
    assert (await collector.collect_subscriber_sessions())[0]["active_sessions"] == 55


@pytest.mark.asyncio
async def test_snmp_table_walk_discovers_interfaces() -> None:
    async def query(oid: str) -> object | None:
        return 1
    async def walk(_oid: str) -> list[tuple[str, object]]:
        return [("1.3.6.1.2.1.2.2.1.2.7", "uplink")]
    collector = SnmpCollector(uuid4(), SnmpProfile(username="monitor"), query, walk=walk)
    assert (await collector.collect_interfaces())[0].name == "uplink"


@pytest.mark.asyncio
async def test_worker_service_executes_assignments() -> None:
    saved: list[str] = []
    async def persist(_device: object, collector_type: str, _status: object) -> None:
        saved.append(collector_type)
    def factory(device_id: object, collector_type: str) -> IcmpCollector:
        return IcmpCollector(device_id, "192.0.2.1", lambda _ip: _latency())  # type: ignore[arg-type]
    await CollectorWorkerService(persist).poll_assignments([(uuid4(), "ICMP")], factory)
    assert saved == ["ICMP"]
