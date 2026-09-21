from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.errors import AppError
from app.models.enums import AuditEventType
from app.models.rules import Rule, RuleEvaluation
from app.repositories.rules import RuleRepository
from app.schemas.operations import IncidentCreate
from app.schemas.rules import RuleCondition, RuleEvaluationRequest
from app.schemas.topology import EntityReference
from app.services.audit import AuditService
from app.services.operations import IncidentService


def evaluate_condition(
    condition: RuleCondition, signals: dict[str, bool | float | str]
) -> dict[str, Any]:
    actual = signals.get(condition.signal)
    expected = condition.value
    matched = False
    if actual is not None:
        if condition.operator == "EQ":
            matched = actual == expected
        elif condition.operator == "NE":
            matched = actual != expected
        elif (
            isinstance(actual, (int, float))
            and not isinstance(actual, bool)
            and isinstance(expected, (int, float))
            and not isinstance(expected, bool)
        ):
            actual_number = float(actual)
            expected_number = float(expected)
            comparisons = {
                "GT": actual_number > expected_number,
                "GTE": actual_number >= expected_number,
                "LT": actual_number < expected_number,
                "LTE": actual_number <= expected_number,
            }
            matched = comparisons.get(condition.operator.value, False)
    return {
        "signal": condition.signal,
        "operator": condition.operator.value,
        "expected": expected,
        "actual": actual,
        "matched": matched,
    }


def evaluate_rule(
    rule: Rule, request: RuleEvaluationRequest
) -> tuple[bool, str, list[dict[str, Any]]]:
    conditions = [RuleCondition.model_validate(item) for item in rule.conditions]
    evidence = [evaluate_condition(item, request.signals) for item in conditions]
    conditions_met = all(bool(item["matched"]) for item in evidence)
    if not rule.enabled:
        trigger_state = "DISABLED"
    elif not conditions_met:
        trigger_state = "CLEAR"
    elif request.observed_duration_seconds < rule.duration_seconds:
        trigger_state = "PENDING"
    else:
        trigger_state = "TRIGGERED"
    return conditions_met, trigger_state, evidence


class RuleService:
    def __init__(
        self,
        repository: RuleRepository,
        audit: AuditService,
        incidents: IncidentService | None = None,
    ) -> None:
        self.repository = repository
        self.audit = audit
        self.incidents = incidents

    async def list_rules(self, enabled: bool | None = None) -> list[Rule]:
        return await self.repository.list_rules(enabled=enabled)

    async def get_rule(self, rule_id: UUID) -> Rule:
        rule = await self.repository.get_rule(rule_id)
        if rule is None:
            raise AppError("RULE_NOT_FOUND", "Rule not found.", 404)
        return rule

    async def create_rule(self, data: dict[str, Any], actor_user_id: UUID) -> Rule:
        try:
            rule = await self.repository.add_rule(Rule(**data))
            await self._audit(rule.id, "created", actor_user_id)
            await self.repository.session.commit()
            return rule
        except IntegrityError as exc:
            await self.repository.session.rollback()
            raise AppError("RULE_CONFLICT", "Rule name already exists.", 409) from exc

    async def update_rule(
        self, rule_id: UUID, data: dict[str, Any], actor_user_id: UUID
    ) -> Rule:
        rule = await self.get_rule(rule_id)
        for key, value in data.items():
            setattr(rule, key, value)
        try:
            await self.repository.session.flush()
            await self._audit(rule.id, "updated", actor_user_id)
            await self.repository.session.commit()
            return rule
        except IntegrityError as exc:
            await self.repository.session.rollback()
            raise AppError("RULE_CONFLICT", "Rule name already exists.", 409) from exc

    async def delete_rule(self, rule_id: UUID, actor_user_id: UUID) -> None:
        rule = await self.get_rule(rule_id)
        await self.repository.delete_rule(rule)
        await self._audit(rule.id, "deleted", actor_user_id)
        await self.repository.session.commit()

    async def evaluate(
        self, rule_id: UUID, request: RuleEvaluationRequest
    ) -> RuleEvaluation:
        rule = await self.get_rule(rule_id)
        if request.entity_type.upper() != rule.entity_type:
            raise AppError(
                "RULE_ENTITY_TYPE_MISMATCH",
                "The evaluation entity type does not match the rule.",
                422,
            )
        result, trigger_state, evidence = evaluate_rule(rule, request)
        evaluation = await self.repository.add_evaluation(
            RuleEvaluation(
                rule_id=rule.id,
                entity_type=request.entity_type.upper(),
                entity_id=request.entity_id,
                result=result,
                evidence=evidence,
                trigger_state=trigger_state,
            )
        )
        if trigger_state == "TRIGGERED" and self.incidents is not None:
            await self.incidents.create_or_attach(
                IncidentCreate(
                    category=rule.incident_category,
                    severity=rule.severity,
                    title=f"{rule.name}: {request.entity_id}",
                    description=rule.description,
                    primary_entity=EntityReference(
                        entity_type=request.entity_type.upper(),
                        entity_id=request.entity_id,
                    ),
                    evidence=evidence,
                    recommendations=[rule.recommendation],
                )
            )
        else:
            await self.repository.session.commit()
        return evaluation

    async def list_evaluations(
        self,
        *,
        rule_id: UUID | None,
        entity_type: str | None,
        entity_id: str | None,
        limit: int,
    ) -> list[RuleEvaluation]:
        return await self.repository.list_evaluations(
            rule_id=rule_id,
            entity_type=entity_type.upper() if entity_type else None,
            entity_id=entity_id,
            limit=limit,
        )

    async def _audit(
        self, rule_id: UUID, action: str, actor_user_id: UUID
    ) -> None:
        await self.audit.record(
            AuditEventType.CONFIGURATION_CHANGED,
            success=True,
            actor_user_id=actor_user_id,
            event_metadata={
                "resource_type": "Rule",
                "resource_id": str(rule_id),
                "action": action,
            },
        )
