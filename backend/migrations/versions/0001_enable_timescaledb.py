"""Enable the TimescaleDB extension.

Revision ID: 0001
Revises:
Create Date: 2026-09-19
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")


def downgrade() -> None:
    # The extension may own future time-series objects, so downgrades retain it.
    pass
