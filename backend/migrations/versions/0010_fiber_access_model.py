"""Add the Phase 6 OLT, PON, ONU, and optical threshold model.

Revision ID: 0010
Revises: 0009
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "olts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("device_id", sa.Uuid(), nullable=False),
        sa.Column("vendor", sa.String(120), nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("frame_count", sa.Integer(), nullable=False),
        sa.Column(
            "slot_information",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "uplinks",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
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
            "frame_count >= 0", name="ck_olts_frame_count_nonnegative"
        ),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("device_id"),
    )

    op.create_table(
        "pons",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("olt_id", sa.Uuid(), nullable=False),
        sa.Column("frame", sa.Integer(), nullable=False),
        sa.Column("slot", sa.Integer(), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False),
        sa.Column("technology", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="UNKNOWN"),
        sa.Column(
            "subscriber_count", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("configured_capacity", sa.Integer(), nullable=False),
        sa.CheckConstraint("frame >= 0", name="ck_pons_frame_nonnegative"),
        sa.CheckConstraint("slot >= 0", name="ck_pons_slot_nonnegative"),
        sa.CheckConstraint("port >= 0", name="ck_pons_port_nonnegative"),
        sa.CheckConstraint(
            "subscriber_count >= 0", name="ck_pons_subscriber_count_nonnegative"
        ),
        sa.CheckConstraint(
            "configured_capacity > 0", name="ck_pons_configured_capacity_positive"
        ),
        sa.CheckConstraint(
            "subscriber_count <= configured_capacity",
            name="ck_pons_subscriber_count_capacity",
        ),
        sa.ForeignKeyConstraint(["olt_id"], ["olts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "olt_id", name="uq_pons_id_olt"),
        sa.UniqueConstraint(
            "olt_id", "frame", "slot", "port", name="uq_pons_olt_frame_slot_port"
        ),
    )
    op.create_index("ix_pons_olt_id", "pons", ["olt_id"])

    op.create_table(
        "onus",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("onu_identifier", sa.String(120), nullable=False),
        sa.Column("serial_number", sa.String(120), nullable=False),
        sa.Column("olt_id", sa.Uuid(), nullable=False),
        sa.Column("pon_id", sa.Uuid(), nullable=False),
        sa.Column("subscriber_id", sa.String(120)),
        sa.Column("status", sa.String(32), nullable=False, server_default="UNKNOWN"),
        sa.Column("last_seen", sa.DateTime(timezone=True)),
        sa.Column(
            "registration_status",
            sa.String(32),
            nullable=False,
            server_default="UNKNOWN",
        ),
        sa.Column("rx_power", sa.Float()),
        sa.Column("tx_power", sa.Float()),
        sa.Column("temperature", sa.Float()),
        sa.Column("distance", sa.Float()),
        sa.ForeignKeyConstraint(
            ["pon_id", "olt_id"],
            ["pons.id", "pons.olt_id"],
            ondelete="CASCADE",
            name="fk_onus_pon_olt",
        ),
        sa.ForeignKeyConstraint(
            ["subscriber_id"],
            ["subscribers.subscriber_id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("serial_number"),
        sa.UniqueConstraint("olt_id", "onu_identifier", name="uq_onus_olt_identifier"),
    )
    op.create_index("ix_onus_pon_id", "onus", ["pon_id"])
    op.create_index("ix_onus_subscriber_id", "onus", ["subscriber_id"])
    op.create_index("ix_onus_status", "onus", ["status"])

    op.create_table(
        "optical_thresholds",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("vendor", sa.String(120), nullable=False),
        sa.Column("technology", sa.String(32), nullable=False),
        sa.Column("device_model", sa.String(120)),
        sa.Column("metric_name", sa.String(64), nullable=False),
        sa.Column("unit", sa.String(32), nullable=False),
        sa.Column("critical_low", sa.Float()),
        sa.Column("warning_low", sa.Float()),
        sa.Column("warning_high", sa.Float()),
        sa.Column("critical_high", sa.Float()),
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
            "num_nonnulls(critical_low, warning_low, warning_high, critical_high) > 0",
            name="ck_optical_thresholds_has_boundary",
        ),
        sa.CheckConstraint(
            "metric_name IN ('RX_POWER', 'TX_POWER', 'TEMPERATURE', 'DISTANCE')",
            name="ck_optical_thresholds_metric_name",
        ),
        sa.CheckConstraint(
            "critical_low IS NULL OR warning_low IS NULL OR critical_low <= warning_low",
            name="ck_optical_thresholds_low_order",
        ),
        sa.CheckConstraint(
            "warning_low IS NULL OR warning_high IS NULL OR warning_low < warning_high",
            name="ck_optical_thresholds_warning_order",
        ),
        sa.CheckConstraint(
            "warning_high IS NULL OR critical_high IS NULL "
            "OR warning_high <= critical_high",
            name="ck_optical_thresholds_high_order",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_optical_threshold_scope_metric",
        "optical_thresholds",
        ["vendor", "technology", "device_model", "metric_name"],
        unique=True,
        postgresql_nulls_not_distinct=True,
    )


def downgrade() -> None:
    op.drop_index(
        "uq_optical_threshold_scope_metric", table_name="optical_thresholds"
    )
    op.drop_table("optical_thresholds")
    op.drop_index("ix_onus_status", table_name="onus")
    op.drop_index("ix_onus_subscriber_id", table_name="onus")
    op.drop_index("ix_onus_pon_id", table_name="onus")
    op.drop_table("onus")
    op.drop_index("ix_pons_olt_id", table_name="pons")
    op.drop_table("pons")
    op.drop_table("olts")
