# ruff: noqa
# mypy: disable-error-code=no-untyped-def
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import or_
from app.api.dependencies.auth import get_collector_status_repository, get_inventory_service, require_permission, require_trusted_origin
from app.models.auth import User
from app.models.enums import PermissionCode
from app.models.inventory import CollectorAssignment, CollectorProfile, Device, Interface, Site
from app.schemas.inventory import *
from app.services.inventory import InventoryService
from app.repositories.collector import CollectorStatusRepository
from app.schemas.collector import CollectorStatusResponse

router = APIRouter()
read = require_permission(PermissionCode.INVENTORY_READ.value)
site_manage = require_permission(PermissionCode.SITES_MANAGE.value)
device_manage = require_permission(PermissionCode.DEVICES_MANAGE.value)
interface_manage = require_permission(PermissionCode.INTERFACES_MANAGE.value)
assignment_manage = require_permission(PermissionCode.COLLECTOR_ASSIGNMENTS_MANAGE.value)

@router.get("/collector-status", response_model=list[CollectorStatusResponse])
async def collector_status(repository: Annotated[CollectorStatusRepository, Depends(get_collector_status_repository)], _u: Annotated[User, Depends(read)], device_id: UUID | None = None):
    return await repository.list(device_id)

@router.get("/sites", response_model=list[SiteResponse])
async def sites(service: Annotated[InventoryService, Depends(get_inventory_service)], _u: Annotated[User, Depends(read)], search: str | None = None):
    return await service.list(Site, [or_(Site.name.ilike(f"%{search}%"), Site.code.ilike(f"%{search}%"))] if search else None)
@router.post("/sites", response_model=SiteResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_trusted_origin)])
async def create_site(payload: SiteCreate, service: Annotated[InventoryService, Depends(get_inventory_service)], _u: Annotated[User, Depends(site_manage)]): return await service.create(Site, payload.model_dump())
@router.get("/sites/{item_id}", response_model=SiteResponse)
async def get_site(item_id: UUID, service: Annotated[InventoryService, Depends(get_inventory_service)], _u: Annotated[User, Depends(read)]): return await service.get(Site, item_id)
@router.patch("/sites/{item_id}", response_model=SiteResponse, dependencies=[Depends(require_trusted_origin)])
async def update_site(item_id: UUID, payload: SiteUpdate, service: Annotated[InventoryService, Depends(get_inventory_service)], _u: Annotated[User, Depends(site_manage)]): return await service.update(Site, item_id, payload.model_dump(exclude_unset=True))
@router.delete("/sites/{item_id}", status_code=204, dependencies=[Depends(require_trusted_origin)])
async def delete_site(item_id: UUID, service: Annotated[InventoryService, Depends(get_inventory_service)], _u: Annotated[User, Depends(site_manage)]): await service.delete(Site, item_id)

@router.get("/devices", response_model=list[DeviceResponse])
async def devices(service: Annotated[InventoryService, Depends(get_inventory_service)], _u: Annotated[User, Depends(read)], search: str | None = None, site_id: UUID | None = None, device_type: str | None = None, status_filter: str | None = Query(None, alias="status"), monitoring_enabled: bool | None = None):
    filters = []
    if search: filters.append(or_(Device.name.ilike(f"%{search}%"), Device.hostname.ilike(f"%{search}%"), Device.management_ip.ilike(f"%{search}%")))
    if site_id: filters.append(Device.site_id == site_id)
    if device_type: filters.append(Device.device_type == device_type)
    if status_filter: filters.append(Device.status == status_filter)
    if monitoring_enabled is not None: filters.append(Device.monitoring_enabled == monitoring_enabled)
    return await service.list(Device, filters)
@router.post("/devices", response_model=DeviceResponse, status_code=201, dependencies=[Depends(require_trusted_origin)])
async def create_device(payload: DeviceCreate, service: Annotated[InventoryService, Depends(get_inventory_service)], _u: Annotated[User, Depends(device_manage)]): return await service.create(Device, payload.model_dump())
@router.get("/devices/{item_id}", response_model=DeviceResponse)
async def get_device(item_id: UUID, service: Annotated[InventoryService, Depends(get_inventory_service)], _u: Annotated[User, Depends(read)]): return await service.get(Device, item_id)
@router.patch("/devices/{item_id}", response_model=DeviceResponse, dependencies=[Depends(require_trusted_origin)])
async def update_device(item_id: UUID, payload: DeviceUpdate, service: Annotated[InventoryService, Depends(get_inventory_service)], _u: Annotated[User, Depends(device_manage)]): return await service.update(Device, item_id, payload.model_dump(exclude_unset=True))
@router.delete("/devices/{item_id}", status_code=204, dependencies=[Depends(require_trusted_origin)])
async def delete_device(item_id: UUID, service: Annotated[InventoryService, Depends(get_inventory_service)], _u: Annotated[User, Depends(device_manage)]): await service.delete(Device, item_id)

