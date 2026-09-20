"""Add the Phase 7 topology graph.

Revision ID: 0011
Revises: 0010
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "topology_nodes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("node_type", sa.String(32), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("entity_type", sa.String(32)),
        sa.Column("entity_id", sa.String(255)),
        sa.Column("status", sa.String(32), nullable=False, server_default="UNKNOWN"),
        sa.Column(
            "attributes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "node_type IN ('TRANSIT', 'CORE', 'BNG', 'BRAS', 'AGGREGATION', "
            "'ACCESS', 'OLT', 'PON', 'ONU', 'SUBSCRIBER')",
            name="ck_topology_nodes_type",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "entity_type", "entity_id", name="uq_topology_nodes_entity"
        ),
    )
    op.create_index(
        "ix_topology_nodes_type_status",
        "topology_nodes",
        ["node_type", "status"],
    )
    op.create_table(
        "topology_edges",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_node_id", sa.Uuid(), nullable=False),
        sa.Column("target_node_id", sa.Uuid(), nullable=False),
        sa.Column("interface_id", sa.Uuid()),
        sa.Column(
            "relation", sa.String(32), nullable=False, server_default="DEPENDS_ON"
        ),
        sa.Column(
            "attributes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "source_node_id <> target_node_id", name="ck_topology_edges_not_self"
        ),
        sa.ForeignKeyConstraint(
            ["interface_id"], ["interfaces.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["source_node_id"], ["topology_nodes.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["target_node_id"], ["topology_nodes.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_node_id", "target_node_id", name="uq_topology_edges_nodes"
        ),
    )
    op.create_index("ix_topology_edges_source", "topology_edges", ["source_node_id"])
    op.create_index("ix_topology_edges_target", "topology_edges", ["target_node_id"])
    op.create_index("ix_topology_edges_interface", "topology_edges", ["interface_id"])


def downgrade() -> None:
    op.drop_index("ix_topology_edges_interface", table_name="topology_edges")
    op.drop_index("ix_topology_edges_target", table_name="topology_edges")
    op.drop_index("ix_topology_edges_source", table_name="topology_edges")
    op.drop_table("topology_edges")
    op.drop_index("ix_topology_nodes_type_status", table_name="topology_nodes")
    op.drop_table("topology_nodes")
