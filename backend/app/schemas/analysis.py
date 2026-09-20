from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.topology import EntityReference


class ConfidenceLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CONFIRMED = "CONFIRMED"


class FaultObservation(EntityReference):
    observed_at: datetime
    evidence: dict[str, Any] = Field(default_factory=dict)


class CorrelationRequest(BaseModel):
    observations: list[FaultObservation] = Field(min_length=1, max_length=5000)
    window_seconds: int | None = Field(default=None, ge=30, le=120)

    @model_validator(mode="after")
    def validate_observation_window(self) -> "CorrelationRequest":
        if len(self.observations) > 1:
            timestamps = [item.observed_at for item in self.observations]
            if max(timestamps) < min(timestamps):
                raise ValueError("observation timestamps are invalid")
        return self


class CorrelationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    window_started_at: datetime
    window_ended_at: datetime
    window_seconds: int
    common_ancestor_node_id: UUID | None
    classification: str
    confidence: ConfidenceLevel
    affected_count: int
    affected_entities: list[EntityReference]
    evidence: list[dict[str, Any]]
    created_at: datetime


class RootCauseRequest(BaseModel):
    correlation_id: UUID | None = None
    signals: dict[str, bool | float | int | str] = Field(default_factory=dict)
    affected_entities: list[EntityReference] = Field(min_length=1, max_length=5000)


class RootCauseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    correlation_id: UUID | None
    classification: str
    severity: str
    evidence: list[dict[str, Any]]
    affected_entities: list[EntityReference]
    recommended_checks: list[str]
    created_at: datetime
