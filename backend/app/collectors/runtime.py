import json
import socket
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import UUID

import structlog
from sqlalchemy import select

from app.collectors.base import DeviceCollector
from app.collectors.errors import CollectorConfigurationError
from app.collectors.icmp import IcmpCollector, system_probe
from app.collectors.reliability import FailureTracker
from app.collectors.snmp import SnmpCollector, SnmpProfile
from app.collectors.snmp_transport import SnmpUdpTransport
from app.collectors.status import StatusTracker
from app.collectors.vendors.cisco import CiscoAdapter
from app.collectors.vendors.generic_snmp import GenericSnmpAdapter
from app.collectors.vendors.huawei import HuaweiAdapter
from app.collectors.vendors.mikrotik import MikrotikAdapter
from app.collectors.vendors.zte import ZteAdapter
from app.core.config import Settings, get_settings
from app.db.session import async_session_factory
from app.models.collector import CollectorStatusRecord
from app.models.inventory import CollectorAssignment, CollectorProfile, Device
from app.repositories.collector import CollectorStatusRepository

logger = structlog.get_logger()

ADAPTERS: dict[str, type[SnmpCollector]] = {
    "cisco": CiscoAdapter,
    "huawei": HuaweiAdapter,
    "mikrotik": MikrotikAdapter,
    "zte": ZteAdapter,
}


def build_collector(
    device: Device,
    profile: CollectorProfile,
    settings: Settings,
) -> DeviceCollector:
    if profile.collector_type == "ICMP":
        return IcmpCollector(
            device.id,
            device.management_ip,
            system_probe,
            attempts=settings.icmp_probe_attempts,
        )
    if profile.collector_type != "SNMP":
        raise CollectorConfigurationError("Unsupported collector type.")
    configurations = _load_profile_configurations(settings)
    if profile.configuration_key is None or profile.configuration_key not in configurations:
        raise CollectorConfigurationError("SNMP profile configuration is missing.")
    values = configurations[profile.configuration_key]
    version = _string(values, "version", "3")
    credential_field = "community" if version == "2c" else "username"
    snmp_profile = SnmpProfile(
        version=version,
        username=_string(values, credential_field),
        auth_protocol=_optional_string(values, "auth_protocol"),
        privacy_protocol=_optional_string(values, "privacy_protocol"),
        auth_secret=_optional_string(values, "auth_secret"),
        privacy_secret=_optional_string(values, "privacy_secret"),
        oid_overrides=_string_mapping(values, "oid_overrides"),
    )
    transport = SnmpUdpTransport(
        device.management_ip,
        snmp_profile,
        port=_integer(values, "port", 161),
        timeout_seconds=_number(values, "timeout_seconds", 2.0),
        retries=_integer(values, "retries", 1),
    )
    adapter = ADAPTERS.get((device.vendor or "").casefold(), GenericSnmpAdapter)
    return adapter(device.id, snmp_profile, transport.query, walk=transport.walk)


async def poll_assignment(assignment_id: UUID, worker: str | None = None) -> dict[str, str]:
    settings = get_settings()
    worker_name = worker or socket.gethostname()
    async with async_session_factory() as session:
        row = (
            await session.execute(
                select(CollectorAssignment, Device, CollectorProfile)
                .join(Device, Device.id == CollectorAssignment.device_id)
                .join(
                    CollectorProfile,
                    CollectorProfile.id == CollectorAssignment.collector_profile_id,
                )
                .where(CollectorAssignment.id == assignment_id)
            )
        ).one_or_none()
        if row is None:
            return {"assignment_id": str(assignment_id), "status": "missing"}
        assignment, device, profile = row
        if not assignment.enabled or not profile.enabled or not device.monitoring_enabled:
            return {"assignment_id": str(assignment_id), "status": "disabled"}
        existing = (
            await session.execute(
                select(CollectorStatusRecord).where(
                    CollectorStatusRecord.device_id == device.id,
                    CollectorStatusRecord.collector_type == profile.collector_type,
                )
            )
        ).scalar_one_or_none()
        status = _status_from_record(existing, profile.failure_threshold)
        try:
            collector = build_collector(device, profile, settings)
            health = await collector.collect_device_health()
            if not health.reachable:
                raise RuntimeError("Device is unreachable.")
            await collector.collect_interfaces()
            await collector.collect_optical_metrics()
            await collector.collect_environment()
            await collector.collect_subscriber_sessions()
            status.success(health.latency_ms)
            result = "success"
        except Exception as exc:
            status.failure()
            result = "failed"
            logger.warning(
                "collector_poll_failed",
                device_id=str(device.id),
                collector_type=profile.collector_type,
                error_type=type(exc).__name__,
            )
        await CollectorStatusRepository(session).save(
            device.id,
            profile.collector_type,
            worker_name,
            status,
        )
        await session.commit()
        return {"assignment_id": str(assignment_id), "status": result}


