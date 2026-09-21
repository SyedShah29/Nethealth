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
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class SubscriberHealthScore(Base):
    __tablename__ = "subscriber_health_scores"
    __table_args__ = (
        CheckConstraint("score BETWEEN 0 AND 100", name="ck_health_scores_range"),
        CheckConstraint(
            "category IN ('HEALTHY', 'GOOD', 'WARNING', 'CRITICAL')",
            name="ck_health_scores_category",
        ),
        Index("ix_health_scores_subscriber_time", "subscriber_id", "evaluated_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    subscriber_id: Mapped[str] = mapped_column(
        String(120),
        ForeignKey("subscribers.subscriber_id", ondelete="CASCADE"),
        nullable=False,
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String(16), nullable=False)
    components: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    weights: Mapped[dict[str, int]] = mapped_column(JSONB, nullable=False)
    thresholds: Mapped[dict[str, int]] = mapped_column(JSONB, nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class OperationalAnomaly(Base):
    __tablename__ = "operational_anomalies"
    __table_args__ = (
        CheckConstraint("duration_seconds >= 0", name="ck_anomalies_duration"),
        CheckConstraint(
            "severity IN ('INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name="ck_anomalies_severity",
        ),
        Index("ix_anomalies_entity_time", "entity_type", "entity_id", "detected_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(255), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(80), nullable=False)
    anomaly_type: Mapped[str] = mapped_column(String(80), nullable=False)
    method: Mapped[str] = mapped_column(String(32), nullable=False)
    current_value: Mapped[float] = mapped_column(Float, nullable=False)
    historical_baseline: Mapped[float] = mapped_column(Float, nullable=False)
    difference: Mapped[float] = mapped_column(Float, nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = (
        CheckConstraint(
            "status IN ('OPEN', 'ACKNOWLEDGED', 'INVESTIGATING', 'RESOLVED', 'CLOSED')",
            name="ck_incidents_status",
        ),
        CheckConstraint(
            "severity IN ('INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name="ck_incidents_severity",
        ),
        Index("ix_incidents_status_severity", "status", "severity"),
        Index(
            "ix_incidents_dedup_lookup",
            "category",
            "primary_entity_type",
            "primary_entity_id",
            "status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN")
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    root_cause: Mapped[str | None] = mapped_column(String(160))
    primary_entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    primary_entity_id: Mapped[str] = mapped_column(String(255), nullable=False)
    affected_subscribers: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    affected_topology: Mapped[list[dict[str, str]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    recommendations: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    assigned_team: Mapped[str | None] = mapped_column(String(120))
    assigned_user_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL")
    )
    comments: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class IncidentEvent(Base):
    __tablename__ = "incident_events"
    __table_args__ = (Index("ix_incident_events_incident_time", "incident_id", "occurred_at"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    incident_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    actor_user_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL")
    )
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class NotificationChannel(Base):
    __tablename__ = "notification_channels"
    __table_args__ = (
        CheckConstraint(
            "channel_type IN ('EMAIL', 'SMS', 'WHATSAPP', 'TELEGRAM', 'DASHBOARD', 'WEB_PUSH')",
            name="ck_notification_channels_type",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    channel_type: Mapped[str] = mapped_column(String(20), nullable=False)
    configuration_key: Mapped[str | None] = mapped_column(String(120))
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class NotificationRule(Base):
    __tablename__ = "notification_rules"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    incident_category: Mapped[str] = mapped_column(String(80), nullable=False)
    minimum_severity: Mapped[str] = mapped_column(String(16), nullable=False)
    teams: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    channel_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"
    __table_args__ = (
        UniqueConstraint("fingerprint", name="uq_notification_deliveries_fingerprint"),
        Index("ix_notification_deliveries_incident", "incident_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    incident_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False
    )
    channel_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("notification_channels.id", ondelete="RESTRICT"), nullable=False
    )
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class CapacityThreshold(Base):
    __tablename__ = "capacity_thresholds"
    __table_args__ = (
        CheckConstraint(
            "informational_percent >= 0 AND informational_percent < warning_percent "
            "AND warning_percent < critical_percent AND critical_percent <= 100",
            name="ck_capacity_threshold_order",
        ),
        CheckConstraint("duration_seconds > 0", name="ck_capacity_threshold_duration"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(80), nullable=False)
    informational_percent: Mapped[float] = mapped_column(Float, nullable=False, default=70)
    warning_percent: Mapped[float] = mapped_column(Float, nullable=False, default=80)
    critical_percent: Mapped[float] = mapped_column(Float, nullable=False, default=90)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=600)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class CapacityAssessment(Base):
    __tablename__ = "capacity_assessments"
    __table_args__ = (
        CheckConstraint(
            "category IN ('NORMAL', 'INFORMATIONAL', 'WARNING', 'CRITICAL')",
            name="ck_capacity_assessments_category",
        ),
        Index("ix_capacity_assessments_entity_time", "entity_type", "entity_id", "evaluated_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(255), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(80), nullable=False)
    current_percent: Mapped[float] = mapped_column(Float, nullable=False)
    sustained_percent: Mapped[float] = mapped_column(Float, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class CapacityTrend(Base):
    __tablename__ = "capacity_trends"
    __table_args__ = (
        Index(
            "ix_capacity_trends_entity_time",
            "entity_type",
            "entity_id",
            "created_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(255), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(80), nullable=False)
    window_days: Mapped[int] = mapped_column(Integer, nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False)
    slope_per_day: Mapped[float] = mapped_column(Float, nullable=False)
    threshold_percent: Mapped[float] = mapped_column(Float, nullable=False)
    projected_crossing_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assumptions: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
