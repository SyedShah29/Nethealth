"""Persist collector health status."""
import sqlalchemy as sa
from alembic import op
revision = "0004"; down_revision = "0003"; branch_labels = None; depends_on = None
def upgrade() -> None:
    op.create_table("collector_status", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("device_id", sa.Uuid(), nullable=False), sa.Column("collector_type", sa.String(32), nullable=False), sa.Column("last_successful_poll", sa.DateTime(timezone=True)), sa.Column("last_failed_poll", sa.DateTime(timezone=True)), sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("latency_ms", sa.Float()), sa.Column("current_health", sa.String(32), nullable=False, server_default="UNKNOWN"), sa.Column("current_worker", sa.String(120)), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
def downgrade() -> None: op.drop_table("collector_status")
