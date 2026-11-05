from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from app.schemas.topology import EntityReference


class HealthCategory(StrEnum):
    HEALTHY = "HEALTHY"
    GOOD = "GOOD"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class HealthScoreRequest(BaseModel):
    components: dict[str, float] = Field(min_length=6, max_length=6)
    weights: dict[str, int] = Field(
        default_factory=lambda: {
            "optical_health": 25,
            "packet_loss": 20,
            "latency": 15,
            "disconnect_frequency": 20,
            "session_stability": 10,
            "bandwidth_performance": 10,
        }
    )
    thresholds: dict[str, int] = Field(
        default_factory=lambda: {
            "healthy": 90,
            "good": 75,
            "warning": 50,
        }
    )

    @model_validator(mode="after")
    def validate_configuration(self) -> "HealthScoreRequest":
        expected = {
            "optical_health",
            "packet_loss",
            "latency",
            "disconnect_frequency",
            "session_stability",
            "bandwidth_performance",
        }
        if set(self.components) != expected or set(self.weights) != expected:
            raise ValueError("all six health components and weights are required")
        if any(value < 0 or value > 100 for value in self.components.values()):
            raise ValueError("component health values must be between 0 and 100")
        if sum(self.weights.values()) != 100 or any(value < 0 for value in self.weights.values()):
            raise ValueError("health weights must be non-negative and total 100")
        healthy = self.thresholds.get("healthy")
        good = self.thresholds.get("good")
        warning = self.thresholds.get("warning")
        if None in {healthy, good, warning} or not 0 <= warning < good < healthy <= 100:  # type: ignore[operator]
            raise ValueError("health thresholds must be ordered from warning to healthy")
        return self


class HealthScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    subscriber_id: str
    score: int
    category: HealthCategory
    components: list[dict[str, Any]]
    weights: dict[str, int]
    thresholds: dict[str, int]
    evaluated_at: datetime


class AnomalyMethod(StrEnum):
    ROLLING = "ROLLING"
    Z_SCORE = "Z_SCORE"
    EWMA = "EWMA"
    RATE_OF_CHANGE = "RATE_OF_CHANGE"
    BASELINE = "BASELINE"
    SEASONAL = "SEASONAL"


class AnomalyEvaluationRequest(BaseModel):
    entity_type: str = Field(min_length=1, max_length=32)
    entity_id: str = Field(min_length=1, max_length=255)
    metric_name: str = Field(min_length=1, max_length=80)
    values: list[float] = Field(min_length=3, max_length=10_000)
    current_value: float
    method: AnomalyMethod = AnomalyMethod.Z_SCORE
    threshold: float = Field(default=3, gt=0)
    duration_seconds: int = Field(default=0, ge=0)


class AnomalyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    entity_type: str
    entity_id: str
    metric_name: str
    anomaly_type: str
    method: str
    current_value: float
    historical_baseline: float
    difference: float
    threshold: float
    duration_seconds: int
    severity: str
    evidence: list[dict[str, Any]]
    detected_at: datetime


