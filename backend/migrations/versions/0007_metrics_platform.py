"""Add the Phase 4 TimescaleDB metrics platform.

Revision ID: 0007
Revises: 0006
"""

import os

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def _days(name: str, default: int) -> int:
    value = int(os.getenv(name, str(default)))
    if value < 1:
        raise ValueError(f"{name} must be at least one day")
    return value


def _create_aggregate(name: str, bucket: str) -> None:
    op.execute(
        f"""
        CREATE MATERIALIZED VIEW {name}
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket(INTERVAL '{bucket}', timestamp) AS bucket,
            entity_type,
            entity_id,
            metric_name,
            unit,
            source,
            tags,
            avg(value) AS value_avg,
            min(value) AS value_min,
            max(value) AS value_max,
            sum(value) AS value_sum,
            count(*)::bigint AS sample_count
        FROM metric_samples
        GROUP BY bucket, entity_type, entity_id, metric_name, unit, source, tags
        WITH NO DATA
        """
    )
    op.execute(f"ALTER MATERIALIZED VIEW {name} SET (timescaledb.materialized_only = false)")


def upgrade() -> None:
    raw_days = _days("METRICS_RAW_RETENTION_DAYS", 30)
    five_minute_days = _days("METRICS_FIVE_MINUTE_RETENTION_DAYS", 180)
    hourly_days = _days("METRICS_HOURLY_RETENTION_DAYS", 730)

    op.create_table(
        "metric_samples",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("entity_type", sa.String(16), nullable=False),
        sa.Column("entity_id", sa.String(255), nullable=False),
        sa.Column("metric_name", sa.String(80), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(32)),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column(
            "tags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.CheckConstraint(
            "entity_type IN ('DEVICE', 'INTERFACE', 'ONU', 'SUBSCRIBER')",
            name="ck_metric_samples_entity_type",
        ),
        sa.PrimaryKeyConstraint("id", "timestamp"),
    )
    op.create_index(
        "ix_metric_samples_entity_metric_time",
        "metric_samples",
        ["entity_type", "entity_id", "metric_name", "timestamp"],
    )
    op.execute(
        "SELECT create_hypertable('metric_samples', by_range('timestamp'), "
        "if_not_exists => TRUE)"
    )

    _create_aggregate("metric_samples_5m", "5 minutes")
    _create_aggregate("metric_samples_hourly", "1 hour")
    _create_aggregate("metric_samples_daily", "1 day")

    for view, end_offset, schedule in (
        ("metric_samples_5m", "5 minutes", "5 minutes"),
        ("metric_samples_hourly", "1 hour", "1 hour"),
        ("metric_samples_daily", "1 day", "1 day"),
    ):
        op.execute(
            "SELECT add_continuous_aggregate_policy("
            f"'{view}', start_offset => INTERVAL '{raw_days} days', "
            f"end_offset => INTERVAL '{end_offset}', "
            f"schedule_interval => INTERVAL '{schedule}')"
        )

    op.execute(
        "SELECT add_retention_policy('metric_samples', "
        f"INTERVAL '{raw_days} days')"
    )
    op.execute(
        "SELECT add_retention_policy('metric_samples_5m', "
        f"INTERVAL '{five_minute_days} days')"
    )
    op.execute(
        "SELECT add_retention_policy('metric_samples_hourly', "
        f"INTERVAL '{hourly_days} days')"
    )


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS metric_samples_daily CASCADE")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS metric_samples_hourly CASCADE")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS metric_samples_5m CASCADE")
    op.drop_index("ix_metric_samples_entity_metric_time", table_name="metric_samples")
    op.drop_table("metric_samples")
