"""Reconcile Phase 2 inventory indexes with ORM metadata.

Revision ID: 0009
Revises: 0008
"""

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_devices_site_id",
        "devices",
        ["site_id"],
    )
    op.create_index(
        "ix_interfaces_device_id",
        "interfaces",
        ["device_id"],
    )
    op.create_index(
        "ix_collector_assignments_device_id",
        "collector_assignments",
        ["device_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_collector_assignments_device_id",
        table_name="collector_assignments",
    )
    op.drop_index("ix_interfaces_device_id", table_name="interfaces")
    op.drop_index("ix_devices_site_id", table_name="devices")
