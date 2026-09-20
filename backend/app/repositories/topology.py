from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.topology import TopologyEdge, TopologyNode


class TopologyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_nodes(self) -> list[TopologyNode]:
        result = await self.session.execute(
            select(TopologyNode).order_by(TopologyNode.node_type, TopologyNode.name)
        )
        return list(result.scalars())

    async def list_edges(self) -> list[TopologyEdge]:
        result = await self.session.execute(
            select(TopologyEdge).order_by(TopologyEdge.created_at, TopologyEdge.id)
        )
        return list(result.scalars())

    async def get_node(self, node_id: UUID) -> TopologyNode | None:
        return await self.session.get(TopologyNode, node_id)

    async def get_edge(self, edge_id: UUID) -> TopologyEdge | None:
        return await self.session.get(TopologyEdge, edge_id)

    async def find_node(self, entity_type: str, entity_id: str) -> TopologyNode | None:
        result = await self.session.execute(
            select(TopologyNode).where(
                TopologyNode.entity_type == entity_type.upper(),
                TopologyNode.entity_id == entity_id,
            )
        )
        return result.scalar_one_or_none()

    async def add_node(self, node: TopologyNode) -> TopologyNode:
        self.session.add(node)
        await self.session.flush()
        return node

    async def add_edge(self, edge: TopologyEdge) -> TopologyEdge:
        self.session.add(edge)
        await self.session.flush()
        return edge

    async def delete(self, item: TopologyNode | TopologyEdge) -> None:
        await self.session.delete(item)
        await self.session.flush()
