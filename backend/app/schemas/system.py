from typing import Any

from pydantic import BaseModel


class PlatformHealthResponse(BaseModel):
    status: str
    collector_health: dict[str, int]
    worker: dict[str, Any]
    queue_depth: int
    database_latency_ms: float
    api: dict[str, float | int]
    failed_polls: int
    metrics_ingestion_per_minute: float
    disk: dict[str, int | float]
    database_size_bytes: int
    notification_failures: int
