# ruff: noqa
from collections.abc import Awaitable, Callable
from app.collectors.base import DeviceCollector
from app.collectors.status import StatusTracker


class CollectorRunner:
    def __init__(
        self,
        collector: DeviceCollector,
        status: StatusTracker,
        persist: Callable[[StatusTracker], Awaitable[None]] | None = None,
    ) -> None:
        self.collector = collector
        self.status = status
        self.persist = persist

    async def poll(self) -> None:
        try:
            health = await self.collector.collect_device_health()
            if health.reachable:
                self.status.success(health.latency_ms)
            else:
                self.status.failure()
        except Exception:
            self.status.failure()
        if self.persist is not None:
            await self.persist(self.status)