async def due_assignment_ids(now: datetime | None = None) -> list[UUID]:
    current = now or datetime.now(UTC)
    async with async_session_factory() as session:
        rows = (
            await session.execute(
                select(CollectorAssignment, CollectorProfile, Device, CollectorStatusRecord)
                .join(
                    CollectorProfile,
                    CollectorProfile.id == CollectorAssignment.collector_profile_id,
                )
                .join(Device, Device.id == CollectorAssignment.device_id)
                .outerjoin(
                    CollectorStatusRecord,
                    (CollectorStatusRecord.device_id == Device.id)
                    & (CollectorStatusRecord.collector_type == CollectorProfile.collector_type),
                )
                .where(
                    CollectorAssignment.enabled.is_(True),
                    CollectorProfile.enabled.is_(True),
                    Device.monitoring_enabled.is_(True),
                )
            )
        ).all()
    return [
        assignment.id
        for assignment, profile, _device, status in rows
        if status is None
        or status.updated_at <= current - timedelta(seconds=profile.interval_seconds)
    ]


def _load_profile_configurations(settings: Settings) -> dict[str, dict[str, Any]]:
    try:
        value = json.loads(settings.collector_profiles_json.get_secret_value())
    except json.JSONDecodeError as exc:
        raise CollectorConfigurationError("Collector profile configuration is invalid.") from exc
    if not isinstance(value, dict) or not all(
        isinstance(key, str) and isinstance(item, dict) for key, item in value.items()
    ):
        raise CollectorConfigurationError("Collector profile configuration is invalid.")
    return cast(dict[str, dict[str, Any]], value)


def _status_from_record(
    record: CollectorStatusRecord | None,
    threshold: int,
) -> StatusTracker:
    tracker = FailureTracker(threshold=threshold)
    if record is None:
        return StatusTracker(tracker)
    tracker.failures = record.failure_count
    return StatusTracker(
        tracker,
        last_successful_poll=record.last_successful_poll,
        last_failed_poll=record.last_failed_poll,
        latency_ms=record.latency_ms,
        health=record.current_health,
    )


def _string(values: dict[str, Any], key: str, default: str = "") -> str:
    value = values.get(key, default)
    if not isinstance(value, str):
        raise CollectorConfigurationError("Collector profile field has an invalid type.")
    return value


def _optional_string(values: dict[str, Any], key: str) -> str | None:
    value = values.get(key)
    if value is not None and not isinstance(value, str):
        raise CollectorConfigurationError("Collector profile field has an invalid type.")
    return value


def _integer(values: dict[str, Any], key: str, default: int) -> int:
    value = values.get(key, default)
    if not isinstance(value, int):
        raise CollectorConfigurationError("Collector profile field has an invalid type.")
    return value


def _number(values: dict[str, Any], key: str, default: float) -> float:
    value = values.get(key, default)
    if not isinstance(value, int | float):
        raise CollectorConfigurationError("Collector profile field has an invalid type.")
    return float(value)


def _string_mapping(values: dict[str, Any], key: str) -> dict[str, str]:
    value = values.get(key, {})
    if not isinstance(value, dict) or not all(
        isinstance(item_key, str) and isinstance(item_value, str)
        for item_key, item_value in value.items()
    ):
        raise CollectorConfigurationError("Collector profile field has an invalid type.")
    return cast(dict[str, str], value)