@router.get("/interfaces", response_model=list[InterfaceResponse])
async def interfaces(service: Annotated[InventoryService, Depends(get_inventory_service)], _u: Annotated[User, Depends(read)], device_id: UUID | None = None): return await service.list(Interface, [Interface.device_id == device_id] if device_id else None)
@router.post("/interfaces", response_model=InterfaceResponse, status_code=201, dependencies=[Depends(require_trusted_origin)])
async def create_interface(payload: InterfaceCreate, service: Annotated[InventoryService, Depends(get_inventory_service)], _u: Annotated[User, Depends(interface_manage)]): return await service.create(Interface, payload.model_dump())
@router.get("/interfaces/{item_id}", response_model=InterfaceResponse)
async def get_interface(item_id: UUID, service: Annotated[InventoryService, Depends(get_inventory_service)], _u: Annotated[User, Depends(read)]): return await service.get(Interface, item_id)
@router.patch("/interfaces/{item_id}", response_model=InterfaceResponse, dependencies=[Depends(require_trusted_origin)])
async def update_interface(item_id: UUID, payload: InterfaceUpdate, service: Annotated[InventoryService, Depends(get_inventory_service)], _u: Annotated[User, Depends(interface_manage)]): return await service.update(Interface, item_id, payload.model_dump(exclude_unset=True))
@router.delete("/interfaces/{item_id}", status_code=204, dependencies=[Depends(require_trusted_origin)])
async def delete_interface(item_id: UUID, service: Annotated[InventoryService, Depends(get_inventory_service)], _u: Annotated[User, Depends(interface_manage)]): await service.delete(Interface, item_id)

@router.get("/collector-profiles", response_model=list[CollectorProfileResponse])
async def profiles(service: Annotated[InventoryService, Depends(get_inventory_service)], _u: Annotated[User, Depends(read)]): return await service.list(CollectorProfile)
@router.post("/collector-profiles", response_model=CollectorProfileResponse, status_code=201, dependencies=[Depends(require_trusted_origin)])
async def create_profile(payload: CollectorProfileCreate, service: Annotated[InventoryService, Depends(get_inventory_service)], _u: Annotated[User, Depends(assignment_manage)]): return await service.create(CollectorProfile, payload.model_dump())
@router.patch("/collector-profiles/{item_id}", response_model=CollectorProfileResponse, dependencies=[Depends(require_trusted_origin)])
async def update_profile(item_id: UUID, payload: CollectorProfileUpdate, service: Annotated[InventoryService, Depends(get_inventory_service)], _u: Annotated[User, Depends(assignment_manage)]): return await service.update(CollectorProfile, item_id, payload.model_dump(exclude_unset=True))
@router.delete("/collector-profiles/{item_id}", status_code=204, dependencies=[Depends(require_trusted_origin)])
async def delete_profile(item_id: UUID, service: Annotated[InventoryService, Depends(get_inventory_service)], _u: Annotated[User, Depends(assignment_manage)]): await service.delete(CollectorProfile, item_id)
@router.get("/collector-assignments", response_model=list[CollectorAssignmentResponse])
async def assignments(service: Annotated[InventoryService, Depends(get_inventory_service)], _u: Annotated[User, Depends(read)], device_id: UUID | None = None): return await service.list(CollectorAssignment, [CollectorAssignment.device_id == device_id] if device_id else None)
@router.post("/collector-assignments", response_model=CollectorAssignmentResponse, status_code=201, dependencies=[Depends(require_trusted_origin)])
async def create_assignment(payload: CollectorAssignmentCreate, service: Annotated[InventoryService, Depends(get_inventory_service)], _u: Annotated[User, Depends(assignment_manage)]): return await service.create(CollectorAssignment, payload.model_dump())
@router.patch("/collector-assignments/{item_id}", response_model=CollectorAssignmentResponse, dependencies=[Depends(require_trusted_origin)])
async def update_assignment(item_id: UUID, payload: CollectorAssignmentUpdate, service: Annotated[InventoryService, Depends(get_inventory_service)], _u: Annotated[User, Depends(assignment_manage)]): return await service.update(CollectorAssignment, item_id, payload.model_dump(exclude_unset=True))
@router.delete("/collector-assignments/{item_id}", status_code=204, dependencies=[Depends(require_trusted_origin)])
async def delete_assignment(item_id: UUID, service: Annotated[InventoryService, Depends(get_inventory_service)], _u: Annotated[User, Depends(assignment_manage)]): await service.delete(CollectorAssignment, item_id)
