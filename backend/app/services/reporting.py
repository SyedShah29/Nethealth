from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.errors import AppError
from app.repositories.fiber import FiberRepository
from app.repositories.operations import OperationsRepository
from app.repositories.reporting import ReportingRepository
from app.repositories.subscriber import SubscriberRepository
from app.schemas.operations import (
    DashboardResponse,
    HealthScoreResponse,
    SubscriberDiagnosticsResponse,
)


class DiagnosticsService:
    def __init__(
        self,
        subscribers: SubscriberRepository,
        fiber: FiberRepository,
        operations: OperationsRepository,
        reporting: ReportingRepository,
    ) -> None:
        self.subscribers = subscribers
        self.fiber = fiber
        self.operations = operations
        self.reporting = reporting

    async def subscriber_360(self, subscriber_id: str) -> SubscriberDiagnosticsResponse:
        subscriber = await self.subscribers.get(subscriber_id)
        if subscriber is None:
            raise AppError("SUBSCRIBER_NOT_FOUND", "Subscriber not found.", 404)
        sessions = await self.subscribers.list_sessions(subscriber_id, limit=500)
        current_session = next((item for item in sessions if item.session_end is None), None)
        onus = await self.fiber.list_onus(subscriber_id=subscriber_id, limit=2)
        onu = onus[0] if onus else None
        pon = await self.fiber.get_pon(onu.pon_id) if onu is not None else None
        olt = await self.fiber.get_olt(onu.olt_id) if onu is not None else None
        now = datetime.now(UTC)
        metrics = await self.reporting.latest_metrics(
            "SUBSCRIBER", subscriber_id, now - timedelta(days=30)
        )
        incident = await self.operations.active_incident_for_subscriber(subscriber_id)
        health = await self.operations.latest_health_score(subscriber_id)

        current_by_name: dict[str, Any] = {}
        for metric in metrics:
            current_by_name.setdefault(metric.metric_name, metric)
        def metric_value(name: str) -> float | None:
            metric = current_by_name.get(name)
            return float(metric.value) if metric is not None else None
        today = now - timedelta(days=1)
        week = now - timedelta(days=7)
        completed = [item for item in sessions if item.session_end is not None]
        durations = [item.duration for item in completed if item.duration is not None]
        diagnosis: dict[str, Any]
        if incident is not None:
            diagnosis = {
                "status": "INCIDENT_RELATED",
                "evidence": [
                    f"Active {incident.category} incident {incident.id}",
                    f"Incident severity is {incident.severity}",
                ],
                "recommended_action": (
                    incident.recommendations[0]
                    if incident.recommendations
                    else "Review the incident timeline."
                ),
            }
        elif (
            subscriber.status.upper() == "OFFLINE"
            and onu is not None
            and onu.status.upper() == "ONLINE"
        ):
            diagnosis = {
                "status": "CUSTOMER_SPECIFIC_ISSUE",
                "evidence": ["Subscriber is offline", "Serving ONU is online"],
                "recommended_action": "Check the subscriber session and drop-side connectivity.",
            }
        else:
            diagnosis = {
                "status": "UNDETERMINED",
                "evidence": ["Available facts do not match a deterministic diagnosis."],
                "recommended_action": (
                    "Collect current reachability, optical, and session evidence."
                ),
            }
        return SubscriberDiagnosticsResponse(
            identity={
                "subscriber_id": subscriber.subscriber_id,
                "external_reference": subscriber.external_reference,
                "package_speed": subscriber.package_speed,
                "status": subscriber.status,
            },
            session={
                "nas": current_session.nas if current_session else subscriber.nas_id,
                "ip": current_session.ip_address if current_session else subscriber.current_ip,
                "session_uptime": metric_value("session_uptime"),
                "last_connection": sessions[0].session_start if sessions else None,
                "last_disconnect": next(
                    (item.session_end for item in sessions if item.session_end), None
                ),
            },
            fiber={
                "olt": str(olt.id) if olt else subscriber.olt_id,
                "pon": str(pon.id) if pon else subscriber.pon_id,
                "onu": onu.onu_identifier if onu else subscriber.onu_id,
                "rx": onu.rx_power if onu else None,
                "tx": onu.tx_power if onu else None,
            },
            performance={
                "latency": metric_value("latency_ms"),
                "packet_loss": metric_value("packet_loss_percent"),
                "current_traffic": {
                    "download_bps": metric_value("download_rate"),
                    "upload_bps": metric_value("upload_rate"),
                },
                "historical_traffic": [
                    {"timestamp": item.timestamp, "metric": item.metric_name, "value": item.value}
                    for item in metrics
                    if item.metric_name in {"download_rate", "upload_rate"}
                ],
            },
            stability={
                "disconnects_today": sum(
                    1
                    for item in sessions
                    if item.session_end and item.session_end >= today
                ),
                "disconnects_last_7_days": sum(
                    1
                    for item in sessions
                    if item.session_end and item.session_end >= week
                ),
                "average_session_duration": (
                    sum(durations) / len(durations) if durations else None
                ),
            },
            incident=(
                {
                    "id": str(incident.id),
                    "severity": incident.severity,
                    "scope": incident.primary_entity_type,
                    "status": incident.status,
                }
                if incident
                else None
            ),
            diagnosis=diagnosis,
            health=HealthScoreResponse.model_validate(health) if health else None,
        )


class DashboardService:
    def __init__(self, reporting: ReportingRepository) -> None:
        self.reporting = reporting

    async def get(self) -> DashboardResponse:
        return DashboardResponse(
            summary=await self.reporting.dashboard_summary(),
            widgets=await self.reporting.widget_rows(),
        )
