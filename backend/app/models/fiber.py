from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class OLT(Base):
    __tablename__ = "olts"
    __table_args__ = (
        CheckConstraint("frame_count >= 0", name="ck_olts_frame_count_nonnegative"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    device_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("devices.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
    )
    vendor: Mapped[str] = mapped_column(String(120), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    frame_count: Mapped[int] = mapped_column(Integer, nullable=False)
    slot_information: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, nullable=False
    )
    uplinks: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    pons: Mapped[list[PON]] = relationship(
        back_populates="olt", cascade="all, delete-orphan"
    )


class PON(Base):
    __tablename__ = "pons"
    __table_args__ = (
        CheckConstraint("frame >= 0", name="ck_pons_frame_nonnegative"),
        CheckConstraint("slot >= 0", name="ck_pons_slot_nonnegative"),
        CheckConstraint("port >= 0", name="ck_pons_port_nonnegative"),
        CheckConstraint(
            "subscriber_count >= 0", name="ck_pons_subscriber_count_nonnegative"
        ),
        CheckConstraint(
            "configured_capacity > 0", name="ck_pons_configured_capacity_positive"
        ),
        CheckConstraint(
            "subscriber_count <= configured_capacity",
            name="ck_pons_subscriber_count_capacity",
        ),
        UniqueConstraint(
            "olt_id", "frame", "slot", "port", name="uq_pons_olt_frame_slot_port"
        ),
        UniqueConstraint("id", "olt_id", name="uq_pons_id_olt"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    olt_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("olts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    frame: Mapped[int] = mapped_column(Integer, nullable=False)
    slot: Mapped[int] = mapped_column(Integer, nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    technology: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="UNKNOWN")
    subscriber_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    configured_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    olt: Mapped[OLT] = relationship(back_populates="pons")
    onus: Mapped[list[ONU]] = relationship(
        back_populates="pon", cascade="all, delete-orphan"
    )


class ONU(Base):
    __tablename__ = "onus"
    __table_args__ = (
        ForeignKeyConstraint(
            ["pon_id", "olt_id"],
            ["pons.id", "pons.olt_id"],
            ondelete="CASCADE",
            name="fk_onus_pon_olt",
        ),
        UniqueConstraint("olt_id", "onu_identifier", name="uq_onus_olt_identifier"),
        Index("ix_onus_pon_id", "pon_id"),
        Index("ix_onus_subscriber_id", "subscriber_id"),
        Index("ix_onus_status", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    onu_identifier: Mapped[str] = mapped_column(String(120), nullable=False)
    serial_number: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    olt_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    pon_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    subscriber_id: Mapped[str | None] = mapped_column(
        String(120),
        ForeignKey("subscribers.subscriber_id", ondelete="SET NULL"),
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="UNKNOWN")
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    registration_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="UNKNOWN"
    )
    rx_power: Mapped[float | None] = mapped_column(Float)
    tx_power: Mapped[float | None] = mapped_column(Float)
    temperature: Mapped[float | None] = mapped_column(Float)
    distance: Mapped[float | None] = mapped_column(Float)
    pon: Mapped[PON] = relationship(back_populates="onus")


class OpticalThreshold(Base):
    __tablename__ = "optical_thresholds"
    __table_args__ = (
        CheckConstraint(
            "num_nonnulls(critical_low, warning_low, warning_high, critical_high) > 0",
            name="ck_optical_thresholds_has_boundary",
        ),
        CheckConstraint(
            "metric_name IN ('RX_POWER', 'TX_POWER', 'TEMPERATURE', 'DISTANCE')",
            name="ck_optical_thresholds_metric_name",
        ),
        CheckConstraint(
            "critical_low IS NULL OR warning_low IS NULL OR critical_low <= warning_low",
            name="ck_optical_thresholds_low_order",
        ),
        CheckConstraint(
            "warning_low IS NULL OR warning_high IS NULL OR warning_low < warning_high",
            name="ck_optical_thresholds_warning_order",
        ),
        CheckConstraint(
            "warning_high IS NULL OR critical_high IS NULL "
            "OR warning_high <= critical_high",
            name="ck_optical_thresholds_high_order",
        ),
        Index(
            "uq_optical_threshold_scope_metric",
            "vendor",
            "technology",
            "device_model",
            "metric_name",
            unique=True,
            postgresql_nulls_not_distinct=True,
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    vendor: Mapped[str] = mapped_column(String(120), nullable=False)
    technology: Mapped[str] = mapped_column(String(32), nullable=False)
    device_model: Mapped[str | None] = mapped_column(String(120))
    metric_name: Mapped[str] = mapped_column(String(64), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    critical_low: Mapped[float | None] = mapped_column(Float)
    warning_low: Mapped[float | None] = mapped_column(Float)
    warning_high: Mapped[float | None] = mapped_column(Float)
    critical_high: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
