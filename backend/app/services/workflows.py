from __future__ import annotations

from base64 import b64decode
from binascii import Error as Base64Error
from collections import Counter, defaultdict
from csv import DictWriter
from datetime import UTC, datetime
from hashlib import sha256
from io import StringIO
from statistics import fmean
from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.errors import AppError
from app.models.enums import AuditEventType, RoleName
from app.models.operations import Incident, IncidentEvent, NotificationDelivery
from app.models.workflows import (
    EscalationEvent,
    EscalationPolicy,
    FieldPhoto,
    FieldTask,
    MaintenanceWindow,
)
from app.repositories.operations import OperationsRepository
from app.repositories.reporting import ReportingRepository
from app.repositories.workflows import WorkflowRepository
from app.schemas.workflows import (
    AnalyticsResponse,
    EscalationPolicyCreate,
    FieldPhotoCreate,
    FieldTaskAction,
    FieldTaskCreate,
    FieldTaskResponse,
    FieldTicketResponse,
    MaintenanceWindowCreate,
    SearchResult,
)
from app.services.audit import AuditService
from app.services.operations import DashboardNotificationAdapter, QueuedNotificationAdapter

FIELD_TRANSITIONS = {
    "ACCEPT": ("ASSIGNED", "ACCEPTED", "accepted_at"),
    "START_WORK": ("ACCEPTED", "IN_PROGRESS", "started_at"),
    "MARK_RESTORED": ("IN_PROGRESS", "RESTORED", "restored_at"),
    "CLOSE": ("RESTORED", "CLOSED", "closed_at"),
}
SEVERITY_RANK = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


class FieldTaskService:
    def __init__(
        self,
        repository: WorkflowRepository,
        operations: OperationsRepository,
        audit: AuditService,
    ) -> None:
        self.repository = repository
        self.operations = operations
        self.audit = audit

    async def create(self, payload: FieldTaskCreate, actor_id: UUID) -> FieldTask:
        incident = await self.operations.get_incident(payload.incident_id)
        if incident is None:
            raise AppError("INCIDENT_NOT_FOUND", "Incident not found.", 404)
        try:
            task = await self.repository.add_task(
                FieldTask(**payload.model_dump(), status="ASSIGNED", notes=[])
            )
            await self._audit(task, "created", actor_id)
            await self.repository.commit()
            return task
        except IntegrityError as exc:
            await self.repository.session.rollback()
            raise AppError(
                "FIELD_TASK_CONFLICT", "Incident already has a field task.", 409
            ) from exc

    async def list_for(self, user_id: UUID, role: str) -> list[FieldTask]:
        technician_id = user_id if role == RoleName.FIELD_TECHNICIAN.value else None
        return await self.repository.list_tasks(technician_id)

    async def ticket(self, task_id: UUID, user_id: UUID, role: str) -> FieldTicketResponse:
        task = await self._get_authorized(task_id, user_id, role)
        incident = await self.operations.get_incident(task.incident_id)
        if incident is None:
            raise AppError("INCIDENT_NOT_FOUND", "Incident not found.", 404)
        return FieldTicketResponse(
            task=FieldTaskResponse.model_validate(task),
            incident={
                "id": str(incident.id),
                "title": incident.title,
                "severity": incident.severity,
                "status": incident.status,
                "category": incident.category,
            },
            photos=await self.repository.list_photos(task.id),
        )

    async def action(
        self, task_id: UUID, payload: FieldTaskAction, user_id: UUID, role: str
    ) -> FieldTask:
        task = await self._get_authorized(task_id, user_id, role)
        expected, target, timestamp_field = FIELD_TRANSITIONS[payload.action]
        if task.status != expected:
            raise AppError(
                "INVALID_FIELD_TASK_TRANSITION", "Field task transition is invalid.", 422
            )
        task.status = target
        task.current_status = target
        setattr(task, timestamp_field, datetime.now(UTC))
        await self._audit(task, payload.action.lower(), user_id)
        await self.repository.commit()
        return task

    async def add_note(self, task_id: UUID, note: str, user_id: UUID, role: str) -> FieldTask:
        task = await self._get_authorized(task_id, user_id, role)
        task.notes = [
            *task.notes,
            {"author_id": str(user_id), "note": note, "created_at": datetime.now(UTC).isoformat()},
        ]
        await self._audit(task, "note_added", user_id)
        await self.repository.commit()
        return task

    async def upload_photo(
        self, task_id: UUID, payload: FieldPhotoCreate, user_id: UUID, role: str
    ) -> FieldPhoto:
        await self._get_authorized(task_id, user_id, role)
        try:
            content = b64decode(payload.content_base64, validate=True)
        except (Base64Error, ValueError) as exc:
            raise AppError("INVALID_PHOTO", "Photo content is not valid base64.", 422) from exc
        if not content or len(content) > 5 * 1024 * 1024:
            raise AppError("INVALID_PHOTO_SIZE", "Photo must be no larger than 5 MiB.", 422)
        photo = await self.repository.add_photo(
            FieldPhoto(
                task_id=task_id,
                uploaded_by=user_id,
                filename=payload.filename,
                content_type=payload.content_type,
                byte_size=len(content),
                sha256=sha256(content).hexdigest(),
                content=content,
            )
        )
        await self.repository.commit()
        return photo

    async def photo_content(self, photo_id: UUID, user_id: UUID, role: str) -> FieldPhoto:
        photo = await self.repository.get_photo(photo_id)
        if photo is None:
            raise AppError("FIELD_PHOTO_NOT_FOUND", "Field photo not found.", 404)
        await self._get_authorized(photo.task_id, user_id, role)
        return photo

    async def _get_authorized(self, task_id: UUID, user_id: UUID, role: str) -> FieldTask:
        task = await self.repository.get_task(task_id)
        if task is None:
            raise AppError("FIELD_TASK_NOT_FOUND", "Field task not found.", 404)
        if role == RoleName.FIELD_TECHNICIAN.value and task.assigned_technician_id != user_id:
            raise AppError("FIELD_TASK_NOT_FOUND", "Field task not found.", 404)
        return task

    async def _audit(self, task: FieldTask, action: str, user_id: UUID) -> None:
        await self.audit.record(
            AuditEventType.INCIDENT_ACTION,
            success=True,
            actor_user_id=user_id,
            event_metadata={"field_task_id": str(task.id), "action": action},
        )


