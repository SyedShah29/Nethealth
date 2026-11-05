from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies.auth import (
    get_anomaly_service,
    get_capacity_service,
    get_dashboard_service,
    get_diagnostics_service,
    get_health_score_service,
    get_incident_service,
    get_notification_service,
    require_permission,
    require_trusted_origin,
)
from app.models.auth import User
from app.models.enums import PermissionCode
from app.models.operations import (
    CapacityAssessment,
    CapacityThreshold,
    CapacityTrend,
    Incident,
    IncidentEvent,
    NotificationChannel,
    NotificationRule,
    OperationalAnomaly,
    SubscriberHealthScore,
)
from app.schemas.operations import (
    AnomalyEvaluationRequest,
    AnomalyResponse,
    CapacityAssessmentResponse,
    CapacityEvaluationRequest,
    CapacityThresholdCreate,
    CapacityThresholdResponse,
    CapacityTrendRequest,
    CapacityTrendResponse,
    DashboardResponse,
    HealthScoreRequest,
    HealthScoreResponse,
    IncidentCreate,
    IncidentEventResponse,
    IncidentResponse,
    IncidentStatus,
    IncidentUpdate,
    NotificationChannelCreate,
    NotificationChannelResponse,
    NotificationRuleCreate,
    NotificationRuleResponse,
    SubscriberDiagnosticsResponse,
)
from app.services.operations import (
    AnomalyService,
    CapacityService,
    HealthScoreService,
    IncidentService,
    NotificationService,
)
from app.services.reporting import DashboardService, DiagnosticsService

router = APIRouter()
diagnostics_read = require_permission(PermissionCode.DIAGNOSTICS_READ.value)
rules_manage = require_permission(PermissionCode.RULES_MANAGE.value)
incidents_read = require_permission(PermissionCode.INCIDENTS_READ.value)
incidents_manage = require_permission(PermissionCode.INCIDENTS_MANAGE.value)
notifications_manage = require_permission(PermissionCode.NOTIFICATIONS_MANAGE.value)
operational_read = require_permission(PermissionCode.OPERATIONAL_READ.value)
dashboards_read = require_permission(PermissionCode.DASHBOARDS_READ.value)


@router.post(
    "/subscriber-health/{subscriber_id}/evaluate",
    response_model=HealthScoreResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_trusted_origin)],
)
async def evaluate_subscriber_health(
    subscriber_id: str,
    payload: HealthScoreRequest,
    service: Annotated[HealthScoreService, Depends(get_health_score_service)],
    _user: Annotated[User, Depends(rules_manage)],
) -> SubscriberHealthScore:
    return await service.evaluate(subscriber_id, payload)


@router.get("/subscriber-health/{subscriber_id}", response_model=HealthScoreResponse)
async def get_subscriber_health(
    subscriber_id: str,
    service: Annotated[HealthScoreService, Depends(get_health_score_service)],
    _user: Annotated[User, Depends(diagnostics_read)],
) -> SubscriberHealthScore:
    return await service.latest(subscriber_id)


@router.get(
    "/subscribers/{subscriber_id}/diagnostics",
    response_model=SubscriberDiagnosticsResponse,
)
async def subscriber_diagnostics(
    subscriber_id: str,
    service: Annotated[DiagnosticsService, Depends(get_diagnostics_service)],
    _user: Annotated[User, Depends(diagnostics_read)],
) -> SubscriberDiagnosticsResponse:
    return await service.subscriber_360(subscriber_id)


@router.post(
    "/anomalies/evaluate",
    response_model=AnomalyResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_trusted_origin)],
)
async def evaluate_anomaly(
    payload: AnomalyEvaluationRequest,
    service: Annotated[AnomalyService, Depends(get_anomaly_service)],
    _user: Annotated[User, Depends(rules_manage)],
) -> OperationalAnomaly:
    return await service.evaluate(payload)


@router.get("/anomalies", response_model=list[AnomalyResponse])
async def list_anomalies(
    service: Annotated[AnomalyService, Depends(get_anomaly_service)],
    _user: Annotated[User, Depends(operational_read)],
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[OperationalAnomaly]:
    return await service.list(limit)


@router.post(
    "/incidents",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_trusted_origin)],
)
async def create_incident(
    payload: IncidentCreate,
    service: Annotated[IncidentService, Depends(get_incident_service)],
    user: Annotated[User, Depends(incidents_manage)],
) -> Incident:
    return await service.create_or_attach(payload, user.id)


