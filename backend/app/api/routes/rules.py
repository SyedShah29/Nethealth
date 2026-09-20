from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies.auth import (
    get_rule_service,
    require_permission,
    require_trusted_origin,
)
from app.models.auth import User
from app.models.enums import PermissionCode
from app.models.rules import Rule, RuleEvaluation
from app.schemas.rules import (
    RuleCreate,
    RuleEvaluationRequest,
    RuleEvaluationResponse,
    RuleResponse,
    RuleUpdate,
)
from app.services.rules import RuleService

router = APIRouter(prefix="/rules")
read_rules = require_permission(PermissionCode.OPERATIONAL_READ.value)
manage_rules = require_permission(PermissionCode.RULES_MANAGE.value)


@router.get("", response_model=list[RuleResponse])
async def list_rules(
    service: Annotated[RuleService, Depends(get_rule_service)],
    _user: Annotated[User, Depends(read_rules)],
    enabled: bool | None = None,
) -> list[Rule]:
    return await service.list_rules(enabled)


@router.post(
    "",
    response_model=RuleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_trusted_origin)],
)
async def create_rule(
    payload: RuleCreate,
    service: Annotated[RuleService, Depends(get_rule_service)],
    user: Annotated[User, Depends(manage_rules)],
) -> Rule:
    return await service.create_rule(payload.model_dump(mode="json"), user.id)


@router.get("/evaluations", response_model=list[RuleEvaluationResponse])
async def list_evaluations(
    service: Annotated[RuleService, Depends(get_rule_service)],
    _user: Annotated[User, Depends(read_rules)],
    rule_id: UUID | None = None,
    entity_type: Annotated[str | None, Query(max_length=32)] = None,
    entity_id: Annotated[str | None, Query(max_length=255)] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[RuleEvaluation]:
    return await service.list_evaluations(
        rule_id=rule_id,
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
    )


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: UUID,
    service: Annotated[RuleService, Depends(get_rule_service)],
    _user: Annotated[User, Depends(read_rules)],
) -> Rule:
    return await service.get_rule(rule_id)


@router.patch(
    "/{rule_id}",
    response_model=RuleResponse,
    dependencies=[Depends(require_trusted_origin)],
)
async def update_rule(
    rule_id: UUID,
    payload: RuleUpdate,
    service: Annotated[RuleService, Depends(get_rule_service)],
    user: Annotated[User, Depends(manage_rules)],
) -> Rule:
    return await service.update_rule(
        rule_id, payload.model_dump(mode="json", exclude_unset=True), user.id
    )


@router.delete(
    "/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_trusted_origin)],
)
async def delete_rule(
    rule_id: UUID,
    service: Annotated[RuleService, Depends(get_rule_service)],
    user: Annotated[User, Depends(manage_rules)],
) -> None:
    await service.delete_rule(rule_id, user.id)


@router.post(
    "/{rule_id}/evaluate",
    response_model=RuleEvaluationResponse,
    dependencies=[Depends(require_trusted_origin)],
)
async def evaluate_rule(
    rule_id: UUID,
    payload: RuleEvaluationRequest,
    service: Annotated[RuleService, Depends(get_rule_service)],
    _user: Annotated[User, Depends(manage_rules)],
) -> RuleEvaluation:
    return await service.evaluate(rule_id, payload)
