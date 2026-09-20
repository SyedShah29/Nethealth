"""Add persisted outage-correlation findings.

Revision ID: 0013
Revises: 0012
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "outage_correlations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_ended_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_seconds", sa.Integer(), nullable=False),
        sa.Column("common_ancestor_node_id", sa.Uuid()),
        sa.Column("classification", sa.String(80), nullable=False),
        sa.Column("confidence", sa.String(16), nullable=False),
        sa.Column("affected_count", sa.Integer(), nullable=False),
        sa.Column(
            "affected_entities", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "confidence IN ('LOW', 'MEDIUM', 'HIGH', 'CONFIRMED')",
            name="ck_outage_correlations_confidence",
        ),
        sa.CheckConstraint(
            "window_seconds BETWEEN 30 AND 120",
            name="ck_outage_correlations_window",
        ),
        sa.CheckConstraint(
            "affected_count > 0", name="ck_outage_correlations_affected_count"
        ),
        sa.ForeignKeyConstraint(
            ["common_ancestor_node_id"], ["topology_nodes.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_outage_correlations_created", "outage_correlations", ["created_at"]
    )
    op.create_index(
        "ix_outage_correlations_ancestor",
        "outage_correlations",
        ["common_ancestor_node_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_outage_correlations_ancestor", table_name="outage_correlations")
    op.drop_index("ix_outage_correlations_created", table_name="outage_correlations")
    op.drop_table("outage_correlations")
