"""Add deterministic root-cause assessments.

Revision ID: 0014
Revises: 0013
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "root_cause_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("correlation_id", sa.Uuid()),
        sa.Column("classification", sa.String(80), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "affected_entities", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column(
            "recommended_checks", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "severity IN ('INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name="ck_root_cause_assessments_severity",
        ),
        sa.ForeignKeyConstraint(
            ["correlation_id"], ["outage_correlations.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_root_cause_assessments_created",
        "root_cause_assessments",
        ["created_at"],
    )
    op.create_index(
        "ix_root_cause_assessments_correlation",
        "root_cause_assessments",
        ["correlation_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_root_cause_assessments_correlation",
        table_name="root_cause_assessments",
    )
    op.drop_index(
        "ix_root_cause_assessments_created", table_name="root_cause_assessments"
    )
    op.drop_table("root_cause_assessments")
