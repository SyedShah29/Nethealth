"""Add the Phase 5 subscriber operational model.

Revision ID: 0008
Revises: 0007
"""

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subscribers",
        sa.Column("subscriber_id", sa.String(120), nullable=False),
        sa.Column("external_reference", sa.String(255)),
        sa.Column("package_speed", sa.BigInteger()),
        sa.Column("status", sa.String(32), nullable=False, server_default="UNKNOWN"),
        sa.Column("nas_id", sa.String(120)),
        sa.Column("olt_id", sa.String(120)),
        sa.Column("pon_id", sa.String(120)),
        sa.Column("onu_id", sa.String(120)),
        sa.Column("current_ip", sa.String(64)),
        sa.Column("mac_address", sa.String(32)),
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
            "package_speed IS NULL OR package_speed >= 0",
            name="ck_subscribers_package_speed_nonnegative",
        ),
        sa.PrimaryKeyConstraint("subscriber_id"),
    )
    op.create_index(
        "ix_subscribers_external_reference",
        "subscribers",
        ["external_reference"],
        unique=True,
    )
    for field in ("status", "nas_id", "olt_id", "pon_id", "onu_id"):
        op.create_index(f"ix_subscribers_{field}", "subscribers", [field])

    op.create_table(
        "subscriber_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("subscriber_id", sa.String(120), nullable=False),
        sa.Column("session_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("session_end", sa.DateTime(timezone=True)),
        sa.Column("nas", sa.String(120), nullable=False),
        sa.Column("ip_address", sa.String(64)),
        sa.Column("disconnect_reason", sa.String(255)),
        sa.Column("duration", sa.Integer()),
        sa.CheckConstraint(
            "session_end IS NULL OR session_end >= session_start",
            name="ck_subscriber_sessions_time_order",
        ),
        sa.CheckConstraint(
            "duration IS NULL OR duration >= 0",
            name="ck_subscriber_sessions_duration_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["subscriber_id"],
            ["subscribers.subscriber_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_subscriber_sessions_subscriber_start",
        "subscriber_sessions",
        ["subscriber_id", "session_start"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_subscriber_sessions_subscriber_start",
        table_name="subscriber_sessions",
    )
    op.drop_table("subscriber_sessions")
    for field in ("onu_id", "pon_id", "olt_id", "nas_id", "status"):
        op.drop_index(f"ix_subscribers_{field}", table_name="subscribers")
    op.drop_index("ix_subscribers_external_reference", table_name="subscribers")
    op.drop_table("subscribers")
