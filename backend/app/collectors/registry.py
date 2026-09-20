# ruff: noqa
from collections.abc import Callable
from app.collectors.base import DeviceCollector
from app.collectors.scheduler import CollectorScheduler

CollectorFactory = Callable[..., DeviceCollector]

class CollectorRegistry:
    def __init__(self, scheduler: CollectorScheduler | None = None) -> None:
        self.scheduler = scheduler or CollectorScheduler()
        self._factories: dict[str, CollectorFactory] = {}
    def register(self, collector_type: str, factory: CollectorFactory) -> None:
        if not collector_type.strip(): raise ValueError("Collector type is required.")
        self._factories[collector_type.upper()] = factory
    def create(self, collector_type: str, **kwargs: object) -> DeviceCollector:
        try: factory = self._factories[collector_type.upper()]
        except KeyError as exc: raise ValueError("Collector type is not registered.") from exc
        return factory(**kwargs)
    def schedule(self, collector_type: str, operation: Callable[[], object], interval_seconds: float) -> None:
        async def run() -> None:
            result = operation()
            if hasattr(result, "__await__"): await result
        self.scheduler.schedule(run, interval_seconds)
