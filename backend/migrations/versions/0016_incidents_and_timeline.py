"""Add incident management and timeline history.

Revision ID: 0016
Revises: 0015
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "incidents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("description", sa.String(2000), nullable=False),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("root_cause", sa.String(160)),
        sa.Column("primary_entity_type", sa.String(32), nullable=False),
        sa.Column("primary_entity_id", sa.String(255), nullable=False),
        sa.Column("affected_subscribers", postgresql.JSONB(), nullable=False),
        sa.Column("affected_topology", postgresql.JSONB(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), nullable=False),
        sa.Column("recommendations", postgresql.JSONB(), nullable=False),
        sa.Column("assigned_team", sa.String(120)),
        sa.Column("assigned_user_id", sa.Uuid()),
        sa.Column("comments", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('OPEN', 'ACKNOWLEDGED', 'INVESTIGATING', 'RESOLVED', 'CLOSED')",
            name="ck_incidents_status",
        ),
        sa.CheckConstraint(
            "severity IN ('INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name="ck_incidents_severity",
        ),
        sa.ForeignKeyConstraint(["assigned_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_incidents_status_severity", "incidents", ["status", "severity"])
    op.create_index(
        "ix_incidents_dedup_lookup",
        "incidents",
        ["category", "primary_entity_type", "primary_entity_id", "status"],
    )
    op.create_table(
        "incident_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("incident_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("message", sa.String(1000), nullable=False),
        sa.Column("actor_user_id", sa.Uuid()),
        sa.Column("details", postgresql.JSONB(), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_incident_events_incident_time", "incident_events", ["incident_id", "occurred_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_incident_events_incident_time", table_name="incident_events")
    op.drop_table("incident_events")
    op.drop_index("ix_incidents_dedup_lookup", table_name="incidents")
    op.drop_index("ix_incidents_status_severity", table_name="incidents")
    op.drop_table("incidents")
