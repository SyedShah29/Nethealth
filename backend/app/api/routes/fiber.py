from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies.auth import (
    get_fiber_service,
    get_optical_threshold_service,
    require_permission,
    require_trusted_origin,
)
from app.models.auth import User
from app.models.enums import PermissionCode
from app.models.fiber import OLT, ONU, PON, OpticalThreshold
from app.schemas.fiber import (
    OLTResponse,
    ONUOpticalHistoryResponse,
    ONUOpticalStatusResponse,
    ONUResponse,
    OpticalHistoryWindow,
    OpticalThresholdCreate,
    OpticalThresholdResponse,
    OpticalThresholdUpdate,
    PONResponse,
)
from app.services.fiber import FiberService, OpticalThresholdService

router = APIRouter()
read_operational = require_permission(PermissionCode.OPERATIONAL_READ.value)
manage_thresholds = require_permission(PermissionCode.THRESHOLDS_MANAGE.value)


@router.get("/olts", response_model=list[OLTResponse])
async def list_olts(
    service: Annotated[FiberService, Depends(get_fiber_service)],
    _user: Annotated[User, Depends(read_operational)],
) -> list[OLT]:
    return await service.list_olts()


@router.get("/olts/{olt_id}", response_model=OLTResponse)
async def get_olt(
    olt_id: UUID,
    service: Annotated[FiberService, Depends(get_fiber_service)],
    _user: Annotated[User, Depends(read_operational)],
) -> OLT:
    return await service.get_olt(olt_id)


@router.get("/pons", response_model=list[PONResponse])
async def list_pons(
    service: Annotated[FiberService, Depends(get_fiber_service)],
    _user: Annotated[User, Depends(read_operational)],
    olt_id: UUID | None = None,
    status: Annotated[str | None, Query(max_length=32)] = None,
) -> list[PON]:
    return await service.list_pons(olt_id=olt_id, status=status)


@router.get("/pons/{pon_id}", response_model=PONResponse)
async def get_pon(
    pon_id: UUID,
    service: Annotated[FiberService, Depends(get_fiber_service)],
    _user: Annotated[User, Depends(read_operational)],
) -> PON:
    return await service.get_pon(pon_id)


@router.get("/onus", response_model=list[ONUResponse])
async def list_onus(
    service: Annotated[FiberService, Depends(get_fiber_service)],
    _user: Annotated[User, Depends(read_operational)],
    olt_id: UUID | None = None,
    pon_id: UUID | None = None,
    subscriber_id: Annotated[str | None, Query(max_length=120)] = None,
    status: Annotated[str | None, Query(max_length=32)] = None,
    search: Annotated[str | None, Query(max_length=255)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ONU]:
    return await service.list_onus(
        olt_id=olt_id,
        pon_id=pon_id,
        subscriber_id=subscriber_id,
        status=status,
        search=search,
        offset=offset,
        limit=limit,
    )


@router.get("/onus/{onu_id}", response_model=ONUResponse)
async def get_onu(
    onu_id: UUID,
    service: Annotated[FiberService, Depends(get_fiber_service)],
    _user: Annotated[User, Depends(read_operational)],
) -> ONU:
    return await service.get_onu(onu_id)


@router.get("/onus/{onu_id}/optical-status", response_model=ONUOpticalStatusResponse)
async def get_onu_optical_status(
    onu_id: UUID,
    service: Annotated[FiberService, Depends(get_fiber_service)],
    _user: Annotated[User, Depends(read_operational)],
) -> ONUOpticalStatusResponse:
    return await service.optical_status(onu_id)


@router.get(
    "/onus/{onu_id}/optical-history",
    response_model=ONUOpticalHistoryResponse,
)
async def get_onu_optical_history(
    onu_id: UUID,
    service: Annotated[FiberService, Depends(get_fiber_service)],
    _user: Annotated[User, Depends(read_operational)],
    window: OpticalHistoryWindow = OpticalHistoryWindow.CURRENT,
) -> ONUOpticalHistoryResponse:
    return await service.optical_history(onu_id, window)


@router.get("/optical-thresholds", response_model=list[OpticalThresholdResponse])
async def list_optical_thresholds(
    service: Annotated[OpticalThresholdService, Depends(get_optical_threshold_service)],
    _user: Annotated[User, Depends(read_operational)],
) -> list[OpticalThreshold]:
    return await service.list()


@router.post(
    "/optical-thresholds",
    response_model=OpticalThresholdResponse,
    status_code=201,
    dependencies=[Depends(require_trusted_origin)],
)
async def create_optical_threshold(
    payload: OpticalThresholdCreate,
    service: Annotated[OpticalThresholdService, Depends(get_optical_threshold_service)],
    user: Annotated[User, Depends(manage_thresholds)],
) -> OpticalThreshold:
    return await service.create(payload, user.id)


@router.patch(
    "/optical-thresholds/{threshold_id}",
    response_model=OpticalThresholdResponse,
    dependencies=[Depends(require_trusted_origin)],
)
async def update_optical_threshold(
    threshold_id: UUID,
    payload: OpticalThresholdUpdate,
    service: Annotated[OpticalThresholdService, Depends(get_optical_threshold_service)],
    user: Annotated[User, Depends(manage_thresholds)],
) -> OpticalThreshold:
    return await service.update(threshold_id, payload, user.id)


@router.delete(
    "/optical-thresholds/{threshold_id}",
    status_code=204,
    dependencies=[Depends(require_trusted_origin)],
)
async def delete_optical_threshold(
    threshold_id: UUID,
    service: Annotated[OpticalThresholdService, Depends(get_optical_threshold_service)],
    user: Annotated[User, Depends(manage_thresholds)],
) -> None:
    await service.delete(threshold_id, user.id)
