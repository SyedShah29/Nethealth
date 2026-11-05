from __future__ import annotations

from collections import Counter, deque
from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.errors import AppError
from app.models.enums import AuditEventType
from app.models.topology import TopologyEdge, TopologyNode
from app.repositories.topology import TopologyRepository
from app.schemas.topology import EntityReference, TopologyImpactResponse
from app.services.audit import AuditService


class TopologyGraph:
    """Deterministic directed graph where every edge points upstream to downstream."""

    def __init__(self, nodes: list[TopologyNode], edges: list[TopologyEdge]) -> None:
        self.nodes = {node.id: node for node in nodes}
        self.downstream: dict[UUID, set[UUID]] = {node.id: set() for node in nodes}
        self.upstream: dict[UUID, set[UUID]] = {node.id: set() for node in nodes}
        for edge in edges:
            if edge.source_node_id in self.nodes and edge.target_node_id in self.nodes:
                self.downstream[edge.source_node_id].add(edge.target_node_id)
                self.upstream[edge.target_node_id].add(edge.source_node_id)

    def descendants(self, node_id: UUID) -> list[TopologyNode]:
        return self._walk(node_id, self.downstream)

    def ancestors_with_distance(self, node_id: UUID) -> dict[UUID, int]:
        distances = {node_id: 0}
        queue: deque[UUID] = deque([node_id])
        while queue:
            current = queue.popleft()
            for parent in self.upstream.get(current, set()):
                if parent not in distances:
                    distances[parent] = distances[current] + 1
                    queue.append(parent)
        return distances

    def common_ancestor(self, node_ids: list[UUID]) -> TopologyNode | None:
        candidates = self.common_ancestors(node_ids)
        return candidates[0] if candidates else None

    def common_ancestors(self, node_ids: list[UUID]) -> list[TopologyNode]:
        if not node_ids:
            return []
        paths = [self.ancestors_with_distance(node_id) for node_id in node_ids]
        shared = set(paths[0]).intersection(*(set(path) for path in paths[1:]))
        ranked = sorted(
            shared,
            key=lambda candidate: (
                max(path[candidate] for path in paths),
                sum(path[candidate] for path in paths),
                str(candidate),
            ),
        )
        return [self.nodes[item] for item in ranked]

    def _walk(self, node_id: UUID, adjacency: dict[UUID, set[UUID]]) -> list[TopologyNode]:
        visited: set[UUID] = set()
        queue: deque[UUID] = deque(sorted(adjacency.get(node_id, set()), key=str))
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            queue.extend(sorted(adjacency.get(current, set()), key=str))
        return [self.nodes[item] for item in visited]

    def would_create_cycle(self, source_node_id: UUID, target_node_id: UUID) -> bool:
        return source_node_id == target_node_id or source_node_id in {
            item.id for item in self.descendants(target_node_id)
        }


