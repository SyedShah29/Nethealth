from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class Rule(Base):
    __tablename__ = "rules"
    __table_args__ = (
        CheckConstraint("duration_seconds >= 0", name="ck_rules_duration_nonnegative"),
        CheckConstraint(
            "severity IN ('INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name="ck_rules_severity",
        ),
        Index("ix_rules_entity_enabled", "entity_type", "enabled"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    conditions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    incident_category: Mapped[str] = mapped_column(String(80), nullable=False)
    recommendation: Mapped[str] = mapped_column(String(1000), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class RuleEvaluation(Base):
    __tablename__ = "rule_evaluations"
    __table_args__ = (
        CheckConstraint(
            "trigger_state IN ('DISABLED', 'CLEAR', 'PENDING', 'TRIGGERED')",
            name="ck_rule_evaluations_trigger_state",
        ),
        Index(
            "ix_rule_evaluations_entity_time",
            "entity_type",
            "entity_id",
            "evaluated_at",
        ),
        Index("ix_rule_evaluations_rule_time", "rule_id", "evaluated_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    rule_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("rules.id", ondelete="CASCADE"), nullable=False
    )
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(255), nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    result: Mapped[bool] = mapped_column(Boolean, nullable=False)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    trigger_state: Mapped[str] = mapped_column(String(16), nullable=False)