class AnalyticsService:
    def __init__(self, repository: WorkflowRepository) -> None:
        self.repository = repository

    async def get(self) -> AnalyticsResponse:
        incidents = await self.repository.incidents()
        events = await self.repository.incident_events()
        anomalies = await self.repository.anomalies()
        capacity = await self.repository.capacity()
        availability = await self.repository.availability_metrics()
        by_month: Counter[str] = Counter()
        by_site: Counter[str] = Counter()
        by_olt: Counter[str] = Counter()
        by_pon: Counter[str] = Counter()
        repeat: Counter[tuple[str, str, str]] = Counter()
        detect: list[float] = []
        acknowledge: list[float] = []
        repair: list[float] = []
        events_by_incident: defaultdict[UUID, list[IncidentEvent]] = defaultdict(list)
        for event in events:
            events_by_incident[event.incident_id].append(event)
        for incident in incidents:
            by_month[incident.first_seen.strftime("%Y-%m")] += 1
            repeat[
                (incident.category, incident.primary_entity_type, incident.primary_entity_id)
            ] += 1
            detect.append(max(0.0, (incident.created_at - incident.first_seen).total_seconds()))
            if incident.resolved_at:
                repair.append((incident.resolved_at - incident.first_seen).total_seconds())
            ack = next(
                (
                    item
                    for item in sorted(
                        events_by_incident[incident.id], key=lambda value: value.occurred_at
                    )
                    if item.details.get("status", {}).get("to") == "ACKNOWLEDGED"
                ),
                None,
            )
            if ack:
                acknowledge.append((ack.occurred_at - incident.first_seen).total_seconds())
            for entity in [
                {
                    "entity_type": incident.primary_entity_type,
                    "entity_id": incident.primary_entity_id,
                },
                *incident.affected_topology,
            ]:
                entity_type = str(entity.get("entity_type", "")).upper()
                entity_id = str(entity.get("entity_id", ""))
                if entity_type == "SITE":
                    by_site[entity_id] += 1
                elif entity_type == "OLT":
                    by_olt[entity_id] += 1
                elif entity_type == "PON":
                    by_pon[entity_id] += 1
        device_values: defaultdict[str, list[float]] = defaultdict(list)
        for metric in availability:
            device_values[metric.entity_id].append(float(metric.value))
        return AnalyticsResponse(
            outages_by_month=self._counter(by_month, "month"),
            outages_by_site=self._counter(by_site, "site"),
            outages_by_olt=self._counter(by_olt, "olt"),
            outages_by_pon=self._counter(by_pon, "pon"),
            mean_time_to_detect_seconds=fmean(detect) if detect else None,
            mean_time_to_acknowledge_seconds=fmean(acknowledge) if acknowledge else None,
            mean_time_to_repair_seconds=fmean(repair) if repair else None,
            repeat_incidents=[
                {"category": key[0], "entity_type": key[1], "entity_id": key[2], "count": count}
                for key, count in repeat.items()
                if count > 1
            ],
            unstable_subscribers=self._anomalies(
                anomalies, {"disconnect_frequency", "disconnect_events"}
            ),
            optical_degradation=[
                {
                    "entity_id": item.entity_id,
                    "detected_at": item.detected_at,
                    "severity": item.severity,
                }
                for item in anomalies
                if item.anomaly_type == "OPTICAL_DEGRADATION_WARNING"
            ],
            congestion=[
                {
                    "entity_id": item.entity_id,
                    "category": item.category,
                    "value": item.sustained_percent,
                }
                for item in capacity
                if item.category != "NORMAL"
            ],
            device_availability=[
                {"device_id": entity_id, "availability_percent": round(fmean(values) * 100, 3)}
                for entity_id, values in device_values.items()
            ],
        )

    @staticmethod
    def _counter(counter: Counter[str], name: str) -> list[dict[str, Any]]:
        return [{name: key, "count": count} for key, count in sorted(counter.items())]

    @staticmethod
    def _anomalies(items: list[Any], metrics: set[str]) -> list[dict[str, Any]]:
        counts = Counter(item.entity_id for item in items if item.metric_name in metrics)
        return [{"subscriber_id": key, "count": count} for key, count in counts.most_common()]


