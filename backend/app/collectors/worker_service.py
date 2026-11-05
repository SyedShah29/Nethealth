# ruff: noqa
from collections.abc import Awaitable, Callable
from uuid import UUID
from app.collectors.base import DeviceCollector
from app.collectors.execution import AssignmentExecutor
from app.collectors.status import StatusTracker

CollectorFactory = Callable[[UUID, str], DeviceCollector]


class CollectorWorkerService:
    def __init__(self, persist: Callable[[UUID, str, StatusTracker], Awaitable[None]]) -> None:
        self.executor = AssignmentExecutor(persist)

    async def poll_assignment(
        self, device_id: UUID, collector_type: str, factory: CollectorFactory
    ) -> None:
        collector = factory(device_id, collector_type)
        await self.executor.execute(device_id, collector)

    async def poll_assignments(
        self, assignments: list[tuple[UUID, str]], factory: CollectorFactory
    ) -> None:
        for device_id, collector_type in assignments:
            await self.poll_assignment(device_id, collector_type, factory)
