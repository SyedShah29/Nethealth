"""Add Phase 2 network inventory metadata."""
from uuid import UUID
import sqlalchemy as sa
from alembic import op
revision = "0003"; down_revision = "0002"; branch_labels = None; depends_on = None
PERMS = {
 "inventory:read": UUID("00000000-0000-4000-8000-000000000104"), "sites:manage": UUID("00000000-0000-4000-8000-000000000105"),
 "devices:manage": UUID("00000000-0000-4000-8000-000000000106"), "interfaces:manage": UUID("00000000-0000-4000-8000-000000000107"), "collector_assignments:manage": UUID("00000000-0000-4000-8000-000000000108")}
ROLES = {"ADMIN": UUID("00000000-0000-4000-8000-000000000001"), "NOC_ENGINEER": UUID("00000000-0000-4000-8000-000000000002"), "VIEWER": UUID("00000000-0000-4000-8000-000000000005")}
def upgrade() -> None:
    op.create_table("sites", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("name", sa.String(120), nullable=False), sa.Column("code", sa.String(32), nullable=False, unique=True), sa.Column("region", sa.String(120), nullable=False), sa.Column("latitude", sa.Numeric(9,6)), sa.Column("longitude", sa.Numeric(9,6)), sa.Column("description", sa.String(500)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("collector_profiles", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("name", sa.String(120), nullable=False, unique=True), sa.Column("description", sa.String(500)), sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_table("devices", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("name", sa.String(120), nullable=False), sa.Column("hostname", sa.String(255), nullable=False), sa.Column("management_ip", sa.String(64), nullable=False), sa.Column("device_type", sa.String(32), nullable=False), sa.Column("vendor", sa.String(120)), sa.Column("model", sa.String(120)), sa.Column("site_id", sa.Uuid(), sa.ForeignKey("sites.id", ondelete="RESTRICT"), nullable=False), sa.Column("monitoring_enabled", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("collector_profile_id", sa.Uuid(), sa.ForeignKey("collector_profiles.id", ondelete="SET NULL")), sa.Column("status", sa.String(32), nullable=False, server_default="UNKNOWN"), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("interfaces", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("device_id", sa.Uuid(), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False), sa.Column("name", sa.String(120), nullable=False), sa.Column("description", sa.String(500)), sa.Column("speed", sa.Integer()), sa.Column("mac_address", sa.String(32)), sa.Column("admin_status", sa.String(16)), sa.Column("oper_status", sa.String(16)))
    op.create_table("collector_assignments", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("device_id", sa.Uuid(), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False), sa.Column("collector_profile_id", sa.Uuid(), sa.ForeignKey("collector_profiles.id", ondelete="CASCADE"), nullable=False), sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()))
    permissions = sa.table("permissions", sa.column("id", sa.Uuid()), sa.column("code", sa.String()), sa.column("description", sa.String()))
    op.bulk_insert(permissions, [{"id": i, "code": c, "description": f"{c} permission"} for c,i in PERMS.items()])
    rp = sa.table("role_permissions", sa.column("role_id", sa.Uuid()), sa.column("permission_id", sa.Uuid()))
    rows = [{"role_id": ROLES["ADMIN"], "permission_id": p} for p in PERMS.values()]
    rows += [{"role_id": ROLES[r], "permission_id": PERMS["inventory:read"]} for r in ("NOC_ENGINEER", "VIEWER")]
    op.bulk_insert(rp, rows)
def downgrade() -> None:
    op.drop_table("collector_assignments"); op.drop_table("interfaces"); op.drop_table("devices"); op.drop_table("collector_profiles"); op.drop_table("sites")
