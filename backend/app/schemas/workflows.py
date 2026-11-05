from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FieldTaskStatus(StrEnum):
    ASSIGNED = "ASSIGNED"
    ACCEPTED = "ACCEPTED"
    IN_PROGRESS = "IN_PROGRESS"
    RESTORED = "RESTORED"
    CLOSED = "CLOSED"


class FieldTaskCreate(BaseModel):
    incident_id: UUID
    subscriber_id: str | None = Field(default=None, max_length=120)
    olt_id: str | None = Field(default=None, max_length=120)
    pon_id: str | None = Field(default=None, max_length=120)
    onu_id: str | None = Field(default=None, max_length=120)
    last_rx: float | None = None
    current_status: str = Field(min_length=1, max_length=32)
    recommended_checks: list[str] = Field(default_factory=list, max_length=100)
    assigned_technician_id: UUID


class FieldTaskAction(BaseModel):
    action: str = Field(pattern="^(ACCEPT|START_WORK|MARK_RESTORED|CLOSE)$")


class FieldNoteCreate(BaseModel):
    note: str = Field(min_length=1, max_length=2000)


class FieldPhotoCreate(BaseModel):
    filename: str = Field(
        min_length=1,
        max_length=255,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._ -]*$",
    )
    content_type: str = Field(pattern="^image/(jpeg|png|webp)$")
    content_base64: str = Field(min_length=1, max_length=7_000_000)


class FieldPhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    task_id: UUID
    filename: str
    content_type: str
    byte_size: int
    sha256: str
    created_at: datetime


class FieldTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    incident_id: UUID
    subscriber_id: str | None
    olt_id: str | None
    pon_id: str | None
    onu_id: str | None
    last_rx: float | None
    current_status: str
    recommended_checks: list[str]
    assigned_technician_id: UUID
    status: FieldTaskStatus
    notes: list[dict[str, Any]]
    accepted_at: datetime | None
    started_at: datetime | None
    restored_at: datetime | None
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class FieldTicketResponse(BaseModel):
    task: FieldTaskResponse
    incident: dict[str, Any]
    photos: list[FieldPhotoResponse]


class EscalationStep(BaseModel):
    delay_minutes: int = Field(gt=0, le=10_080)
    team: str = Field(min_length=1, max_length=120)
    channel_ids: list[UUID] = Field(min_length=1)


class EscalationPolicyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    incident_category: str | None = Field(default=None, max_length=80)
    minimum_severity: str = Field(pattern="^(HIGH|CRITICAL)$")
    steps: list[EscalationStep] = Field(min_length=1, max_length=20)
    enabled: bool = True

    @model_validator(mode="after")
    def steps_are_ordered(self) -> "EscalationPolicyCreate":
        delays = [step.delay_minutes for step in self.steps]
        if delays != sorted(set(delays)):
            raise ValueError("escalation step delays must be unique and increasing")
        return self


class EscalationPolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    incident_category: str | None
    minimum_severity: str
    steps: list[dict[str, Any]]
    enabled: bool


class MaintenanceWindowCreate(BaseModel):
    scope_type: str = Field(pattern="^(DEVICE|SITE)$")
    scope_id: str = Field(min_length=1, max_length=255)
    starts_at: datetime
    ends_at: datetime
    reason: str = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def valid_window(self) -> "MaintenanceWindowCreate":
        if self.ends_at <= self.starts_at:
            raise ValueError("maintenance end must be after start")
        return self


class MaintenanceWindowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    scope_type: str
    scope_id: str
    starts_at: datetime
    ends_at: datetime
    reason: str
    created_by: UUID
    created_at: datetime


class AnalyticsResponse(BaseModel):
    outages_by_month: list[dict[str, Any]]
    outages_by_site: list[dict[str, Any]]
    outages_by_olt: list[dict[str, Any]]
    outages_by_pon: list[dict[str, Any]]
    mean_time_to_detect_seconds: float | None
    mean_time_to_acknowledge_seconds: float | None
    mean_time_to_repair_seconds: float | None
    repeat_incidents: list[dict[str, Any]]
    unstable_subscribers: list[dict[str, Any]]
    optical_degradation: list[dict[str, Any]]
    congestion: list[dict[str, Any]]
    device_availability: list[dict[str, Any]]


class SearchResult(BaseModel):
    result_type: str
    id: str
    label: str
    detail: str | None = None
