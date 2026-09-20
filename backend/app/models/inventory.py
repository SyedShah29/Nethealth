# ruff: noqa
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Site(Base):
    __tablename__ = "sites"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    region: Mapped[str] = mapped_column(String(120), nullable=False)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    description: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    devices: Mapped[list[Device]] = relationship(back_populates="site")


class CollectorProfile(Base):
    __tablename__ = "collector_profiles"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Device(Base):
    __tablename__ = "devices"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    management_ip: Mapped[str] = mapped_column(String(64), nullable=False)
    device_type: Mapped[str] = mapped_column(String(32), nullable=False)
    vendor: Mapped[str | None] = mapped_column(String(120))
    model: Mapped[str | None] = mapped_column(String(120))
    site_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("sites.id", ondelete="RESTRICT"), index=True, nullable=False)
    monitoring_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    collector_profile_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("collector_profiles.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(32), default="UNKNOWN", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    site: Mapped[Site] = relationship(back_populates="devices", lazy="selectin")
    interfaces: Mapped[list[Interface]] = relationship(back_populates="device", cascade="all, delete-orphan")


class Interface(Base):
    __tablename__ = "interfaces"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    device_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("devices.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    speed: Mapped[int | None] = mapped_column(Integer)
    mac_address: Mapped[str | None] = mapped_column(String(32))
    admin_status: Mapped[str | None] = mapped_column(String(16))
    oper_status: Mapped[str | None] = mapped_column(String(16))
    device: Mapped[Device] = relationship(back_populates="interfaces")


class CollectorAssignment(Base):
    __tablename__ = "collector_assignments"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    device_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("devices.id", ondelete="CASCADE"), index=True, nullable=False)
    collector_profile_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("collector_profiles.id", ondelete="CASCADE"), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
