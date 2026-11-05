# ruff: noqa
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class CollectorStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    device_id: UUID
    collector_type: str
    last_successful_poll: datetime | None
    last_failed_poll: datetime | None
    failure_count: int
    latency_ms: float | None
    current_health: str
    current_worker: str | None
    updated_at: datetime
