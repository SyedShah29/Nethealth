from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class OutageCorrelation(Base):
    __tablename__ = "outage_correlations"
    __table_args__ = (
        CheckConstraint(
            "confidence IN ('LOW', 'MEDIUM', 'HIGH', 'CONFIRMED')",
            name="ck_outage_correlations_confidence",
        ),
        CheckConstraint(
            "window_seconds BETWEEN 30 AND 120",
            name="ck_outage_correlations_window",
        ),
        CheckConstraint("affected_count > 0", name="ck_outage_correlations_affected_count"),
        Index("ix_outage_correlations_created", "created_at"),
        Index("ix_outage_correlations_ancestor", "common_ancestor_node_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    window_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    common_ancestor_node_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("topology_nodes.id", ondelete="SET NULL")
    )
    classification: Mapped[str] = mapped_column(String(80), nullable=False)
    confidence: Mapped[str] = mapped_column(String(16), nullable=False)
    affected_count: Mapped[int] = mapped_column(Integer, nullable=False)
    affected_entities: Mapped[list[dict[str, str]]] = mapped_column(JSONB, nullable=False)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class RootCauseAssessment(Base):
    __tablename__ = "root_cause_assessments"
    __table_args__ = (
        CheckConstraint(
            "severity IN ('INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name="ck_root_cause_assessments_severity",
        ),
        Index("ix_root_cause_assessments_created", "created_at"),
        Index("ix_root_cause_assessments_correlation", "correlation_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    correlation_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("outage_correlations.id", ondelete="SET NULL")
    )
    classification: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    affected_entities: Mapped[list[dict[str, str]]] = mapped_column(JSONB, nullable=False)
    recommended_checks: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
