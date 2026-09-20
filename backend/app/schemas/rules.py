from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RuleSeverity(StrEnum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RuleOperator(StrEnum):
    GT = "GT"
    GTE = "GTE"
    LT = "LT"
    LTE = "LTE"
    EQ = "EQ"
    NE = "NE"


class RuleCondition(BaseModel):
    signal: str = Field(min_length=1, max_length=120)
    operator: RuleOperator
    value: bool | float | str


class RuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=1000)
    entity_type: str = Field(min_length=1, max_length=32)
    conditions: list[RuleCondition] = Field(min_length=1, max_length=20)
    duration_seconds: int = Field(default=0, ge=0, le=86400)
    severity: RuleSeverity
    incident_category: str = Field(min_length=1, max_length=80)
    recommendation: str = Field(min_length=1, max_length=1000)
    enabled: bool = True

    @field_validator("entity_type", "incident_category")
    @classmethod
    def normalize_identifier(cls, value: str) -> str:
        return value.strip().upper()


class RuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, min_length=1, max_length=1000)
    entity_type: str | None = Field(default=None, min_length=1, max_length=32)
    conditions: list[RuleCondition] | None = Field(default=None, min_length=1, max_length=20)
    duration_seconds: int | None = Field(default=None, ge=0, le=86400)
    severity: RuleSeverity | None = None
    incident_category: str | None = Field(default=None, min_length=1, max_length=80)
    recommendation: str | None = Field(default=None, min_length=1, max_length=1000)
    enabled: bool | None = None

    @field_validator("entity_type", "incident_category")
    @classmethod
    def normalize_optional_identifier(cls, value: str | None) -> str | None:
        return value.strip().upper() if value is not None else None


class RuleResponse(RuleCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class RuleEvaluationRequest(BaseModel):
    entity_type: str = Field(min_length=1, max_length=32)
    entity_id: str = Field(min_length=1, max_length=255)
    signals: dict[str, bool | float | str]
    observed_duration_seconds: int = Field(default=0, ge=0, le=86400)


class RuleEvidence(BaseModel):
    signal: str
    operator: str
    expected: bool | float | str
    actual: bool | float | str | None
    matched: bool


class RuleEvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rule_id: UUID
    entity_type: str
    entity_id: str
    evaluated_at: datetime
    result: bool
    evidence: list[RuleEvidence]
    trigger_state: str


RuleConditionData = dict[str, Any]
