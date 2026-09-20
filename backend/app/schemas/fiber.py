from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class OLTResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_id: UUID
    vendor: str
    model: str
    frame_count: int
    slot_information: dict[str, Any]
    uplinks: list[str]
    created_at: datetime
    updated_at: datetime


class PONResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    olt_id: UUID
    frame: int
    slot: int
    port: int
    technology: str
    status: str
    subscriber_count: int
    configured_capacity: int


class ONUResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    onu_identifier: str
    serial_number: str
    olt_id: UUID
    pon_id: UUID
    subscriber_id: str | None
    status: str
    last_seen: datetime | None
    registration_status: str
    rx_power: float | None
    tx_power: float | None
    temperature: float | None
    distance: float | None


class OpticalClassification(StrEnum):
    GOOD = "GOOD"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class OpticalMetricName(StrEnum):
    RX_POWER = "RX_POWER"
    TX_POWER = "TX_POWER"
    TEMPERATURE = "TEMPERATURE"
    DISTANCE = "DISTANCE"


class OpticalThresholdBase(BaseModel):
    vendor: str = Field(min_length=1, max_length=120)
    technology: str = Field(min_length=1, max_length=32)
    device_model: str | None = Field(default=None, max_length=120)
    metric_name: OpticalMetricName
    unit: str = Field(min_length=1, max_length=32)
    critical_low: float | None = None
    warning_low: float | None = None
    warning_high: float | None = None
    critical_high: float | None = None

    @field_validator("vendor", "technology", "unit")
    @classmethod
    def normalize_key(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("value must not be blank")
        return normalized

    @field_validator("device_model")
    @classmethod
    def normalize_model(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        return normalized or None

    @model_validator(mode="after")
    def validate_boundaries(self) -> "OpticalThresholdBase":
        boundaries = (
            self.critical_low,
            self.warning_low,
            self.warning_high,
            self.critical_high,
        )
        if all(value is None for value in boundaries):
            raise ValueError("at least one optical threshold boundary is required")
        if (
            self.critical_low is not None
            and self.warning_low is not None
            and self.critical_low > self.warning_low
        ):
            raise ValueError("critical_low must not exceed warning_low")
        if (
            self.warning_low is not None
            and self.warning_high is not None
            and self.warning_low >= self.warning_high
        ):
            raise ValueError("warning_low must be less than warning_high")
        if (
            self.warning_high is not None
            and self.critical_high is not None
            and self.warning_high > self.critical_high
        ):
            raise ValueError("warning_high must not exceed critical_high")
        return self


class OpticalThresholdCreate(OpticalThresholdBase):
    pass


class OpticalThresholdUpdate(BaseModel):
    vendor: str | None = Field(default=None, min_length=1, max_length=120)
    technology: str | None = Field(default=None, min_length=1, max_length=32)
    device_model: str | None = Field(default=None, max_length=120)
    metric_name: OpticalMetricName | None = None
    unit: str | None = Field(default=None, min_length=1, max_length=32)
    critical_low: float | None = None
    warning_low: float | None = None
    warning_high: float | None = None
    critical_high: float | None = None


class OpticalThresholdResponse(OpticalThresholdBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class ONUOpticalMetric(BaseModel):
    metric_name: str
    value: float | None
    unit: str
    classification: OpticalClassification


class ONUOpticalStatusResponse(BaseModel):
    onu_id: UUID
    observed_at: datetime | None
    metrics: list[ONUOpticalMetric]


class OpticalHistoryWindow(StrEnum):
    CURRENT = "current"
    HOURS_24 = "24h"
    DAYS_7 = "7d"
    DAYS_30 = "30d"


class OpticalHistoryPoint(BaseModel):
    timestamp: datetime
    metric_name: str
    value: float
    value_min: float
    value_max: float
    unit: str | None


class ONUOpticalHistoryResponse(BaseModel):
    onu_id: UUID
    window: OpticalHistoryWindow
    resolution: str
    points: list[OpticalHistoryPoint]
