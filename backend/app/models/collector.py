# ruff: noqa
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import DateTime, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.base import Base

class CollectorStatusRecord(Base):
    __tablename__ = "collector_status"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    device_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    collector_type: Mapped[str] = mapped_column(String(32), nullable=False)
    last_successful_poll: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_failed_poll: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[float | None] = mapped_column()
    current_health: Mapped[str] = mapped_column(String(32), nullable=False, default="UNKNOWN")
    current_worker: Mapped[str | None] = mapped_column(String(120))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
