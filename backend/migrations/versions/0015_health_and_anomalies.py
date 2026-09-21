"""Add subscriber health scores and explainable anomalies.

Revision ID: 0015
Revises: 0014
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subscriber_health_scores",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("subscriber_id", sa.String(120), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(16), nullable=False),
        sa.Column("components", postgresql.JSONB(), nullable=False),
        sa.Column("weights", postgresql.JSONB(), nullable=False),
        sa.Column("thresholds", postgresql.JSONB(), nullable=False),
        sa.Column(
            "evaluated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("score BETWEEN 0 AND 100", name="ck_health_scores_range"),
        sa.CheckConstraint(
            "category IN ('HEALTHY', 'GOOD', 'WARNING', 'CRITICAL')",
            name="ck_health_scores_category",
        ),
        sa.ForeignKeyConstraint(
            ["subscriber_id"], ["subscribers.subscriber_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_health_scores_subscriber_time",
        "subscriber_health_scores",
        ["subscriber_id", "evaluated_at"],
    )
    op.create_table(
        "operational_anomalies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("entity_id", sa.String(255), nullable=False),
        sa.Column("metric_name", sa.String(80), nullable=False),
        sa.Column("anomaly_type", sa.String(80), nullable=False),
        sa.Column("method", sa.String(32), nullable=False),
        sa.Column("current_value", sa.Float(), nullable=False),
        sa.Column("historical_baseline", sa.Float(), nullable=False),
        sa.Column("difference", sa.Float(), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), nullable=False),
        sa.Column(
            "detected_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("duration_seconds >= 0", name="ck_anomalies_duration"),
        sa.CheckConstraint(
            "severity IN ('INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name="ck_anomalies_severity",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_anomalies_entity_time",
        "operational_anomalies",
        ["entity_type", "entity_id", "detected_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_anomalies_entity_time", table_name="operational_anomalies")
    op.drop_table("operational_anomalies")
    op.drop_index("ix_health_scores_subscriber_time", table_name="subscriber_health_scores")
    op.drop_table("subscriber_health_scores")
