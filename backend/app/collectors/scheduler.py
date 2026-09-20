# ruff: noqa
from collections.abc import Awaitable, Callable
import asyncio

class CollectorScheduler:
    def __init__(self) -> None: self._tasks: set[asyncio.Task[None]] = set()
    def schedule(self, operation: Callable[[], Awaitable[None]], interval_seconds: float) -> None:
        if interval_seconds <= 0: raise ValueError("Polling interval must be positive.")
        task = asyncio.create_task(self._run(operation, interval_seconds)); self._tasks.add(task); task.add_done_callback(self._tasks.discard)

    def schedule_defaults(self, reachability: Callable[[], Awaitable[None]], health: Callable[[], Awaitable[None]], interfaces: Callable[[], Awaitable[None]], inventory: Callable[[], Awaitable[None]]) -> None:
        self.schedule(reachability, 30); self.schedule(health, 60); self.schedule(interfaces, 60); self.schedule(inventory, 1800)
    async def _run(self, operation: Callable[[], Awaitable[None]], interval_seconds: float) -> None:
        while True:
            try: await operation()
            except Exception: pass
            await asyncio.sleep(interval_seconds)
    async def shutdown(self) -> None:
        for task in self._tasks: task.cancel()
        if self._tasks: await asyncio.gather(*self._tasks, return_exceptions=True)
