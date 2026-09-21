"""Add configurable capacity monitoring and trend projections.

Revision ID: 0018
Revises: 0017
"""

from uuid import UUID

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    thresholds = op.create_table(
        "capacity_thresholds",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("metric_name", sa.String(80), nullable=False),
        sa.Column("informational_percent", sa.Float(), nullable=False),
        sa.Column("warning_percent", sa.Float(), nullable=False),
        sa.Column("critical_percent", sa.Float(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.CheckConstraint(
            "informational_percent >= 0 AND informational_percent < warning_percent "
            "AND warning_percent < critical_percent AND critical_percent <= 100",
            name="ck_capacity_threshold_order",
        ),
        sa.CheckConstraint("duration_seconds > 0", name="ck_capacity_threshold_duration"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "capacity_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("entity_id", sa.String(255), nullable=False),
        sa.Column("metric_name", sa.String(80), nullable=False),
        sa.Column("current_percent", sa.Float(), nullable=False),
        sa.Column("sustained_percent", sa.Float(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), nullable=False),
        sa.Column(
            "evaluated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "category IN ('NORMAL', 'INFORMATIONAL', 'WARNING', 'CRITICAL')",
            name="ck_capacity_assessments_category",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_capacity_assessments_entity_time",
        "capacity_assessments",
        ["entity_type", "entity_id", "evaluated_at"],
    )
    op.create_table(
        "capacity_trends",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("entity_id", sa.String(255), nullable=False),
        sa.Column("metric_name", sa.String(80), nullable=False),
        sa.Column("window_days", sa.Integer(), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("slope_per_day", sa.Float(), nullable=False),
        sa.Column("threshold_percent", sa.Float(), nullable=False),
        sa.Column("projected_crossing_at", sa.DateTime(timezone=True)),
        sa.Column("assumptions", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_capacity_trends_entity_time",
        "capacity_trends",
        ["entity_type", "entity_id", "created_at"],
    )
    op.bulk_insert(
        thresholds,
        [
            {
                "id": UUID("00000000-0000-4000-8000-000000000301"),
                "name": "Interface sustained utilization",
                "entity_type": "INTERFACE",
                "metric_name": "utilization_percent",
                "informational_percent": 70.0,
                "warning_percent": 80.0,
                "critical_percent": 90.0,
                "duration_seconds": 600,
                "enabled": True,
            },
            {
                "id": UUID("00000000-0000-4000-8000-000000000302"),
                "name": "PON subscriber utilization",
                "entity_type": "PON",
                "metric_name": "subscriber_utilization_percent",
                "informational_percent": 70.0,
                "warning_percent": 80.0,
                "critical_percent": 90.0,
                "duration_seconds": 600,
                "enabled": True,
            },
            {
                "id": UUID("00000000-0000-4000-8000-000000000303"),
                "name": "OLT uplink sustained utilization",
                "entity_type": "OLT",
                "metric_name": "uplink_utilization_percent",
                "informational_percent": 70.0,
                "warning_percent": 80.0,
                "critical_percent": 90.0,
                "duration_seconds": 600,
                "enabled": True,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_capacity_trends_entity_time", table_name="capacity_trends")
    op.drop_table("capacity_trends")
    op.drop_index("ix_capacity_assessments_entity_time", table_name="capacity_assessments")
    op.drop_table("capacity_assessments")
    op.drop_table("capacity_thresholds")
