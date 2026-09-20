from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MetricEntityType(StrEnum):
    DEVICE = "DEVICE"
    INTERFACE = "INTERFACE"
    ONU = "ONU"
    SUBSCRIBER = "SUBSCRIBER"


class MetricResolution(StrEnum):
    RAW = "raw"
    FIVE_MINUTES = "5m"
    HOURLY = "1h"
    DAILY = "1d"


class MetricSampleCreate(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    entity_type: MetricEntityType
    entity_id: str = Field(min_length=1, max_length=255)
    metric_name: str = Field(min_length=1, max_length=80)
    value: float
    unit: str | None = Field(default=None, max_length=32)
    source: str = Field(min_length=1, max_length=64)
    tags: dict[str, str] = Field(default_factory=dict)


class MetricSampleResponse(MetricSampleCreate):
    model_config = ConfigDict(from_attributes=True)


class MetricAggregateResponse(BaseModel):
    bucket: datetime
    entity_type: MetricEntityType
    entity_id: str
    metric_name: str
    unit: str | None
    source: str
    tags: dict[str, str]
    value_avg: float
    value_min: float
    value_max: float
    value_sum: float
    sample_count: int


class MetricQuery(BaseModel):
    start: datetime
    end: datetime
    entity_type: MetricEntityType | None = None
    entity_id: Annotated[str | None, Field(max_length=255)] = None
    metric_name: Annotated[str | None, Field(max_length=80)] = None
    source: Annotated[str | None, Field(max_length=64)] = None
    resolution: MetricResolution = MetricResolution.RAW
    limit: Annotated[int, Field(ge=1, le=10_000)] = 1000

    @model_validator(mode="after")
    def validate_window(self) -> "MetricQuery":
        if self.end <= self.start:
            raise ValueError("end must be later than start")
        return self