@router.get("/incidents", response_model=list[IncidentResponse])
async def list_incidents(
    service: Annotated[IncidentService, Depends(get_incident_service)],
    _user: Annotated[User, Depends(incidents_read)],
    incident_status: Annotated[IncidentStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[Incident]:
    return await service.list_incidents(incident_status.value if incident_status else None, limit)


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: UUID,
    service: Annotated[IncidentService, Depends(get_incident_service)],
    _user: Annotated[User, Depends(incidents_read)],
) -> Incident:
    return await service.get(incident_id)


@router.patch(
    "/incidents/{incident_id}",
    response_model=IncidentResponse,
    dependencies=[Depends(require_trusted_origin)],
)
async def update_incident(
    incident_id: UUID,
    payload: IncidentUpdate,
    service: Annotated[IncidentService, Depends(get_incident_service)],
    user: Annotated[User, Depends(incidents_manage)],
) -> Incident:
    return await service.update(incident_id, payload, user.id)


@router.get("/incidents/{incident_id}/timeline", response_model=list[IncidentEventResponse])
async def incident_timeline(
    incident_id: UUID,
    service: Annotated[IncidentService, Depends(get_incident_service)],
    _user: Annotated[User, Depends(incidents_read)],
) -> list[IncidentEvent]:
    return await service.timeline(incident_id)


@router.post(
    "/notification-channels",
    response_model=NotificationChannelResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_trusted_origin)],
)
async def create_notification_channel(
    payload: NotificationChannelCreate,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    user: Annotated[User, Depends(notifications_manage)],
) -> NotificationChannel:
    return await service.create_channel(payload, user.id)


@router.get("/notification-channels", response_model=list[NotificationChannelResponse])
async def list_notification_channels(
    service: Annotated[NotificationService, Depends(get_notification_service)],
    _user: Annotated[User, Depends(notifications_manage)],
) -> list[NotificationChannel]:
    return await service.list_channels()


@router.post(
    "/notification-rules",
    response_model=NotificationRuleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_trusted_origin)],
)
async def create_notification_rule(
    payload: NotificationRuleCreate,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    user: Annotated[User, Depends(notifications_manage)],
) -> NotificationRule:
    return await service.create_rule(payload, user.id)


@router.get("/notification-rules", response_model=list[NotificationRuleResponse])
async def list_notification_rules(
    service: Annotated[NotificationService, Depends(get_notification_service)],
    _user: Annotated[User, Depends(notifications_manage)],
) -> list[NotificationRule]:
    return await service.list_rules()


@router.post(
    "/incidents/{incident_id}/notifications/dispatch",
    dependencies=[Depends(require_trusted_origin)],
)
async def dispatch_incident_notifications(
    incident_id: UUID,
    incident_service: Annotated[IncidentService, Depends(get_incident_service)],
    notification_service: Annotated[NotificationService, Depends(get_notification_service)],
    _user: Annotated[User, Depends(incidents_manage)],
) -> dict[str, Any]:
    deliveries = await notification_service.dispatch(await incident_service.get(incident_id))
    return {"created": len(deliveries), "delivery_ids": [str(item.id) for item in deliveries]}


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard(
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
    _user: Annotated[User, Depends(dashboards_read)],
) -> DashboardResponse:
    return await service.get()


@router.post(
    "/capacity/thresholds",
    response_model=CapacityThresholdResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_trusted_origin)],
)
async def create_capacity_threshold(
    payload: CapacityThresholdCreate,
    service: Annotated[CapacityService, Depends(get_capacity_service)],
    user: Annotated[User, Depends(rules_manage)],
) -> CapacityThreshold:
    return await service.create_threshold(payload.model_dump(), user.id)


@router.get("/capacity/thresholds", response_model=list[CapacityThresholdResponse])
async def list_capacity_thresholds(
    service: Annotated[CapacityService, Depends(get_capacity_service)],
    _user: Annotated[User, Depends(operational_read)],
) -> list[CapacityThreshold]:
    return await service.list_thresholds()


@router.post(
    "/capacity/evaluate",
    response_model=CapacityAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_trusted_origin)],
)
async def evaluate_capacity(
    payload: CapacityEvaluationRequest,
    service: Annotated[CapacityService, Depends(get_capacity_service)],
    _user: Annotated[User, Depends(rules_manage)],
) -> CapacityAssessment:
    return await service.evaluate(payload)


@router.get("/capacity/assessments", response_model=list[CapacityAssessmentResponse])
async def list_capacity_assessments(
    service: Annotated[CapacityService, Depends(get_capacity_service)],
    _user: Annotated[User, Depends(operational_read)],
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[CapacityAssessment]:
    return await service.list_assessments(limit)


@router.post(
    "/capacity/trends",
    response_model=CapacityTrendResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_trusted_origin)],
)
async def create_capacity_trend(
    payload: CapacityTrendRequest,
    service: Annotated[CapacityService, Depends(get_capacity_service)],
    _user: Annotated[User, Depends(rules_manage)],
) -> CapacityTrend:
    return await service.trend(payload)


@router.get("/capacity/trends", response_model=list[CapacityTrendResponse])
async def list_capacity_trends(
    service: Annotated[CapacityService, Depends(get_capacity_service)],
    _user: Annotated[User, Depends(operational_read)],
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[CapacityTrend]:
    return await service.list_trends(limit)
