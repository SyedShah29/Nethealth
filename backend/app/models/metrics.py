from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Float, Index, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MetricSample(Base):
    __tablename__ = "metric_samples"
    __table_args__ = (
        CheckConstraint(
            "entity_type IN ('DEVICE', 'INTERFACE', 'ONU', 'SUBSCRIBER')",
            name="ck_metric_samples_entity_type",
        ),
        Index(
            "ix_metric_samples_entity_metric_time",
            "entity_type",
            "entity_id",
            "metric_name",
            "timestamp",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(16), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(255), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(80), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(32))
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    tags: Mapped[dict[str, str]] = mapped_column(JSONB, default=dict, nullable=False)