class ReportService:
    REPORTS = {
        "daily-network-summary",
        "weekly-reliability",
        "monthly-incidents",
        "capacity",
        "olt-health",
        "subscriber-stability",
    }

    def __init__(
        self,
        repository: WorkflowRepository,
        analytics: AnalyticsService,
        reporting: ReportingRepository,
    ) -> None:
        self.repository = repository
        self.analytics = analytics
        self.reporting = reporting

    async def csv(self, report_name: str) -> str:
        if report_name not in self.REPORTS:
            raise AppError("REPORT_NOT_FOUND", "Report type not found.", 404)
        data = await self.analytics.get()
        rows: list[dict[str, Any]]
        if report_name == "daily-network-summary":
            summary = await self.reporting.dashboard_summary()
            rows = [
                {"group": group, "status": status, "count": count}
                for group, values in summary.items()
                for status, count in values.items()
            ]
        elif report_name == "weekly-reliability":
            rows = data.device_availability or [{"device_id": "", "availability_percent": ""}]
        elif report_name == "monthly-incidents":
            rows = data.outages_by_month or [{"month": "", "count": 0}]
        elif report_name == "capacity":
            rows = data.congestion or [{"entity_id": "", "category": "NORMAL", "value": 0}]
        elif report_name == "olt-health":
            rows = [
                {"olt_id": str(olt.id), "device": device.name, "status": device.status}
                for olt, device in await self.repository.olt_health()
            ] or [{"olt_id": "", "device": "", "status": ""}]
        else:
            rows = data.unstable_subscribers or [{"subscriber_id": "", "count": 0}]
        output = StringIO()
        writer = DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()


class SearchService:
    def __init__(self, repository: WorkflowRepository) -> None:
        self.repository = repository

    async def search(self, query: str, permissions: set[str], limit: int) -> list[SearchResult]:
        results: list[SearchResult] = []
        if "subscribers:read" in permissions:
            results.extend(
                SearchResult(
                    result_type="SUBSCRIBER",
                    id=item.subscriber_id,
                    label=item.subscriber_id,
                    detail=item.current_ip or item.mac_address,
                )
                for item in await self.repository.search_subscribers(query, limit)
            )
        if "operational:read" in permissions:
            results.extend(
                SearchResult(result_type=kind, id=item_id, label=label)
                for kind, item_id, label in await self.repository.search_fiber(query, limit)
            )
        if "inventory:read" in permissions:
            results.extend(
                SearchResult(result_type=kind, id=item_id, label=label)
                for kind, item_id, label in await self.repository.search_inventory(query, limit)
            )
        if "incidents:read" in permissions or "incidents:manage" in permissions:
            results.extend(
                SearchResult(
                    result_type="INCIDENT", id=str(item.id), label=item.title, detail=item.status
                )
                for item in await self.repository.search_incidents(query, limit)
            )
        return results[:limit]


