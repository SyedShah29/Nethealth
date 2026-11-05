from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rules import Rule, RuleEvaluation


class RuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_rules(self, *, enabled: bool | None = None) -> list[Rule]:
        statement = select(Rule)
        if enabled is not None:
            statement = statement.where(Rule.enabled == enabled)
        result = await self.session.execute(statement.order_by(Rule.name))
        return list(result.scalars())

    async def get_rule(self, rule_id: UUID) -> Rule | None:
        return await self.session.get(Rule, rule_id)

    async def add_rule(self, rule: Rule) -> Rule:
        self.session.add(rule)
        await self.session.flush()
        return rule

    async def delete_rule(self, rule: Rule) -> None:
        await self.session.delete(rule)
        await self.session.flush()

    async def add_evaluation(self, evaluation: RuleEvaluation) -> RuleEvaluation:
        self.session.add(evaluation)
        await self.session.flush()
        return evaluation

    async def list_evaluations(
        self,
        *,
        rule_id: UUID | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        limit: int = 100,
    ) -> list[RuleEvaluation]:
        statement = select(RuleEvaluation)
        if rule_id is not None:
            statement = statement.where(RuleEvaluation.rule_id == rule_id)
        if entity_type is not None:
            statement = statement.where(RuleEvaluation.entity_type == entity_type)
        if entity_id is not None:
            statement = statement.where(RuleEvaluation.entity_id == entity_id)
        result = await self.session.execute(
            statement.order_by(RuleEvaluation.evaluated_at.desc()).limit(limit)
        )
        return list(result.scalars())
