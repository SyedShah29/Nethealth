"""Complete Phase 0-3 constraints, profiles, and RBAC capabilities.

Revision ID: 0005
Revises: 0004
"""

from uuid import UUID

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
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
    code: UUID(f"00000000-0000-4000-8000-{number:012d}")
    for number, code in enumerate(
        (
            "thresholds:manage",
            "collectors:manage",
            "rules:manage",
            "notifications:manage",
            "operational:read",
            "topology:read",
            "metrics:read",
            "subscribers:read",
            "incidents:manage",
            "incidents:acknowledge",
            "diagnostics:read",
            "jobs:read",
            "jobs:update",
            "field_notes:create",
            "dashboards:read",
        ),
        start=109,
    )
}

ROLE_CAPABILITIES = {
    "ADMIN": set(PERMISSION_IDS),
    "NOC_ENGINEER": {
        "operational:read",
        "topology:read",
        "metrics:read",
        "subscribers:read",
        "incidents:manage",
        "incidents:acknowledge",
        "diagnostics:read",
        "rules:manage",
    },
    "SUPPORT": {
        "operational:read",
        "subscribers:read",
        "incidents:manage",
        "diagnostics:read",
    },
    "FIELD_TECHNICIAN": {
        "jobs:read",
        "jobs:update",
        "diagnostics:read",
        "field_notes:create",
    },
    "VIEWER": {
        "dashboards:read",
        "operational:read",
        "topology:read",
        "metrics:read",
    },
}

DEVICE_TYPES = (
    "CORE_ROUTER",
    "EDGE_ROUTER",
    "BNG",
    "BRAS",
    "AGGREGATION_SWITCH",
    "ACCESS_SWITCH",
    "OLT",
    "OTHER",
)


def upgrade() -> None:
    op.add_column(
        "collector_profiles",
        sa.Column("collector_type", sa.String(16), nullable=False, server_default="ICMP"),
    )
    op.add_column(
        "collector_profiles", sa.Column("configuration_key", sa.String(120), nullable=True)
    )
    op.add_column(
        "collector_profiles",
        sa.Column("interval_seconds", sa.Integer(), nullable=False, server_default="60"),
    )
    op.add_column(
        "collector_profiles",
        sa.Column("failure_threshold", sa.Integer(), nullable=False, server_default="3"),
    )
    op.create_check_constraint(
        "ck_collector_profiles_type",
        "collector_profiles",
        "collector_type IN ('ICMP', 'SNMP')",
    )
    op.create_check_constraint(
        "ck_collector_profiles_interval",
        "collector_profiles",
        "interval_seconds > 0",
    )
    op.create_check_constraint(
        "ck_collector_profiles_failure_threshold",
        "collector_profiles",
        "failure_threshold > 0",
    )
    allowed_types = ", ".join(f"'{value}'" for value in DEVICE_TYPES)
    op.create_check_constraint(
        "ck_devices_device_type", "devices", f"device_type IN ({allowed_types})"
    )
    op.create_unique_constraint(
        "uq_collector_status_device_type",
        "collector_status",
        ["device_id", "collector_type"],
    )
    op.create_index("ix_collector_status_device_id", "collector_status", ["device_id"])

    permissions = sa.table(
        "permissions",
        sa.column("id", sa.Uuid()),
        sa.column("code", sa.String()),
        sa.column("description", sa.String()),
    )
    op.bulk_insert(
        permissions,
        [
            {
                "id": permission_id,
                "code": code,
                "description": f"{code.replace(':', ' ')} capability",
            }
            for code, permission_id in PERMISSION_IDS.items()
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
            {
                "role_id": ROLE_IDS[role],
                "permission_id": PERMISSION_IDS[permission],
            }
            for role, permissions in ROLE_CAPABILITIES.items()
            for permission in permissions
        ],
    )


def downgrade() -> None:
    role_permissions = sa.table(
        "role_permissions",
        sa.column("permission_id", sa.Uuid()),
    )
    permissions = sa.table("permissions", sa.column("id", sa.Uuid()))
    permission_ids = list(PERMISSION_IDS.values())
    op.execute(role_permissions.delete().where(role_permissions.c.permission_id.in_(permission_ids)))
    op.execute(permissions.delete().where(permissions.c.id.in_(permission_ids)))
    op.drop_index("ix_collector_status_device_id", table_name="collector_status")
    op.drop_constraint(
        "uq_collector_status_device_type", "collector_status", type_="unique"
    )
    op.drop_constraint("ck_devices_device_type", "devices", type_="check")
    op.drop_constraint(
        "ck_collector_profiles_failure_threshold", "collector_profiles", type_="check"
    )
    op.drop_constraint(
        "ck_collector_profiles_interval", "collector_profiles", type_="check"
    )
    op.drop_constraint("ck_collector_profiles_type", "collector_profiles", type_="check")
    op.drop_column("collector_profiles", "failure_threshold")
    op.drop_column("collector_profiles", "interval_seconds")
    op.drop_column("collector_profiles", "configuration_key")
    op.drop_column("collector_profiles", "collector_type")
