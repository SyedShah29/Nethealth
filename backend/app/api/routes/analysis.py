from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies.auth import (
    get_correlation_service,
    get_root_cause_service,
    require_permission,
    require_trusted_origin,
)
from app.models.analysis import OutageCorrelation, RootCauseAssessment
from app.models.auth import User
from app.models.enums import PermissionCode
from app.schemas.analysis import (
    CorrelationRequest,
    CorrelationResponse,
    RootCauseRequest,
    RootCauseResponse,
)
from app.services.analysis import CorrelationService, RootCauseService

router = APIRouter()
read_incidents = require_permission(PermissionCode.INCIDENTS_READ.value)
manage_incidents = require_permission(PermissionCode.INCIDENTS_MANAGE.value)
read_diagnostics = require_permission(PermissionCode.DIAGNOSTICS_READ.value)


@router.get("/correlations", response_model=list[CorrelationResponse])
async def list_correlations(
    service: Annotated[CorrelationService, Depends(get_correlation_service)],
    _user: Annotated[User, Depends(read_incidents)],
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[OutageCorrelation]:
    return await service.list_correlations(limit)


@router.post(
    "/correlations/evaluate",
    response_model=CorrelationResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_trusted_origin)],
)
async def correlate_outage(
    payload: CorrelationRequest,
    service: Annotated[CorrelationService, Depends(get_correlation_service)],
    _user: Annotated[User, Depends(manage_incidents)],
) -> OutageCorrelation:
    return await service.correlate(payload)


@router.get("/root-causes", response_model=list[RootCauseResponse])
async def list_root_causes(
    service: Annotated[RootCauseService, Depends(get_root_cause_service)],
    _user: Annotated[User, Depends(read_diagnostics)],
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[RootCauseAssessment]:
    return await service.list(limit)


@router.post(
    "/root-causes/classify",
    response_model=RootCauseResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_trusted_origin)],
)
async def classify_root_cause(
    payload: RootCauseRequest,
    service: Annotated[RootCauseService, Depends(get_root_cause_service)],
    _user: Annotated[User, Depends(read_diagnostics)],
) -> RootCauseAssessment:
    return await service.classify(payload)


@router.get("/root-causes/{assessment_id}", response_model=RootCauseResponse)
async def get_root_cause(
    assessment_id: UUID,
    service: Annotated[RootCauseService, Depends(get_root_cause_service)],
    _user: Annotated[User, Depends(read_diagnostics)],
) -> RootCauseAssessment:
    return await service.get(assessment_id)
