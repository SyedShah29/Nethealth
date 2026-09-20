from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class TopologyNode(Base):
    __tablename__ = "topology_nodes"
    __table_args__ = (
        CheckConstraint(
            "node_type IN ('TRANSIT', 'CORE', 'BNG', 'BRAS', 'AGGREGATION', "
            "'ACCESS', 'OLT', 'PON', 'ONU', 'SUBSCRIBER')",
            name="ck_topology_nodes_type",
        ),
        UniqueConstraint(
            "entity_type", "entity_id", name="uq_topology_nodes_entity"
        ),
        Index("ix_topology_nodes_type_status", "node_type", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    node_type: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(32))
    entity_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="UNKNOWN")
    attributes: Mapped[dict[str, Any]] = mapped_column(
        "attributes", JSONB, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class TopologyEdge(Base):
    __tablename__ = "topology_edges"
    __table_args__ = (
        CheckConstraint(
            "source_node_id <> target_node_id", name="ck_topology_edges_not_self"
        ),
        UniqueConstraint(
            "source_node_id", "target_node_id", name="uq_topology_edges_nodes"
        ),
        Index("ix_topology_edges_source", "source_node_id"),
        Index("ix_topology_edges_target", "target_node_id"),
        Index("ix_topology_edges_interface", "interface_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    source_node_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("topology_nodes.id", ondelete="CASCADE"), nullable=False
    )
    target_node_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("topology_nodes.id", ondelete="CASCADE"), nullable=False
    )
    interface_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("interfaces.id", ondelete="SET NULL")
    )
    relation: Mapped[str] = mapped_column(
        String(32), nullable=False, default="DEPENDS_ON"
    )
    attributes: Mapped[dict[str, Any]] = mapped_column(
        "attributes", JSONB, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
