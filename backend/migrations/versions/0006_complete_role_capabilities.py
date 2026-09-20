"""Complete role-management and least-privilege capability mappings.

Revision ID: 0006
Revises: 0005
"""

from uuid import UUID

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

ROLE_IDS = {
    "ADMIN": UUID("00000000-0000-4000-8000-000000000001"),
    "NOC_ENGINEER": UUID("00000000-0000-4000-8000-000000000002"),
    "SUPPORT": UUID("00000000-0000-4000-8000-000000000003"),
    "FIELD_TECHNICIAN": UUID("00000000-0000-4000-8000-000000000004"),
}
PERMISSION_IDS = {
    "roles:manage": UUID("00000000-0000-4000-8000-000000000124"),
    "incidents:read": UUID("00000000-0000-4000-8000-000000000125"),
    "field_photos:upload": UUID("00000000-0000-4000-8000-000000000126"),
}


def upgrade() -> None:
    permissions = sa.table(
        "permissions",
        sa.column("id", sa.Uuid()),
        sa.column("code", sa.String()),
        sa.column("description", sa.String()),
    )
    op.bulk_insert(
        permissions,
        [
            {"id": value, "code": code, "description": f"{code.replace(':', ' ')} capability"}
            for code, value in PERMISSION_IDS.items()
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
                "role_id": ROLE_IDS["ADMIN"],
                "permission_id": PERMISSION_IDS[permission],
            }
            for permission in PERMISSION_IDS
        ]
        + [
            {
                "role_id": ROLE_IDS["NOC_ENGINEER"],
                "permission_id": PERMISSION_IDS["incidents:read"],
            },
            {
                "role_id": ROLE_IDS["SUPPORT"],
                "permission_id": PERMISSION_IDS["incidents:read"],
            },
            {
                "role_id": ROLE_IDS["FIELD_TECHNICIAN"],
                "permission_id": PERMISSION_IDS["field_photos:upload"],
            },
        ],
    )
    op.execute(
        sa.text(
            "DELETE FROM role_permissions WHERE role_id = :support_id "
            "AND permission_id = (SELECT id FROM permissions WHERE code = 'incidents:manage')"
        ).bindparams(support_id=ROLE_IDS["SUPPORT"])
    )


def downgrade() -> None:
    role_permissions = sa.table(
        "role_permissions",
        sa.column("role_id", sa.Uuid()),
        sa.column("permission_id", sa.Uuid()),
    )
    permissions = sa.table("permissions", sa.column("id", sa.Uuid()))
    permission_ids = list(PERMISSION_IDS.values())
    op.execute(role_permissions.delete().where(role_permissions.c.permission_id.in_(permission_ids)))
    op.execute(permissions.delete().where(permissions.c.id.in_(permission_ids)))
    manage_permission_id = op.get_bind().execute(
        sa.text("SELECT id FROM permissions WHERE code = 'incidents:manage'")
    ).scalar_one()
    op.bulk_insert(
        role_permissions,
        [{"role_id": ROLE_IDS["SUPPORT"], "permission_id": manage_permission_id}],
    )
