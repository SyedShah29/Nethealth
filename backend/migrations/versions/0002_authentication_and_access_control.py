"""Add authentication and access-control schema.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-19
"""

from collections.abc import Sequence
from uuid import UUID

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

ROLE_IDS = {
    "ADMIN": UUID("00000000-0000-4000-8000-000000000001"),
    "NOC_ENGINEER": UUID("00000000-0000-4000-8000-000000000002"),
    "SUPPORT": UUID("00000000-0000-4000-8000-000000000003"),
    "FIELD_TECHNICIAN": UUID("00000000-0000-4000-8000-000000000004"),
    "VIEWER": UUID("00000000-0000-4000-8000-000000000005"),
}
PERMISSION_IDS = {
    "users:manage": UUID("00000000-0000-4000-8000-000000000101"),
    "roles:read": UUID("00000000-0000-4000-8000-000000000102"),
    "audit:read": UUID("00000000-0000-4000-8000-000000000103"),
}


def upgrade() -> None:
    roles = op.create_table(
        "roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=32), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    permissions = op.create_table(
        "permissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("permission_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )
    op.bulk_insert(
        roles,
        [
            {"id": ROLE_IDS["ADMIN"], "name": "ADMIN", "description": "Full administration"},
            {
                "id": ROLE_IDS["NOC_ENGINEER"],
                "name": "NOC_ENGINEER",
                "description": "Network operations engineer",
            },
            {"id": ROLE_IDS["SUPPORT"], "name": "SUPPORT", "description": "Support staff"},
            {
                "id": ROLE_IDS["FIELD_TECHNICIAN"],
                "name": "FIELD_TECHNICIAN",
                "description": "Field technician",
            },
            {"id": ROLE_IDS["VIEWER"], "name": "VIEWER", "description": "Read-only user"},
        ],
    )
    op.bulk_insert(
        permissions,
        [
            {
                "id": PERMISSION_IDS["users:manage"],
                "code": "users:manage",
                "description": "Create, update, disable, and assign roles to users",
            },
            {
                "id": PERMISSION_IDS["roles:read"],
                "code": "roles:read",
                "description": "View roles and permissions",
            },
            {
                "id": PERMISSION_IDS["audit:read"],
                "code": "audit:read",
                "description": "View authentication and access-control audit events",
            },
        ],
    )
    role_permissions = sa.table(
        "role_permissions",
        sa.column("role_id", sa.Uuid()),
        sa.column("permission_id", sa.Uuid()),
    )
    op.bulk_insert(
        role_permissions,
        [
            {"role_id": ROLE_IDS["ADMIN"], "permission_id": permission_id}
            for permission_id in PERMISSION_IDS.values()
        ],
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("failed_login_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("failed_login_count >= 0", name="ck_users_failed_login_count"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role_id", "users", ["role_id"])

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_auth_sessions_expires_at", "auth_sessions", ["expires_at"])
    op.create_index("ix_auth_sessions_token_hash", "auth_sessions", ["token_hash"], unique=True)
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("target_user_id", sa.Uuid(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("subject_fingerprint", sa.String(length=64), nullable=True),
        sa.Column(
            "event_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")
        ),
        sa.Column(
            "occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    op.create_index("ix_audit_logs_event_type", "audit_logs", ["event_type"])
    op.create_index("ix_audit_logs_occurred_at", "audit_logs", ["occurred_at"])
    op.create_index("ix_audit_logs_target_user_id", "audit_logs", ["target_user_id"])


def downgrade() -> None:
    _drop_indexes(
        "audit_logs",
        (
            "ix_audit_logs_target_user_id",
            "ix_audit_logs_occurred_at",
            "ix_audit_logs_event_type",
            "ix_audit_logs_actor_user_id",
        ),
    )
    op.drop_table("audit_logs")
    _drop_indexes(
        "auth_sessions",
        (
            "ix_auth_sessions_user_id",
            "ix_auth_sessions_token_hash",
            "ix_auth_sessions_expires_at",
        ),
    )
    op.drop_table("auth_sessions")
    _drop_indexes("users", ("ix_users_role_id", "ix_users_email"))
    op.drop_table("users")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")


def _drop_indexes(table_name: str, index_names: Sequence[str]) -> None:
    for index_name in index_names:
        op.drop_index(index_name, table_name=table_name)
