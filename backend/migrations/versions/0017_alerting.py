"""Add alert routing channels, rules, and deduplicated deliveries.

Revision ID: 0017
Revises: 0016
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_channels",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("channel_type", sa.String(20), nullable=False),
        sa.Column("configuration_key", sa.String(120)),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.CheckConstraint(
            "channel_type IN ('EMAIL', 'SMS', 'WHATSAPP', 'TELEGRAM', 'DASHBOARD', 'WEB_PUSH')",
            name="ck_notification_channels_type",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "notification_rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("incident_category", sa.String(80), nullable=False),
        sa.Column("minimum_severity", sa.String(16), nullable=False),
        sa.Column("teams", postgresql.JSONB(), nullable=False),
        sa.Column("channel_ids", postgresql.JSONB(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "notification_deliveries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("incident_id", sa.Uuid(), nullable=False),
        sa.Column("channel_id", sa.Uuid(), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["channel_id"], ["notification_channels.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fingerprint", name="uq_notification_deliveries_fingerprint"),
    )
    op.create_index(
        "ix_notification_deliveries_incident", "notification_deliveries", ["incident_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_notification_deliveries_incident", table_name="notification_deliveries")
    op.drop_table("notification_deliveries")
    op.drop_table("notification_rules")
    op.drop_table("notification_channels")
