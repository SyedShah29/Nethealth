from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class FieldTask(Base):
    __tablename__ = "field_tasks"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ASSIGNED', 'ACCEPTED', 'IN_PROGRESS', 'RESTORED', 'CLOSED')",
            name="ck_field_tasks_status",
        ),
        Index("ix_field_tasks_technician_status", "assigned_technician_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    incident_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("incidents.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    subscriber_id: Mapped[str | None] = mapped_column(
        String(120), ForeignKey("subscribers.subscriber_id", ondelete="SET NULL")
    )
    olt_id: Mapped[str | None] = mapped_column(String(120))
    pon_id: Mapped[str | None] = mapped_column(String(120))
    onu_id: Mapped[str | None] = mapped_column(String(120))
    last_rx: Mapped[float | None] = mapped_column(Float)
    current_status: Mapped[str] = mapped_column(String(32), nullable=False)
    recommended_checks: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    assigned_technician_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ASSIGNED")
    notes: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    restored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class FieldPhoto(Base):
    __tablename__ = "field_photos"
    __table_args__ = (Index("ix_field_photos_task_time", "task_id", "created_at"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("field_tasks.id", ondelete="CASCADE"), nullable=False
    )
    uploaded_by: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(80), nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class EscalationPolicy(Base):
    __tablename__ = "escalation_policies"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    incident_category: Mapped[str | None] = mapped_column(String(80))
    minimum_severity: Mapped[str] = mapped_column(String(16), nullable=False)
    steps: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class EscalationEvent(Base):
    __tablename__ = "escalation_events"
    __table_args__ = (
        UniqueConstraint("incident_id", "policy_id", "step_index", name="uq_escalation_event_step"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    incident_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False
    )
    policy_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("escalation_policies.id", ondelete="CASCADE"), nullable=False
    )
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    team: Mapped[str] = mapped_column(String(120), nullable=False)
    channel_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    escalated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class MaintenanceWindow(Base):
    __tablename__ = "maintenance_windows"
    __table_args__ = (
        CheckConstraint("scope_type IN ('DEVICE', 'SITE')", name="ck_maintenance_scope"),
        CheckConstraint("ends_at > starts_at", name="ck_maintenance_time_order"),
        Index("ix_maintenance_scope_time", "scope_type", "scope_id", "starts_at", "ends_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    scope_type: Mapped[str] = mapped_column(String(16), nullable=False)
    scope_id: Mapped[str] = mapped_column(String(255), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str] = mapped_column(String(1000), nullable=False)
    created_by: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
