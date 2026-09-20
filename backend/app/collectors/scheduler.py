import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import structlog

logger = structlog.get_logger()


@dataclass(frozen=True, slots=True)
class PollingIntervals:
    reachability: float = 30
    health: float = 60
    interfaces: float = 60
    optical: float = 180
    inventory: float = 1800


class CollectorScheduler:
    def __init__(self) -> None:
        self._tasks: set[asyncio.Task[None]] = set()

    def schedule(
        self,
        operation: Callable[[], Awaitable[None]],
        interval_seconds: float,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("Polling interval must be positive.")
        task = asyncio.create_task(self._run(operation, interval_seconds))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    def schedule_defaults(
        self,
        reachability: Callable[[], Awaitable[None]],
        health: Callable[[], Awaitable[None]],
        interfaces: Callable[[], Awaitable[None]],
        optical: Callable[[], Awaitable[None]],
        inventory: Callable[[], Awaitable[None]],
        intervals: PollingIntervals | None = None,
    ) -> None:
        values = intervals or PollingIntervals()
        self.schedule(reachability, values.reachability)
        self.schedule(health, values.health)
        self.schedule(interfaces, values.interfaces)
        self.schedule(optical, values.optical)
        self.schedule(inventory, values.inventory)

    async def _run(
        self,
        operation: Callable[[], Awaitable[None]],
        interval_seconds: float,
    ) -> None:
        while True:
            try:
                await operation()
            except Exception:
                logger.exception("collector_schedule_operation_failed")
            await asyncio.sleep(interval_seconds)

    async def shutdown(self) -> None:
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
