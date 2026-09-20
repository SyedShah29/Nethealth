# ruff: noqa
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass(frozen=True, slots=True)
class DeviceHealth:
    device_id: UUID
    reachable: bool
    latency_ms: float | None
    packet_loss_percent: float | None
    uptime_seconds: int | None = None
    cpu_percent: float | None = None
    memory_percent: float | None = None

@dataclass(frozen=True, slots=True)
class InterfaceHealth:
    device_id: UUID
    name: str
    admin_status: str | None
    oper_status: str | None
    in_octets: int | None = None
    out_octets: int | None = None
    errors: int | None = None
    discards: int | None = None

@dataclass(frozen=True, slots=True)
class OpticalMetric:
    device_id: UUID
    interface_name: str
    metric: str
    value: float | None
    unit: str | None

@dataclass(frozen=True, slots=True)
class EnvironmentReading:
    device_id: UUID
    metric: str
    value: float | None
    unit: str | None

@dataclass(frozen=True, slots=True)
class SyslogEvent:
    device: str
    timestamp: datetime
    facility: int | None
    severity: int | None
    message: str
    event_type: str

@dataclass(frozen=True, slots=True)
class CollectorStatus:
    device_id: UUID
    collector_type: str
    last_successful_poll: datetime | None
    last_failed_poll: datetime | None
    failure_count: int
    latency_ms: float | None
    current_health: str
    current_worker: str | None
