from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.db.session import get_db_session
from app.models.auth import User
from app.repositories.analysis import AnalysisRepository
from app.repositories.audit import AuditLogRepository
from app.repositories.auth import PermissionRepository, RoleRepository
from app.repositories.collector import CollectorStatusRepository
from app.repositories.fiber import FiberRepository, OpticalThresholdRepository
from app.repositories.inventory import InventoryRepository
from app.repositories.metrics import MetricRepository
from app.repositories.operations import OperationsRepository
from app.repositories.reporting import ReportingRepository
from app.repositories.rules import RuleRepository
from app.repositories.subscriber import SubscriberRepository
from app.repositories.topology import TopologyRepository
from app.repositories.workflows import WorkflowRepository
from app.security.passwords import PasswordHasher, get_password_hasher
from app.services.admin import AdminService
from app.services.analysis import CorrelationService, RootCauseService
from app.services.audit import AuditService
from app.services.auth import AuthService
from app.services.fiber import FiberService, OpticalThresholdService
from app.services.inventory import InventoryService
from app.services.metrics import MetricService
from app.services.operations import (
    AnomalyService,
    CapacityService,
    HealthScoreService,
    IncidentService,
    NotificationService,
)
from app.services.reporting import DashboardService, DiagnosticsService
from app.services.rules import RuleService
from app.services.subscriber import SubscriberService
from app.services.topology import TopologyService
from app.services.users import UserService
from app.services.workflows import (
    AnalyticsService,
    EscalationService,
    FieldTaskService,
    MaintenanceService,
    ReportService,
    SearchService,
)


def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    password_hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
) -> AuthService:
    return AuthService(session, settings, password_hasher)


def get_user_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    password_hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
) -> UserService:
    return UserService(session, password_hasher)


def get_admin_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AdminService:
    return AdminService(
        session,
        RoleRepository(session),
        PermissionRepository(session),
        AuditLogRepository(session),
    )


def get_inventory_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> InventoryService:
    return InventoryService(
        InventoryRepository(session),
        AuditService(AuditLogRepository(session)),
    )


def get_collector_status_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CollectorStatusRepository:
    return CollectorStatusRepository(session)


def get_metric_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MetricService:
    return MetricService(MetricRepository(session))


def get_subscriber_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SubscriberService:
    return SubscriberService(SubscriberRepository(session))


def get_fiber_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> FiberService:
    return FiberService(
        FiberRepository(session),
        OpticalThresholdRepository(session),
        MetricRepository(session),
    )


def get_optical_threshold_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> OpticalThresholdService:
    return OpticalThresholdService(
        OpticalThresholdRepository(session),
        AuditService(AuditLogRepository(session)),
    )


def get_topology_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TopologyService:
    return TopologyService(
        TopologyRepository(session),
        AuditService(AuditLogRepository(session)),
    )


def get_rule_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RuleService:
    operations = OperationsRepository(session)
    audit = AuditService(AuditLogRepository(session))
    return RuleService(
        RuleRepository(session),
        audit,
        IncidentService(
            operations,
            audit,
            NotificationService(operations, audit),
            WorkflowRepository(session),
        ),
    )


def get_correlation_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CorrelationService:
    operations = OperationsRepository(session)
    audit = AuditService(AuditLogRepository(session))
    return CorrelationService(
        AnalysisRepository(session),
        TopologyRepository(session),
        settings.correlation_window_seconds,
        IncidentService(
            operations,
            audit,
            NotificationService(operations, audit),
            WorkflowRepository(session),
        ),
    )


def get_root_cause_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RootCauseService:
    return RootCauseService(AnalysisRepository(session))


def get_health_score_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> HealthScoreService:
    return HealthScoreService(OperationsRepository(session), SubscriberRepository(session))


def get_anomaly_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AnomalyService:
    return AnomalyService(OperationsRepository(session))


def get_incident_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IncidentService:
    operations = OperationsRepository(session)
    audit = AuditService(AuditLogRepository(session))
    return IncidentService(
        operations,
        audit,
        NotificationService(operations, audit),
        WorkflowRepository(session),
    )


def get_notification_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> NotificationService:
    return NotificationService(
        OperationsRepository(session), AuditService(AuditLogRepository(session))
    )


def get_capacity_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CapacityService:
    return CapacityService(OperationsRepository(session), AuditService(AuditLogRepository(session)))


def get_diagnostics_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DiagnosticsService:
    return DiagnosticsService(
        SubscriberRepository(session),
        FiberRepository(session),
        OperationsRepository(session),
        ReportingRepository(session),
    )


def get_dashboard_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DashboardService:
    return DashboardService(ReportingRepository(session))


def get_field_task_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> FieldTaskService:
    return FieldTaskService(
        WorkflowRepository(session),
        OperationsRepository(session),
        AuditService(AuditLogRepository(session)),
    )


def get_analytics_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AnalyticsService:
    return AnalyticsService(WorkflowRepository(session))


def get_report_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ReportService:
    repository = WorkflowRepository(session)
    return ReportService(repository, AnalyticsService(repository), ReportingRepository(session))


def get_search_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SearchService:
    return SearchService(WorkflowRepository(session))


def get_escalation_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> EscalationService:
    return EscalationService(
        WorkflowRepository(session),
        OperationsRepository(session),
        AuditService(AuditLogRepository(session)),
    )


def get_maintenance_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MaintenanceService:
    return MaintenanceService(
        WorkflowRepository(session), AuditService(AuditLogRepository(session))
    )


def require_trusted_origin(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    origin = request.headers.get("origin")
    if origin is None:
        return
    backend_origin = f"{request.url.scheme}://{request.url.netloc}"
    trusted_origins = {item.rstrip("/") for item in settings.backend_cors_origins}
    trusted_origins.add(backend_origin)
    if origin.rstrip("/") not in trusted_origins:
        raise AppError(
            code="UNTRUSTED_ORIGIN",
            message="The request origin is not allowed.",
            status_code=403,
        )


async def get_current_user(
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    token = request.cookies.get(settings.auth_cookie_name)
    return await service.authenticate_session(token)


def require_permission(permission: str) -> Callable[..., Awaitable[User]]:
    async def dependency(
        user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        permissions = {item.code for item in user.role.permissions}
        if permission not in permissions:
            raise AppError(
                code="PERMISSION_DENIED",
                message="You do not have permission to perform this action.",
                status_code=403,
            )
        return user

    return dependency
