from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.models.rules import Rule
from app.schemas.rules import RuleEvaluationRequest
from app.services.rules import evaluate_rule


def make_rule(
    *, conditions: list[dict[str, object]], duration_seconds: int = 0, enabled: bool = True
) -> Rule:
    now = datetime.now(UTC)
    return Rule(
        id=uuid4(),
        name="Test rule",
        description="Deterministic test rule",
        entity_type="INTERFACE",
        conditions=conditions,
        duration_seconds=duration_seconds,
        severity="HIGH",
        incident_category="CONGESTION",
        recommendation="Check the interface.",
        enabled=enabled,
        created_at=now,
        updated_at=now,
    )


def request(signals: dict[str, bool | float | str], duration: int = 0) -> RuleEvaluationRequest:
    return RuleEvaluationRequest(
        entity_type="INTERFACE",
        entity_id="interface-1",
        signals=signals,
        observed_duration_seconds=duration,
    )


def test_congestion_rule_requires_all_conditions_and_duration() -> None:
    rule = make_rule(
        conditions=[
            {"signal": "utilization_pct", "operator": "GT", "value": 90},
            {"signal": "packet_loss_pct", "operator": "GT", "value": 1},
        ],
        duration_seconds=600,
    )
    result, state, evidence = evaluate_rule(
        rule, request({"utilization_pct": 98.0, "packet_loss_pct": 2.0}, 599)
    )
    assert result is True
    assert state == "PENDING"
    assert all(item["matched"] for item in evidence)

    _, state, _ = evaluate_rule(
        rule, request({"utilization_pct": 98.0, "packet_loss_pct": 2.0}, 600)
    )
    assert state == "TRIGGERED"


def test_rule_evidence_explains_clear_and_disabled_states() -> None:
    rule = make_rule(
        conditions=[{"signal": "snmp_reachable", "operator": "EQ", "value": False}]
    )
    result, state, evidence = evaluate_rule(rule, request({"snmp_reachable": True}))
    assert result is False
    assert state == "CLEAR"
    assert evidence == [
        {
            "signal": "snmp_reachable",
            "operator": "EQ",
            "expected": False,
            "actual": True,
            "matched": False,
        }
    ]

    rule.enabled = False
    _, state, _ = evaluate_rule(rule, request({"snmp_reachable": False}))
    assert state == "DISABLED"


def test_rule_history_fields_and_constraints_exist() -> None:
    constraints = {item.name for item in Rule.__table__.constraints}
    assert "ck_rules_duration_nonnegative" in constraints
    assert "ck_rules_severity" in constraints


@pytest.mark.parametrize(
    ("operator", "actual", "expected", "matches"),
    [
        ("GT", 2.0, 1.0, True),
        ("GTE", 2.0, 2.0, True),
        ("LT", 1.0, 2.0, True),
        ("LTE", 2.0, 2.0, True),
        ("EQ", "CRITICAL", "CRITICAL", True),
        ("NE", True, False, True),
        ("GT", 1.0, 2.0, False),
    ],
)
def test_all_rule_operators_are_deterministic(
    operator: str,
    actual: bool | float | str,
    expected: bool | float | str,
    matches: bool,
) -> None:
    rule = make_rule(
        conditions=[{"signal": "value", "operator": operator, "value": expected}]
    )
    result, _, _ = evaluate_rule(rule, request({"value": actual}))
    assert result is matches
