"""Add field, escalation, and maintenance workflows.

Revision ID: 0019
Revises: 0018
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "field_tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("incident_id", sa.Uuid(), nullable=False),
        sa.Column("subscriber_id", sa.String(120)),
        sa.Column("olt_id", sa.String(120)),
        sa.Column("pon_id", sa.String(120)),
        sa.Column("onu_id", sa.String(120)),
        sa.Column("last_rx", sa.Float()),
        sa.Column("current_status", sa.String(32), nullable=False),
        sa.Column("recommended_checks", postgresql.JSONB(), nullable=False),
        sa.Column("assigned_technician_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("notes", postgresql.JSONB(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("restored_at", sa.DateTime(timezone=True)),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('ASSIGNED', 'ACCEPTED', 'IN_PROGRESS', 'RESTORED', 'CLOSED')",
            name="ck_field_tasks_status",
        ),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["subscriber_id"], ["subscribers.subscriber_id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["assigned_technician_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("incident_id"),
    )
    op.create_index(
        "ix_field_tasks_technician_status", "field_tasks", ["assigned_technician_id", "status"]
    )
    op.create_table(
        "field_photos",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("uploaded_by", sa.Uuid(), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(80), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["task_id"], ["field_tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_field_photos_task_time", "field_photos", ["task_id", "created_at"])
    op.create_table(
        "escalation_policies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("incident_category", sa.String(80)),
        sa.Column("minimum_severity", sa.String(16), nullable=False),
        sa.Column("steps", postgresql.JSONB(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "escalation_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("incident_id", sa.Uuid(), nullable=False),
        sa.Column("policy_id", sa.Uuid(), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("team", sa.String(120), nullable=False),
        sa.Column("channel_ids", postgresql.JSONB(), nullable=False),
        sa.Column(
            "escalated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["policy_id"], ["escalation_policies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "incident_id", "policy_id", "step_index", name="uq_escalation_event_step"
        ),
    )
    op.create_table(
        "maintenance_windows",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("scope_type", sa.String(16), nullable=False),
        sa.Column("scope_id", sa.String(255), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(1000), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("scope_type IN ('DEVICE', 'SITE')", name="ck_maintenance_scope"),
        sa.CheckConstraint("ends_at > starts_at", name="ck_maintenance_time_order"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_maintenance_scope_time",
        "maintenance_windows",
        ["scope_type", "scope_id", "starts_at", "ends_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_maintenance_scope_time", table_name="maintenance_windows")
    op.drop_table("maintenance_windows")
    op.drop_table("escalation_events")
    op.drop_table("escalation_policies")
    op.drop_index("ix_field_photos_task_time", table_name="field_photos")
    op.drop_table("field_photos")
    op.drop_index("ix_field_tasks_technician_status", table_name="field_tasks")
    op.drop_table("field_tasks")
