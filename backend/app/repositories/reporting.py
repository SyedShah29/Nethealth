from datetime import datetime
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fiber import OLT, ONU, PON
from app.models.inventory import Device
from app.models.metrics import MetricSample
from app.models.operations import (
    CapacityAssessment,
    Incident,
    OperationalAnomaly,
    SubscriberHealthScore,
)
from app.models.subscriber import Subscriber


class ReportingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def latest_metrics(
        self,
        entity_type: str,
        entity_id: str,
        since: datetime,
        limit: int = 500,
    ) -> list[MetricSample]:
        result = await self.session.execute(
            select(MetricSample)
            .where(
                MetricSample.entity_type == entity_type,
                MetricSample.entity_id == entity_id,
                MetricSample.timestamp >= since,
            )
            .order_by(MetricSample.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars())

    async def dashboard_summary(self) -> dict[str, Any]:
        device_rows = (
            await self.session.execute(select(Device.status, func.count()).group_by(Device.status))
        ).all()
        subscriber_rows = (
            await self.session.execute(
                select(Subscriber.status, func.count()).group_by(Subscriber.status)
            )
        ).all()
        incident_rows = (
            await self.session.execute(
                select(Incident.severity, func.count())
                .where(Incident.status.in_(("OPEN", "ACKNOWLEDGED", "INVESTIGATING")))
                .group_by(Incident.severity)
            )
        ).all()
        devices = {str(status).upper(): count for status, count in device_rows}
        subscribers = {str(status).upper(): count for status, count in subscriber_rows}
        incidents = {str(severity).upper(): count for severity, count in incident_rows}
        return {
            "devices": {"total": sum(devices.values()), **devices},
            "subscribers": {"total": sum(subscribers.values()), **subscribers},
            "active_incidents": {"total": sum(incidents.values()), **incidents},
        }

    async def widget_rows(self) -> dict[str, list[dict[str, Any]]]:
        incidents = list(
            (
                await self.session.execute(
                    select(Incident)
                    .where(Incident.status.in_(("OPEN", "ACKNOWLEDGED", "INVESTIGATING")))
                    .order_by(Incident.last_seen.desc())
                    .limit(10)
                )
            ).scalars()
        )
        devices = list(
            (
                await self.session.execute(
                    select(Device).where(Device.status != "UP").order_by(Device.name).limit(10)
                )
            ).scalars()
        )
        olt_rows = (
            await self.session.execute(
                select(OLT, Device.status)
                .join(Device, Device.id == OLT.device_id)
                .order_by(OLT.vendor, OLT.model)
                .limit(10)
            )
        ).all()
        pons = list(
            (await self.session.execute(select(PON).where(PON.status != "UP").limit(10))).scalars()
        )
        latest_health = (
            select(
                SubscriberHealthScore.subscriber_id,
                func.max(SubscriberHealthScore.evaluated_at).label("evaluated_at"),
            )
            .group_by(SubscriberHealthScore.subscriber_id)
            .subquery()
        )
        health_rows = (
            await self.session.execute(
                select(SubscriberHealthScore.category, func.count())
                .join(
                    latest_health,
                    (SubscriberHealthScore.subscriber_id == latest_health.c.subscriber_id)
                    & (SubscriberHealthScore.evaluated_at == latest_health.c.evaluated_at),
                )
                .group_by(SubscriberHealthScore.category)
            )
        ).all()
        capacity = list(
            (
                await self.session.execute(
                    select(CapacityAssessment)
                    .where(CapacityAssessment.category != "NORMAL")
                    .order_by(desc(CapacityAssessment.sustained_percent))
                    .limit(10)
                )
            ).scalars()
        )
        packet_loss = list(
            (
                await self.session.execute(
                    select(MetricSample)
                    .where(MetricSample.metric_name == "packet_loss_percent")
                    .order_by(desc(MetricSample.value), desc(MetricSample.timestamp))
                    .limit(10)
                )
            ).scalars()
        )
        anomalies = list(
            (
                await self.session.execute(
                    select(OperationalAnomaly)
                    .where(OperationalAnomaly.anomaly_type != "NO_ANOMALY")
                    .order_by(OperationalAnomaly.detected_at.desc())
                    .limit(20)
                )
            ).scalars()
        )
        optical_onus = list(
            (
                await self.session.execute(
                    select(ONU)
                    .where(ONU.rx_power.is_not(None), ONU.status != "ONLINE")
                    .limit(10)
                )
            ).scalars()
        )
        return {
            "active_incidents": [
                {
                    "id": str(item.id),
                    "title": item.title,
                    "severity": item.severity,
                    "status": item.status,
                }
                for item in incidents
            ],
            "device_health": [
                {"id": str(item.id), "name": item.name, "status": item.status} for item in devices
            ],
            "olt_status": [
                {
                    "id": str(item.id),
                    "vendor": item.vendor,
                    "model": item.model,
                    "status": status,
                }
                for item, status in olt_rows
            ],
            "pon_status": [
                {"id": str(item.id), "status": item.status, "subscribers": item.subscriber_count}
                for item in pons
            ],
            "subscriber_health_distribution": [
                {"category": category, "count": count} for category, count in health_rows
            ],
            "top_congested_links": [
                {
                    "entity_id": item.entity_id,
                    "value": item.sustained_percent,
                    "category": item.category,
                }
                for item in capacity
            ],
            "highest_packet_loss_links": [
                {
                    "entity_id": item.entity_id,
                    "value": item.value,
                    "timestamp": item.timestamp.isoformat(),
                }
                for item in packet_loss
            ],
            "unstable_subscribers": [
                {"entity_id": item.entity_id, "type": item.anomaly_type}
                for item in anomalies
                if item.metric_name in {"disconnect_frequency", "disconnect_events"}
            ][:10],
            "optical_warnings": [
                {"entity_id": item.entity_id, "type": item.anomaly_type}
                for item in anomalies
                if item.anomaly_type == "OPTICAL_DEGRADATION_WARNING"
            ][:10] + [
                {"entity_id": str(item.id), "type": "ONU_STATUS", "status": item.status}
                for item in optical_onus
            ],
            "recent_outages": [
                {"id": str(item.id), "title": item.title, "status": item.status}
                for item in incidents
                if "OUTAGE" in item.category
            ],
        }
