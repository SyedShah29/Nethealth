"""Add configurable rules and evaluation history.

Revision ID: 0012
Revises: 0011
"""

from uuid import UUID

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None

RULE_IDS = {
    "congestion": UUID("00000000-0000-4000-8000-000000000201"),
    "optical": UUID("00000000-0000-4000-8000-000000000202"),
    "device": UUID("00000000-0000-4000-8000-000000000203"),
    "subscriber": UUID("00000000-0000-4000-8000-000000000204"),
}


def upgrade() -> None:
    op.create_table(
        "rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.String(1000), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("conditions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "duration_seconds", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("incident_category", sa.String(80), nullable=False),
        sa.Column("recommendation", sa.String(1000), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "duration_seconds >= 0", name="ck_rules_duration_nonnegative"
        ),
        sa.CheckConstraint(
            "severity IN ('INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name="ck_rules_severity",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(
        "ix_rules_entity_enabled", "rules", ["entity_type", "enabled"]
    )
    op.create_table(
        "rule_evaluations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("rule_id", sa.Uuid(), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("entity_id", sa.String(255), nullable=False),
        sa.Column(
            "evaluated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("result", sa.Boolean(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("trigger_state", sa.String(16), nullable=False),
        sa.CheckConstraint(
            "trigger_state IN ('DISABLED', 'CLEAR', 'PENDING', 'TRIGGERED')",
            name="ck_rule_evaluations_trigger_state",
        ),
        sa.ForeignKeyConstraint(["rule_id"], ["rules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_rule_evaluations_entity_time",
        "rule_evaluations",
        ["entity_type", "entity_id", "evaluated_at"],
    )
    op.create_index(
        "ix_rule_evaluations_rule_time",
        "rule_evaluations",
        ["rule_id", "evaluated_at"],
    )

    rules = sa.table(
        "rules",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("description", sa.String()),
        sa.column("entity_type", sa.String()),
        sa.column("conditions", postgresql.JSONB()),
        sa.column("duration_seconds", sa.Integer()),
        sa.column("severity", sa.String()),
        sa.column("incident_category", sa.String()),
        sa.column("recommendation", sa.String()),
        sa.column("enabled", sa.Boolean()),
    )
    op.bulk_insert(
        rules,
        [
            {
                "id": RULE_IDS["congestion"],
                "name": "Interface congestion",
                "description": "Sustained high utilization with packet loss.",
                "entity_type": "INTERFACE",
                "conditions": [
                    {"signal": "utilization_pct", "operator": "GT", "value": 90},
                    {"signal": "packet_loss_pct", "operator": "GT", "value": 1},
                ],
                "duration_seconds": 600,
                "severity": "HIGH",
                "incident_category": "CONGESTION",
                "recommendation": "Check interface capacity, errors, and queue drops.",
                "enabled": True,
            },
            {
                "id": RULE_IDS["optical"],
                "name": "Critical ONU optical signal",
                "description": "ONU optical classification crosses its configured threshold.",
                "entity_type": "ONU",
                "conditions": [
                    {"signal": "optical_class", "operator": "EQ", "value": "CRITICAL"}
                ],
                "duration_seconds": 0,
                "severity": "CRITICAL",
                "incident_category": "OPTICAL_SIGNAL_CRITICAL",
                "recommendation": "Inspect optical levels, connectors, and fiber path.",
                "enabled": True,
            },
            {
                "id": RULE_IDS["device"],
                "name": "Device unreachable",
                "description": "ICMP failure threshold reached and SNMP is unavailable.",
                "entity_type": "DEVICE",
                "conditions": [
                    {"signal": "icmp_failures", "operator": "GTE", "value": 3},
                    {"signal": "snmp_reachable", "operator": "EQ", "value": False},
                ],
                "duration_seconds": 0,
                "severity": "CRITICAL",
                "incident_category": "DEVICE_UNREACHABLE",
                "recommendation": "Check device power, reachability, and upstream path.",
                "enabled": True,
            },
            {
                "id": RULE_IDS["subscriber"],
                "name": "Unstable subscriber",
                "description": (
                    "Disconnect count exceeds the configured evaluation-window threshold."
                ),
                "entity_type": "SUBSCRIBER",
                "conditions": [
                    {"signal": "disconnect_count", "operator": "GT", "value": 3}
                ],
                "duration_seconds": 3600,
                "severity": "MEDIUM",
                "incident_category": "UNSTABLE_SUBSCRIBER",
                "recommendation": "Check session history, optical health, and access stability.",
                "enabled": True,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_rule_evaluations_rule_time", table_name="rule_evaluations")
    op.drop_index("ix_rule_evaluations_entity_time", table_name="rule_evaluations")
    op.drop_table("rule_evaluations")
    op.drop_index("ix_rules_entity_enabled", table_name="rules")
    op.drop_table("rules")