class EscalationService:
    def __init__(
        self,
        repository: WorkflowRepository,
        operations: OperationsRepository,
        audit: AuditService | None = None,
    ) -> None:
        self.repository = repository
        self.operations = operations
        self.audit = audit

    async def create_policy(
        self, payload: EscalationPolicyCreate, actor_id: UUID | None = None
    ) -> EscalationPolicy:
        for step in payload.steps:
            for channel_id in step.channel_ids:
                if await self.operations.get_channel(channel_id) is None:
                    raise AppError(
                        "NOTIFICATION_CHANNEL_NOT_FOUND", "Notification channel not found.", 404
                    )
        try:
            policy = await self.repository.add_policy(
                EscalationPolicy(
                    **payload.model_dump(exclude={"steps"}),
                    steps=[
                        {
                            **step.model_dump(exclude={"channel_ids"}),
                            "channel_ids": [str(item) for item in step.channel_ids],
                        }
                        for step in payload.steps
                    ],
                )
            )
            if self.audit is not None:
                await self.audit.record(
                    AuditEventType.CONFIGURATION_CHANGED,
                    success=True,
                    actor_user_id=actor_id,
                    event_metadata={
                        "resource_type": "EscalationPolicy",
                        "resource_id": str(policy.id),
                        "action": "created",
                    },
                )
            await self.repository.commit()
            return policy
        except IntegrityError as exc:
            await self.repository.session.rollback()
            raise AppError(
                "ESCALATION_POLICY_CONFLICT", "Escalation policy name exists.", 409
            ) from exc

    async def evaluate(self, now: datetime | None = None) -> list[EscalationEvent]:
        evaluated_at = now or datetime.now(UTC)
        incidents = await self.repository.incidents()
        policies = await self.repository.list_policies()
        created: list[EscalationEvent] = []
        for incident in incidents:
            if incident.status != "OPEN":
                continue
            age_minutes = (evaluated_at - incident.first_seen).total_seconds() / 60
            for policy in policies:
                if (
                    not policy.enabled
                    or SEVERITY_RANK[incident.severity] < SEVERITY_RANK[policy.minimum_severity]
                    or (policy.incident_category and policy.incident_category != incident.category)
                ):
                    continue
                for index, step in enumerate(policy.steps):
                    if age_minutes < int(step["delay_minutes"]):
                        continue
                    if await self.repository.escalation_exists(incident.id, policy.id, index):
                        continue
                    event = await self.repository.add_escalation(
                        EscalationEvent(
                            incident_id=incident.id,
                            policy_id=policy.id,
                            step_index=index,
                            team=str(step["team"]),
                            channel_ids=list(step["channel_ids"]),
                        )
                    )
                    await self._deliver(incident, event)
                    created.append(event)
        await self.repository.commit()
        return created

    async def _deliver(self, incident: Incident, event: EscalationEvent) -> None:
        for raw_channel_id in event.channel_ids:
            channel = await self.operations.get_channel(UUID(raw_channel_id))
            if channel is None or not channel.enabled:
                continue
            fingerprint = sha256(
                f"escalation:{incident.id}:{event.policy_id}:{event.step_index}:{channel.id}".encode()
            ).hexdigest()
            if await self.operations.delivery_exists(fingerprint):
                continue
            payload = {
                "incident_id": str(incident.id),
                "title": incident.title,
                "severity": incident.severity,
                "escalated_to": event.team,
                "step": event.step_index,
            }
            adapter = (
                DashboardNotificationAdapter()
                if channel.channel_type == "DASHBOARD"
                else QueuedNotificationAdapter()
            )
            await self.operations.add_delivery(
                NotificationDelivery(
                    incident_id=incident.id,
                    channel_id=channel.id,
                    fingerprint=fingerprint,
                    status=await adapter.deliver(payload),
                    payload=payload,
                )
            )


class MaintenanceService:
    def __init__(self, repository: WorkflowRepository, audit: AuditService) -> None:
        self.repository = repository
        self.audit = audit

    async def create(self, payload: MaintenanceWindowCreate, actor_id: UUID) -> MaintenanceWindow:
        item = await self.repository.add_maintenance(
            MaintenanceWindow(**payload.model_dump(), created_by=actor_id)
        )
        await self._audit(item, "created", actor_id)
        await self.repository.commit()
        return item

    async def list(self) -> list[MaintenanceWindow]:
        return await self.repository.list_maintenance()

    async def delete(self, window_id: UUID, actor_id: UUID) -> None:
        item = await self.repository.get_maintenance(window_id)
        if item is None:
            raise AppError("MAINTENANCE_NOT_FOUND", "Maintenance window not found.", 404)
        await self.repository.delete_maintenance(item)
        await self._audit(item, "deleted", actor_id)
        await self.repository.commit()

    async def _audit(self, item: MaintenanceWindow, action: str, actor_id: UUID) -> None:
        await self.audit.record(
            AuditEventType.CONFIGURATION_CHANGED,
            success=True,
            actor_user_id=actor_id,
            event_metadata={
                "resource_type": "MaintenanceWindow",
                "resource_id": str(item.id),
                "action": action,
            },
        )
