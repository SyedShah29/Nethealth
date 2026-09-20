# ruff: noqa
from collections.abc import Awaitable, Callable
from uuid import UUID
from app.collectors.base import DeviceCollector
from app.collectors.runner import CollectorRunner
from app.collectors.status import StatusTracker
from app.collectors.reliability import FailureTracker

class AssignmentExecutor:
    def __init__(self, persist: Callable[[UUID, str, StatusTracker], Awaitable[None]]) -> None:
        self.persist = persist
    async def execute(self, device_id: UUID, collector: DeviceCollector) -> None:
        status = StatusTracker(FailureTracker(threshold=3))
        await CollectorRunner(collector, status, lambda s: self.persist(device_id, collector.collector_type, s)).poll()