class TopologyService:
    def __init__(self, repository: TopologyRepository, audit: AuditService) -> None:
        self.repository = repository
        self.audit = audit

    async def graph(self) -> tuple[list[TopologyNode], list[TopologyEdge]]:
        return await self.repository.list_nodes(), await self.repository.list_edges()

    async def get_node(self, node_id: UUID) -> TopologyNode:
        node = await self.repository.get_node(node_id)
        if node is None:
            raise AppError("TOPOLOGY_NODE_NOT_FOUND", "Topology node not found.", 404)
        return node

    async def create_node(self, data: dict[str, Any], actor_user_id: UUID) -> TopologyNode:
        data["node_type"] = str(data["node_type"])
        if data.get("entity_type") is not None:
            data["entity_type"] = str(data["entity_type"]).upper()
        try:
            node = await self.repository.add_node(TopologyNode(**data))
            await self._audit("TopologyNode", node.id, "created", actor_user_id)
            await self.repository.session.commit()
            return node
        except IntegrityError as exc:
            await self.repository.session.rollback()
            raise AppError(
                "TOPOLOGY_NODE_CONFLICT",
                "Topology node conflicts with existing topology data.",
                409,
            ) from exc

    async def update_node(
        self, node_id: UUID, data: dict[str, Any], actor_user_id: UUID
    ) -> TopologyNode:
        node = await self.get_node(node_id)
        for key, value in data.items():
            setattr(node, key, value)
        await self.repository.session.flush()
        await self._audit("TopologyNode", node.id, "updated", actor_user_id)
        await self.repository.session.commit()
        return node

    async def delete_node(self, node_id: UUID, actor_user_id: UUID) -> None:
        node = await self.get_node(node_id)
        await self.repository.delete(node)
        await self._audit("TopologyNode", node.id, "deleted", actor_user_id)
        await self.repository.session.commit()

    async def create_edge(self, data: dict[str, Any], actor_user_id: UUID) -> TopologyEdge:
        source = await self.get_node(data["source_node_id"])
        target = await self.get_node(data["target_node_id"])
        nodes, edges = await self.graph()
        graph = TopologyGraph(nodes, edges)
        if graph.would_create_cycle(source.id, target.id):
            raise AppError(
                "TOPOLOGY_CYCLE",
                "The topology edge would create a dependency cycle.",
                422,
            )
        try:
            edge = await self.repository.add_edge(TopologyEdge(**data))
            await self._audit("TopologyEdge", edge.id, "created", actor_user_id)
            await self.repository.session.commit()
            return edge
        except IntegrityError as exc:
            await self.repository.session.rollback()
            raise AppError(
                "TOPOLOGY_EDGE_CONFLICT",
                "Topology edge conflicts with existing topology data.",
                409,
            ) from exc

    async def delete_edge(self, edge_id: UUID, actor_user_id: UUID) -> None:
        edge = await self.repository.get_edge(edge_id)
        if edge is None:
            raise AppError("TOPOLOGY_EDGE_NOT_FOUND", "Topology edge not found.", 404)
        await self.repository.delete(edge)
        await self._audit("TopologyEdge", edge.id, "deleted", actor_user_id)
        await self.repository.session.commit()

    async def downstream(self, node_id: UUID) -> list[TopologyNode]:
        await self.get_node(node_id)
        nodes, edges = await self.graph()
        return TopologyGraph(nodes, edges).descendants(node_id)

    async def impact(self, node_id: UUID) -> TopologyImpactResponse:
        source = await self.get_node(node_id)
        downstream = await self.downstream(node_id)
        return TopologyImpactResponse(
            source_node=source,
            downstream_nodes=downstream,
            counts_by_type=dict(Counter(item.node_type for item in downstream)),
        )

    async def common_infrastructure(self, entities: list[EntityReference]) -> TopologyNode:
        nodes, edges = await self.graph()
        resolved: list[TopologyNode] = []
        for entity in entities:
            node = await self.repository.find_node(entity.entity_type, entity.entity_id)
            if node is None:
                raise AppError(
                    "TOPOLOGY_ENTITY_NOT_FOUND",
                    "An affected entity is not represented in topology.",
                    404,
                )
            resolved.append(node)
        ancestor = TopologyGraph(nodes, edges).common_ancestor([item.id for item in resolved])
        if ancestor is None:
            raise AppError(
                "COMMON_INFRASTRUCTURE_NOT_FOUND",
                "The entities have no shared topology ancestor.",
                404,
            )
        return ancestor

    async def subscribers_for_pon(self, pon_id: UUID) -> list[TopologyNode]:
        pon = await self._entity_node("PON", str(pon_id))
        return [item for item in await self.downstream(pon.id) if item.node_type == "SUBSCRIBER"]

    async def olt_for_subscriber(self, subscriber_id: str) -> TopologyNode:
        subscriber = await self._entity_node("SUBSCRIBER", subscriber_id)
        return await self._nearest_ancestor(subscriber.id, {"OLT"})

    async def upstream_for_olt(self, olt_id: UUID) -> TopologyNode:
        olt = await self._entity_node("OLT", str(olt_id))
        return await self._nearest_ancestor(
            olt.id, {"TRANSIT", "CORE", "BNG", "BRAS", "AGGREGATION", "ACCESS"}
        )

    async def downstream_devices_for_interface(self, interface_id: UUID) -> list[TopologyNode]:
        nodes, edges = await self.graph()
        graph = TopologyGraph(nodes, edges)
        starts = [edge.target_node_id for edge in edges if edge.interface_id == interface_id]
        device_types = {"TRANSIT", "CORE", "BNG", "BRAS", "AGGREGATION", "ACCESS", "OLT"}
        found: dict[UUID, TopologyNode] = {}
        for start in starts:
            candidates = [graph.nodes[start], *graph.descendants(start)]
            found.update({item.id: item for item in candidates if item.node_type in device_types})
        return sorted(found.values(), key=lambda item: (item.node_type, item.name))

    async def _entity_node(self, entity_type: str, entity_id: str) -> TopologyNode:
        node = await self.repository.find_node(entity_type, entity_id)
        if node is None:
            raise AppError(
                "TOPOLOGY_ENTITY_NOT_FOUND",
                "The requested entity is not represented in topology.",
                404,
            )
        return node

    async def _nearest_ancestor(self, node_id: UUID, allowed_types: set[str]) -> TopologyNode:
        nodes, edges = await self.graph()
        graph = TopologyGraph(nodes, edges)
        distances = graph.ancestors_with_distance(node_id)
        candidates = [
            node
            for candidate_id, node in graph.nodes.items()
            if candidate_id != node_id
            and node.node_type in allowed_types
            and candidate_id in distances
        ]
        if not candidates:
            raise AppError(
                "UPSTREAM_DEPENDENCY_NOT_FOUND",
                "No matching upstream dependency exists.",
                404,
            )
        return min(candidates, key=lambda item: (distances[item.id], str(item.id)))

    async def _audit(
        self, resource_type: str, resource_id: UUID, action: str, actor_user_id: UUID
    ) -> None:
        await self.audit.record(
            AuditEventType.CONFIGURATION_CHANGED,
            success=True,
            actor_user_id=actor_user_id,
            event_metadata={
                "resource_type": resource_type,
                "resource_id": str(resource_id),
                "action": action,
            },
        )
