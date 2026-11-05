from datetime import datetime
from uuid import UUID

from sqlalchemy import String, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fiber import OLT, ONU, PON
from app.models.inventory import Device, Site
from app.models.metrics import MetricSample
from app.models.operations import CapacityAssessment, Incident, IncidentEvent, OperationalAnomaly
from app.models.subscriber import Subscriber
from app.models.topology import TopologyEdge, TopologyNode
from app.models.workflows import (
    EscalationEvent,
    EscalationPolicy,
    FieldPhoto,
    FieldTask,
    MaintenanceWindow,
)


class WorkflowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_task(self, item: FieldTask) -> FieldTask:
        self.session.add(item)
        await self.session.flush()
        return item

    async def get_task(self, task_id: UUID) -> FieldTask | None:
        return await self.session.get(FieldTask, task_id)

    async def list_tasks(self, technician_id: UUID | None = None) -> list[FieldTask]:
        statement = select(FieldTask)
        if technician_id is not None:
            statement = statement.where(FieldTask.assigned_technician_id == technician_id)
        result = await self.session.execute(statement.order_by(FieldTask.updated_at.desc()))
        return list(result.scalars())

    async def add_photo(self, item: FieldPhoto) -> FieldPhoto:
        self.session.add(item)
        await self.session.flush()
        return item

    async def get_photo(self, photo_id: UUID) -> FieldPhoto | None:
        return await self.session.get(FieldPhoto, photo_id)

    async def list_photos(self, task_id: UUID) -> list[FieldPhoto]:
        result = await self.session.execute(
            select(FieldPhoto).where(FieldPhoto.task_id == task_id).order_by(FieldPhoto.created_at)
        )
        return list(result.scalars())

    async def add_policy(self, item: EscalationPolicy) -> EscalationPolicy:
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_policies(self) -> list[EscalationPolicy]:
        result = await self.session.execute(
            select(EscalationPolicy).order_by(EscalationPolicy.name)
        )
        return list(result.scalars())

    async def add_escalation(self, item: EscalationEvent) -> EscalationEvent:
        self.session.add(item)
        await self.session.flush()
        return item

    async def escalation_exists(self, incident_id: UUID, policy_id: UUID, step: int) -> bool:
        result = await self.session.execute(
            select(EscalationEvent.id).where(
                EscalationEvent.incident_id == incident_id,
                EscalationEvent.policy_id == policy_id,
                EscalationEvent.step_index == step,
            )
        )
        return result.scalar_one_or_none() is not None

    async def add_maintenance(self, item: MaintenanceWindow) -> MaintenanceWindow:
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_maintenance(self) -> list[MaintenanceWindow]:
        result = await self.session.execute(
            select(MaintenanceWindow).order_by(MaintenanceWindow.starts_at.desc())
        )
        return list(result.scalars())

    async def delete_maintenance(self, item: MaintenanceWindow) -> None:
        await self.session.delete(item)
        await self.session.flush()

    async def get_maintenance(self, window_id: UUID) -> MaintenanceWindow | None:
        return await self.session.get(MaintenanceWindow, window_id)

    async def active_maintenance(
        self, entity_type: str, entity_id: str, observed_at: datetime
    ) -> MaintenanceWindow | None:
        scopes: list[tuple[str, str]] = [(entity_type.upper(), entity_id)]
        if entity_type.upper() == "DEVICE":
            try:
                device_id = UUID(entity_id)
            except ValueError:
                device_id = None
            device = await self.session.get(Device, device_id) if device_id is not None else None
            if device is not None:
                scopes.append(("SITE", str(device.site_id)))
        node = (
            await self.session.execute(
                select(TopologyNode).where(
                    TopologyNode.entity_type == entity_type.upper(),
                    TopologyNode.entity_id == entity_id,
                )
            )
        ).scalar_one_or_none()
        if node is not None and node.attributes.get("site_id"):
            scopes.append(("SITE", str(node.attributes["site_id"])))
        result = await self.session.execute(
            select(MaintenanceWindow)
            .where(
                or_(
                    *[
                        (MaintenanceWindow.scope_type == scope_type)
                        & (MaintenanceWindow.scope_id == scope_id)
                        for scope_type, scope_id in scopes
                    ]
                ),
                MaintenanceWindow.starts_at <= observed_at,
                MaintenanceWindow.ends_at >= observed_at,
            )
            .order_by(MaintenanceWindow.starts_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def upstream_active_incident(self, entity_type: str, entity_id: str) -> Incident | None:
        nodes = list((await self.session.execute(select(TopologyNode))).scalars())
        edges = list((await self.session.execute(select(TopologyEdge))).scalars())
        target = next(
            (
                item
                for item in nodes
                if item.entity_type == entity_type.upper() and item.entity_id == entity_id
            ),
            None,
        )
        if target is None:
            return None
        node_by_id = {item.id: item for item in nodes}
        upstream: set[UUID] = set()
        queue = [target.id]
        while queue:
            current = queue.pop(0)
            for edge in edges:
                if edge.target_node_id == current and edge.source_node_id not in upstream:
                    upstream.add(edge.source_node_id)
                    queue.append(edge.source_node_id)
        if not upstream:
            return None
        incidents = list(
            (
                await self.session.execute(
                    select(Incident)
                    .where(Incident.status.in_(("OPEN", "ACKNOWLEDGED", "INVESTIGATING")))
                    .order_by(Incident.first_seen)
                )
            ).scalars()
        )
        for incident in incidents:
            if any(
                node_by_id[node_id].entity_type == incident.primary_entity_type
                and node_by_id[node_id].entity_id == incident.primary_entity_id
                for node_id in upstream
            ):
                return incident
        return None

    async def incidents(self) -> list[Incident]:
        return list((await self.session.execute(select(Incident))).scalars())

    async def incident_events(self) -> list[IncidentEvent]:
        return list((await self.session.execute(select(IncidentEvent))).scalars())

    async def anomalies(self) -> list[OperationalAnomaly]:
        return list((await self.session.execute(select(OperationalAnomaly))).scalars())

    async def capacity(self) -> list[CapacityAssessment]:
        return list((await self.session.execute(select(CapacityAssessment))).scalars())

    async def availability_metrics(self) -> list[MetricSample]:
        result = await self.session.execute(
            select(MetricSample).where(
                MetricSample.entity_type == "DEVICE",
                MetricSample.metric_name.in_(("reachable", "availability")),
            )
        )
        return list(result.scalars())

    async def olt_health(self) -> list[tuple[OLT, Device]]:
        result = await self.session.execute(
            select(OLT, Device).join(Device, Device.id == OLT.device_id)
        )
        return list(result.tuples().all())

    async def search_subscribers(self, query: str, limit: int) -> list[Subscriber]:
        pattern = f"%{query}%"
        result = await self.session.execute(
            select(Subscriber)
            .where(
                or_(
                    Subscriber.subscriber_id.ilike(pattern),
                    Subscriber.current_ip.ilike(pattern),
                    Subscriber.mac_address.ilike(pattern),
                )
            )
            .limit(limit)
        )
        return list(result.scalars())

    async def search_fiber(self, query: str, limit: int) -> list[tuple[str, str, str]]:
        pattern = f"%{query}%"
        results: list[tuple[str, str, str]] = []
        onus = list(
            (
                await self.session.execute(
                    select(ONU)
                    .where(or_(ONU.serial_number.ilike(pattern), ONU.onu_identifier.ilike(pattern)))
                    .limit(limit)
                )
            ).scalars()
        )
        results.extend(("ONU", str(item.id), item.serial_number) for item in onus)
        olts = list(
            (
                await self.session.execute(
                    select(OLT, Device)
                    .join(Device, Device.id == OLT.device_id)
                    .where(or_(Device.name.ilike(pattern), Device.hostname.ilike(pattern)))
                    .limit(limit)
                )
            ).all()
        )
        results.extend(("OLT", str(olt.id), device.name) for olt, device in olts)
        pons = list(
            (
                await self.session.execute(
                    select(PON).where(PON.id.cast(String).ilike(pattern)).limit(limit)
                )
            ).scalars()
        )
        results.extend(
            ("PON", str(item.id), f"PON {item.frame}/{item.slot}/{item.port}") for item in pons
        )
        return results[:limit]

    async def search_inventory(self, query: str, limit: int) -> list[tuple[str, str, str]]:
        pattern = f"%{query}%"
        devices = list(
            (
                await self.session.execute(
                    select(Device)
                    .where(or_(Device.name.ilike(pattern), Device.hostname.ilike(pattern)))
                    .limit(limit)
                )
            ).scalars()
        )
        sites = list(
            (
                await self.session.execute(
                    select(Site)
                    .where(or_(Site.name.ilike(pattern), Site.code.ilike(pattern)))
                    .limit(limit)
                )
            ).scalars()
        )
        return [
            *(("DEVICE", str(item.id), f"{item.name} ({item.hostname})") for item in devices),
            *(("SITE", str(item.id), f"{item.name} ({item.code})") for item in sites),
        ][:limit]

    async def search_incidents(self, query: str, limit: int) -> list[Incident]:
        pattern = f"%{query}%"
        result = await self.session.execute(
            select(Incident)
            .where(
                or_(
                    Incident.id.cast(String).ilike(pattern),
                    Incident.title.ilike(pattern),
                    Incident.category.ilike(pattern),
                )
            )
            .limit(limit)
        )
        return list(result.scalars())

    async def commit(self) -> None:
        await self.session.commit()
