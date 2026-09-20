from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.models.topology import TopologyEdge, TopologyNode
from app.schemas.topology import EntityReference, TopologyEdgeCreate, TopologyNodeCreate
from app.services.analysis import lowest_common_failing_ancestor
from app.services.topology import TopologyGraph, TopologyService


def node(node_type: str, name: str, *, entity_id: str | None = None) -> TopologyNode:
    now = datetime.now(UTC)
    return TopologyNode(
        id=uuid4(),
        node_type=node_type,
        name=name,
        entity_type=node_type if entity_id else None,
        entity_id=entity_id,
        status="UP",
        attributes={},
        created_at=now,
        updated_at=now,
    )


def edge(source: TopologyNode, target: TopologyNode) -> TopologyEdge:
    return TopologyEdge(
        id=uuid4(),
        source_node_id=source.id,
        target_node_id=target.id,
        relation="DEPENDS_ON",
        attributes={},
        created_at=datetime.now(UTC),
    )


def test_topology_graph_answers_dependency_and_impact_queries() -> None:
    core = node("CORE", "CORE-01")
    olt = node("OLT", "OLT-04", entity_id=str(uuid4()))
    pon = node("PON", "PON-7", entity_id=str(uuid4()))
    onu = node("ONU", "ONU-38")
    subscriber_a = node("SUBSCRIBER", "SUB-1", entity_id="SUB-1")
    subscriber_b = node("SUBSCRIBER", "SUB-2", entity_id="SUB-2")
    graph = TopologyGraph(
        [core, olt, pon, onu, subscriber_a, subscriber_b],
        [
            edge(core, olt),
            edge(olt, pon),
            edge(pon, onu),
            edge(onu, subscriber_a),
            edge(onu, subscriber_b),
        ],
    )

    assert {item.name for item in graph.descendants(pon.id)} == {
        "ONU-38",
        "SUB-1",
        "SUB-2",
    }
    assert graph.common_ancestor([subscriber_a.id, subscriber_b.id]) is onu
    assert [item.name for item in graph.common_ancestors([subscriber_a.id, subscriber_b.id])] == [
        "ONU-38",
        "PON-7",
        "OLT-04",
        "CORE-01",
    ]
    olt.status = "DOWN"
    assert lowest_common_failing_ancestor(
        graph, [subscriber_a.id, subscriber_b.id]
    ) is olt
    assert graph.common_ancestor([pon.id, subscriber_a.id]) is pon
    assert graph.ancestors_with_distance(subscriber_a.id)[olt.id] == 3
    assert graph.would_create_cycle(subscriber_a.id, core.id) is True
    assert graph.would_create_cycle(core.id, subscriber_a.id) is False


def test_disconnected_entities_have_no_common_ancestor() -> None:
    first = node("SUBSCRIBER", "SUB-1")
    second = node("SUBSCRIBER", "SUB-2")
    assert TopologyGraph([first, second], []).common_ancestor([first.id, second.id]) is None


def test_topology_schema_rejects_partial_entity_reference_and_self_edge() -> None:
    with pytest.raises(ValueError):
        TopologyNodeCreate(node_type="PON", name="PON-1", entity_type="PON")
    node_id = uuid4()
    with pytest.raises(ValueError):
        TopologyEdgeCreate(source_node_id=node_id, target_node_id=node_id)


def test_topology_database_constraints_are_declared() -> None:
    node_constraints = {item.name for item in TopologyNode.__table__.constraints}
    edge_constraints = {item.name for item in TopologyEdge.__table__.constraints}
    assert "uq_topology_nodes_entity" in node_constraints
    assert "ck_topology_nodes_type" in node_constraints
    assert "uq_topology_edges_nodes" in edge_constraints
    assert "ck_topology_edges_not_self" in edge_constraints
    assert TopologyEdge.__table__.c.interface_id.type.python_type is UUID


class FakeTopologyRepository:
    def __init__(self, nodes: list[TopologyNode], edges: list[TopologyEdge]) -> None:
        self.nodes = nodes
        self.edges = edges

    async def list_nodes(self) -> list[TopologyNode]:
        return self.nodes

    async def list_edges(self) -> list[TopologyEdge]:
        return self.edges

    async def get_node(self, node_id: UUID) -> TopologyNode | None:
        return next((item for item in self.nodes if item.id == node_id), None)

    async def find_node(self, entity_type: str, entity_id: str) -> TopologyNode | None:
        return next(
            (
                item
                for item in self.nodes
                if item.entity_type == entity_type.upper() and item.entity_id == entity_id
            ),
            None,
        )


@pytest.mark.asyncio
async def test_required_topology_queries_use_the_dependency_graph() -> None:
    interface_id = uuid4()
    core = node("CORE", "CORE-01", entity_id=str(uuid4()))
    access = node("ACCESS", "ACCESS-01", entity_id=str(uuid4()))
    olt = node("OLT", "OLT-04", entity_id=str(uuid4()))
    pon = node("PON", "PON-7", entity_id=str(uuid4()))
    onu = node("ONU", "ONU-38", entity_id=str(uuid4()))
    subscriber_a = node("SUBSCRIBER", "SUB-1", entity_id="SUB-1")
    subscriber_b = node("SUBSCRIBER", "SUB-2", entity_id="SUB-2")
    links = [
        edge(core, access),
        edge(access, olt),
        edge(olt, pon),
        edge(pon, onu),
        edge(onu, subscriber_a),
        edge(onu, subscriber_b),
    ]
    links[0].interface_id = interface_id
    repository = FakeTopologyRepository(
        [core, access, olt, pon, onu, subscriber_a, subscriber_b], links
    )
    service = TopologyService(repository, object())  # type: ignore[arg-type]

    assert {item.name for item in await service.subscribers_for_pon(UUID(pon.entity_id or ""))} == {
        "SUB-1",
        "SUB-2",
    }
    assert await service.olt_for_subscriber("SUB-1") is olt
    assert await service.upstream_for_olt(UUID(olt.entity_id or "")) is access
    assert await service.common_infrastructure(
        [
            EntityReference(entity_type="SUBSCRIBER", entity_id="SUB-1"),
            EntityReference(entity_type="SUBSCRIBER", entity_id="SUB-2"),
        ]
    ) is onu
    assert {item.name for item in await service.downstream_devices_for_interface(interface_id)} == {
        "ACCESS-01",
        "OLT-04",
    }
    impact = await service.impact(pon.id)
    assert impact.counts_by_type == {"ONU": 1, "SUBSCRIBER": 2}
