# ruff: noqa
from abc import ABC, abstractmethod
from uuid import UUID
from app.collectors.schemas import DeviceHealth, EnvironmentReading, InterfaceHealth, OpticalMetric


class DeviceCollector(ABC):
    """Common read-only contract implemented by protocol/vendor collectors."""

    collector_type: str

    def __init__(self, device_id: UUID) -> None:
        self.device_id = device_id

    @abstractmethod
    async def test_connection(self) -> bool: ...

    @abstractmethod
    async def collect_device_health(self) -> DeviceHealth: ...

    @abstractmethod
    async def collect_interfaces(self) -> list[InterfaceHealth]: ...

    async def collect_optical_metrics(self) -> list[OpticalMetric]:
        return []

    async def collect_subscriber_sessions(self) -> list[dict[str, object]]:
        return []

    async def collect_environment(self) -> list[EnvironmentReading]:
        return []
