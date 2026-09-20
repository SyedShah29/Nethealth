from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Subscriber(Base):
    __tablename__ = "subscribers"
    __table_args__ = (
        CheckConstraint(
            "package_speed IS NULL OR package_speed >= 0",
            name="ck_subscribers_package_speed_nonnegative",
        ),
        Index("ix_subscribers_status", "status"),
        Index("ix_subscribers_nas_id", "nas_id"),
        Index("ix_subscribers_olt_id", "olt_id"),
        Index("ix_subscribers_pon_id", "pon_id"),
        Index("ix_subscribers_onu_id", "onu_id"),
    )

    subscriber_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    external_reference: Mapped[str | None] = mapped_column(
        String(255), unique=True, index=True
    )
    package_speed: Mapped[int | None] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="UNKNOWN")
    nas_id: Mapped[str | None] = mapped_column(String(120))
    olt_id: Mapped[str | None] = mapped_column(String(120))
    pon_id: Mapped[str | None] = mapped_column(String(120))
    onu_id: Mapped[str | None] = mapped_column(String(120))
    current_ip: Mapped[str | None] = mapped_column(String(64))
    mac_address: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    sessions: Mapped[list[SubscriberSession]] = relationship(
        back_populates="subscriber",
        cascade="all, delete-orphan",
    )


class SubscriberSession(Base):
    __tablename__ = "subscriber_sessions"
    __table_args__ = (
        CheckConstraint(
            "session_end IS NULL OR session_end >= session_start",
            name="ck_subscriber_sessions_time_order",
        ),
        CheckConstraint(
            "duration IS NULL OR duration >= 0",
            name="ck_subscriber_sessions_duration_nonnegative",
        ),
        Index(
            "ix_subscriber_sessions_subscriber_start",
            "subscriber_id",
            "session_start",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    subscriber_id: Mapped[str] = mapped_column(
        String(120),
        ForeignKey("subscribers.subscriber_id", ondelete="CASCADE"),
        nullable=False,
    )
    session_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    session_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    nas: Mapped[str] = mapped_column(String(120), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    disconnect_reason: Mapped[str | None] = mapped_column(String(255))
    duration: Mapped[int | None] = mapped_column(Integer)
    subscriber: Mapped[Subscriber] = relationship(back_populates="sessions")
