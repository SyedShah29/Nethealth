from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.dependencies.auth import (
    get_analytics_service,
    get_current_user,
    get_escalation_service,
    get_field_task_service,
    get_maintenance_service,
    get_report_service,
    get_search_service,
    require_permission,
    require_trusted_origin,
)
from app.models.auth import User
from app.models.enums import PermissionCode
from app.models.workflows import EscalationPolicy, FieldPhoto, FieldTask, MaintenanceWindow
from app.schemas.workflows import (
    AnalyticsResponse,
    EscalationPolicyCreate,
    EscalationPolicyResponse,
    FieldNoteCreate,
    FieldPhotoCreate,
    FieldPhotoResponse,
    FieldTaskAction,
    FieldTaskCreate,
    FieldTaskResponse,
    FieldTicketResponse,
    MaintenanceWindowCreate,
    MaintenanceWindowResponse,
    SearchResult,
)
from app.services.workflows import (
    AnalyticsService,
    EscalationService,
    FieldTaskService,
    MaintenanceService,
    ReportService,
    SearchService,
)

router = APIRouter()
jobs_read = require_permission(PermissionCode.JOBS_READ.value)
jobs_update = require_permission(PermissionCode.JOBS_UPDATE.value)
notes_create = require_permission(PermissionCode.FIELD_NOTES_CREATE.value)
photos_upload = require_permission(PermissionCode.FIELD_PHOTOS_UPLOAD.value)
incidents_manage = require_permission(PermissionCode.INCIDENTS_MANAGE.value)
dashboards_read = require_permission(PermissionCode.DASHBOARDS_READ.value)
notifications_manage = require_permission(PermissionCode.NOTIFICATIONS_MANAGE.value)
rules_manage = require_permission(PermissionCode.RULES_MANAGE.value)


@router.post(
    "/field-tasks",
    response_model=FieldTaskResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_trusted_origin)],
)
async def create_field_task(
    payload: FieldTaskCreate,
    service: Annotated[FieldTaskService, Depends(get_field_task_service)],
    user: Annotated[User, Depends(incidents_manage)],
) -> FieldTask:
    return await service.create(payload, user.id)


@router.get("/field-tasks", response_model=list[FieldTaskResponse])
async def list_field_tasks(
    service: Annotated[FieldTaskService, Depends(get_field_task_service)],
    user: Annotated[User, Depends(jobs_read)],
) -> list[FieldTask]:
    return await service.list_for(user.id, user.role.name)


@router.get("/field-tasks/{task_id}", response_model=FieldTicketResponse)
async def get_field_ticket(
    task_id: UUID,
    service: Annotated[FieldTaskService, Depends(get_field_task_service)],
    user: Annotated[User, Depends(jobs_read)],
) -> FieldTicketResponse:
    return await service.ticket(task_id, user.id, user.role.name)


@router.post(
    "/field-tasks/{task_id}/actions",
    response_model=FieldTaskResponse,
    dependencies=[Depends(require_trusted_origin)],
)
async def field_task_action(
    task_id: UUID,
    payload: FieldTaskAction,
    service: Annotated[FieldTaskService, Depends(get_field_task_service)],
    user: Annotated[User, Depends(jobs_update)],
) -> FieldTask:
    return await service.action(task_id, payload, user.id, user.role.name)


@router.post(
    "/field-tasks/{task_id}/notes",
    response_model=FieldTaskResponse,
    dependencies=[Depends(require_trusted_origin)],
)
async def add_field_note(
    task_id: UUID,
    payload: FieldNoteCreate,
    service: Annotated[FieldTaskService, Depends(get_field_task_service)],
    user: Annotated[User, Depends(notes_create)],
) -> FieldTask:
    return await service.add_note(task_id, payload.note, user.id, user.role.name)


@router.post(
    "/field-tasks/{task_id}/photos",
    response_model=FieldPhotoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_trusted_origin)],
)
async def upload_field_photo(
    task_id: UUID,
    payload: FieldPhotoCreate,
    service: Annotated[FieldTaskService, Depends(get_field_task_service)],
    user: Annotated[User, Depends(photos_upload)],
) -> FieldPhoto:
    return await service.upload_photo(task_id, payload, user.id, user.role.name)


@router.get("/field-photos/{photo_id}")
async def download_field_photo(
    photo_id: UUID,
    service: Annotated[FieldTaskService, Depends(get_field_task_service)],
    user: Annotated[User, Depends(jobs_read)],
) -> Response:
    photo = await service.photo_content(photo_id, user.id, user.role.name)
    return Response(
        content=photo.content,
        media_type=photo.content_type,
        headers={"Content-Disposition": f'attachment; filename="{photo.filename}"'},
    )


@router.get("/analytics/operations", response_model=AnalyticsResponse)
async def operational_analytics(
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    _user: Annotated[User, Depends(dashboards_read)],
) -> AnalyticsResponse:
    return await service.get()


@router.get("/reports/{report_name}.csv")
async def export_report(
    report_name: str,
    service: Annotated[ReportService, Depends(get_report_service)],
    _user: Annotated[User, Depends(dashboards_read)],
) -> Response:
    return Response(
        content=await service.csv(report_name),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{report_name}.csv"'},
    )


@router.get("/search", response_model=list[SearchResult])
async def global_search(
    service: Annotated[SearchService, Depends(get_search_service)],
    user: Annotated[User, Depends(get_current_user)],
    query: Annotated[str, Query(min_length=2, max_length=255)],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
) -> list[SearchResult]:
    permissions = {item.code for item in user.role.permissions}
    return await service.search(query, permissions, limit)


@router.post(
    "/escalation-policies",
    response_model=EscalationPolicyResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_trusted_origin)],
)
async def create_escalation_policy(
    payload: EscalationPolicyCreate,
    service: Annotated[EscalationService, Depends(get_escalation_service)],
    user: Annotated[User, Depends(notifications_manage)],
) -> EscalationPolicy:
    return await service.create_policy(payload, user.id)


@router.get("/escalation-policies", response_model=list[EscalationPolicyResponse])
async def list_escalation_policies(
    service: Annotated[EscalationService, Depends(get_escalation_service)],
    _user: Annotated[User, Depends(notifications_manage)],
) -> list[EscalationPolicy]:
    return await service.repository.list_policies()


@router.post(
    "/escalations/evaluate",
    dependencies=[Depends(require_trusted_origin)],
)
async def evaluate_escalations(
    service: Annotated[EscalationService, Depends(get_escalation_service)],
    _user: Annotated[User, Depends(notifications_manage)],
) -> dict[str, int]:
    return {"created": len(await service.evaluate())}


@router.post(
    "/maintenance-windows",
    response_model=MaintenanceWindowResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_trusted_origin)],
)
async def create_maintenance_window(
    payload: MaintenanceWindowCreate,
    service: Annotated[MaintenanceService, Depends(get_maintenance_service)],
    user: Annotated[User, Depends(rules_manage)],
) -> MaintenanceWindow:
    return await service.create(payload, user.id)


@router.get("/maintenance-windows", response_model=list[MaintenanceWindowResponse])
async def list_maintenance_windows(
    service: Annotated[MaintenanceService, Depends(get_maintenance_service)],
    _user: Annotated[User, Depends(rules_manage)],
) -> list[MaintenanceWindow]:
    return await service.list()


@router.delete(
    "/maintenance-windows/{window_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_trusted_origin)],
)
async def delete_maintenance_window(
    window_id: UUID,
    service: Annotated[MaintenanceService, Depends(get_maintenance_service)],
    user: Annotated[User, Depends(rules_manage)],
) -> Response:
    await service.delete(window_id, user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
