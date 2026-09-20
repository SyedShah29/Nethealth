from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies.auth import get_metric_service, require_permission
from app.core.errors import AppError
from app.models.auth import User
from app.models.enums import PermissionCode
from app.schemas.metrics import (
    MetricAggregateResponse,
    MetricEntityType,
    MetricQuery,
    MetricResolution,
    MetricSampleResponse,
)
from app.services.metrics import MetricService

router = APIRouter(prefix="/metrics")


@router.get("", response_model=list[MetricSampleResponse | MetricAggregateResponse])
async def query_metrics(
    service: Annotated[MetricService, Depends(get_metric_service)],
    _user: Annotated[
        User, Depends(require_permission(PermissionCode.METRICS_READ.value))
    ],
    start: datetime,
    end: datetime,
    entity_type: MetricEntityType | None = None,
    entity_id: Annotated[str | None, Query(max_length=255)] = None,
    metric_name: Annotated[str | None, Query(max_length=80)] = None,
    source: Annotated[str | None, Query(max_length=64)] = None,
    resolution: MetricResolution = MetricResolution.RAW,
    limit: Annotated[int, Query(ge=1, le=10_000)] = 1000,
) -> list[object]:
    if end <= start:
        raise AppError(
            "INVALID_TIME_RANGE",
            "The metric query end time must be later than its start time.",
            422,
        )
    query = MetricQuery(
        start=start,
        end=end,
        entity_type=entity_type,
        entity_id=entity_id,
        metric_name=metric_name,
        source=source,
        resolution=resolution,
        limit=limit,
    )
    return await service.query(query)