class IncidentStatus(StrEnum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class IncidentCreate(BaseModel):
    category: str = Field(min_length=1, max_length=80)
    severity: str = Field(pattern="^(INFO|LOW|MEDIUM|HIGH|CRITICAL)$")
    title: str = Field(min_length=1, max_length=240)
    description: str = Field(min_length=1, max_length=2000)
    primary_entity: EntityReference
    affected_subscribers: list[str] = Field(default_factory=list, max_length=10_000)
    affected_topology: list[EntityReference] = Field(default_factory=list, max_length=10_000)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    root_cause: str | None = Field(default=None, max_length=160)
    assigned_team: str | None = Field(default=None, max_length=120)


class IncidentUpdate(BaseModel):
    status: IncidentStatus | None = None
    severity: str | None = Field(default=None, pattern="^(INFO|LOW|MEDIUM|HIGH|CRITICAL)$")
    root_cause: str | None = Field(default=None, max_length=160)
    assigned_team: str | None = Field(default=None, max_length=120)
    assigned_user_id: UUID | None = None
    comment: str | None = Field(default=None, min_length=1, max_length=1000)


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    category: str
    severity: str
    status: IncidentStatus
    title: str
    description: str
    first_seen: datetime
    last_seen: datetime
    resolved_at: datetime | None
    root_cause: str | None
    primary_entity_type: str
    primary_entity_id: str
    affected_subscribers: list[str]
    affected_topology: list[dict[str, str]]
    evidence: list[dict[str, Any]]
    recommendations: list[str]
    assigned_team: str | None
    assigned_user_id: UUID | None
    comments: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class IncidentEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    incident_id: UUID
    event_type: str
    message: str
    actor_user_id: UUID | None
    details: dict[str, Any]
    occurred_at: datetime


class NotificationChannelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    channel_type: str = Field(pattern="^(EMAIL|SMS|WHATSAPP|TELEGRAM|DASHBOARD|WEB_PUSH)$")
    configuration_key: str | None = Field(default=None, max_length=120)
    enabled: bool = True


class NotificationChannelResponse(NotificationChannelCreate):
    model_config = ConfigDict(from_attributes=True)
    configuration_key: str | None = Field(default=None, exclude=True)
    id: UUID

    @computed_field  # type: ignore[prop-decorator]
    @property
    def credential_configured(self) -> bool:
        return self.configuration_key is not None


class NotificationRuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    incident_category: str = Field(min_length=1, max_length=80)
    minimum_severity: str = Field(pattern="^(INFO|LOW|MEDIUM|HIGH|CRITICAL)$")
    teams: list[str] = Field(min_length=1)
    channel_ids: list[UUID] = Field(min_length=1)
    enabled: bool = True


class NotificationRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    incident_category: str
    minimum_severity: str
    teams: list[str]
    channel_ids: list[str]
    enabled: bool


class CapacityThresholdCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    entity_type: str = Field(min_length=1, max_length=32)
    metric_name: str = Field(min_length=1, max_length=80)
    informational_percent: float = 70
    warning_percent: float = 80
    critical_percent: float = 90
    duration_seconds: int = Field(default=600, gt=0, le=86400)
    enabled: bool = True

    @model_validator(mode="after")
    def validate_thresholds(self) -> "CapacityThresholdCreate":
        ordered = (
            0 <= self.informational_percent < self.warning_percent < self.critical_percent <= 100
        )
        if not ordered:
            raise ValueError("capacity thresholds must be ordered within 0-100")
        return self


class CapacityThresholdResponse(CapacityThresholdCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


class CapacityEvaluationRequest(BaseModel):
    entity_type: str = Field(min_length=1, max_length=32)
    entity_id: str = Field(min_length=1, max_length=255)
    metric_name: str = Field(min_length=1, max_length=80)
    samples: list[float] = Field(min_length=2, max_length=10_000)
    duration_seconds: int = Field(gt=0, le=86400)


class CapacityAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    entity_type: str
    entity_id: str
    metric_name: str
    current_percent: float
    sustained_percent: float
    duration_seconds: int
    category: str
    evidence: list[dict[str, Any]]
    evaluated_at: datetime


class CapacityTrendRequest(BaseModel):
    entity_type: str = Field(min_length=1, max_length=32)
    entity_id: str = Field(min_length=1, max_length=255)
    metric_name: str = Field(min_length=1, max_length=80)
    observations: list[tuple[datetime, float]] = Field(min_length=3, max_length=10_000)
    threshold_percent: float = Field(default=80, gt=0, le=100)


class CapacityTrendResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    entity_type: str
    entity_id: str
    metric_name: str
    window_days: int
    sample_count: int
    slope_per_day: float
    threshold_percent: float
    projected_crossing_at: datetime | None
    assumptions: list[str]
    created_at: datetime


class SubscriberDiagnosticsResponse(BaseModel):
    identity: dict[str, Any]
    session: dict[str, Any]
    fiber: dict[str, Any]
    performance: dict[str, Any]
    stability: dict[str, Any]
    incident: dict[str, Any] | None
    diagnosis: dict[str, Any]
    health: HealthScoreResponse | None


class DashboardResponse(BaseModel):
    summary: dict[str, Any]
    widgets: dict[str, list[dict[str, Any]]]
