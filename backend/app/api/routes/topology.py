from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies.auth import (
    get_topology_service,
    require_permission,
    require_trusted_origin,
)
from app.models.auth import User
from app.models.enums import PermissionCode
from app.models.topology import TopologyEdge, TopologyNode
from app.schemas.topology import (
    CommonInfrastructureRequest,
    TopologyEdgeCreate,
    TopologyEdgeResponse,
    TopologyGraphResponse,
    TopologyImpactResponse,
    TopologyNodeCreate,
    TopologyNodeResponse,
    TopologyNodeUpdate,
)
from app.services.topology import TopologyService

router = APIRouter(prefix="/topology")
read_topology = require_permission(PermissionCode.TOPOLOGY_READ.value)
manage_topology = require_permission(PermissionCode.DEVICES_MANAGE.value)


@router.get("", response_model=TopologyGraphResponse)
async def get_topology(
    service: Annotated[TopologyService, Depends(get_topology_service)],
    _user: Annotated[User, Depends(read_topology)],
) -> dict[str, list[TopologyNode] | list[TopologyEdge]]:
    nodes, edges = await service.graph()
    return {"nodes": nodes, "edges": edges}


@router.post(
    "/nodes",
    response_model=TopologyNodeResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_trusted_origin)],
)
async def create_node(
    payload: TopologyNodeCreate,
    service: Annotated[TopologyService, Depends(get_topology_service)],
    user: Annotated[User, Depends(manage_topology)],
) -> TopologyNode:
    return await service.create_node(payload.model_dump(), user.id)


@router.patch(
    "/nodes/{node_id}",
    response_model=TopologyNodeResponse,
    dependencies=[Depends(require_trusted_origin)],
)
async def update_node(
    node_id: UUID,
    payload: TopologyNodeUpdate,
    service: Annotated[TopologyService, Depends(get_topology_service)],
    user: Annotated[User, Depends(manage_topology)],
) -> TopologyNode:
    return await service.update_node(
        node_id, payload.model_dump(exclude_unset=True), user.id
    )


@router.delete(
    "/nodes/{node_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_trusted_origin)],
)
async def delete_node(
    node_id: UUID,
    service: Annotated[TopologyService, Depends(get_topology_service)],
    user: Annotated[User, Depends(manage_topology)],
) -> None:
    await service.delete_node(node_id, user.id)


@router.post(
    "/edges",
    response_model=TopologyEdgeResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_trusted_origin)],
)
async def create_edge(
    payload: TopologyEdgeCreate,
    service: Annotated[TopologyService, Depends(get_topology_service)],
    user: Annotated[User, Depends(manage_topology)],
) -> TopologyEdge:
    return await service.create_edge(payload.model_dump(), user.id)


@router.delete(
    "/edges/{edge_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_trusted_origin)],
)
async def delete_edge(
    edge_id: UUID,
    service: Annotated[TopologyService, Depends(get_topology_service)],
    user: Annotated[User, Depends(manage_topology)],
) -> None:
    await service.delete_edge(edge_id, user.id)


@router.get("/nodes/{node_id}/downstream", response_model=list[TopologyNodeResponse])
async def downstream_nodes(
    node_id: UUID,
    service: Annotated[TopologyService, Depends(get_topology_service)],
    _user: Annotated[User, Depends(read_topology)],
) -> list[TopologyNode]:
    return await service.downstream(node_id)


@router.get("/nodes/{node_id}/impact", response_model=TopologyImpactResponse)
async def failure_impact(
    node_id: UUID,
    service: Annotated[TopologyService, Depends(get_topology_service)],
    _user: Annotated[User, Depends(read_topology)],
) -> TopologyImpactResponse:
    return await service.impact(node_id)


@router.post(
    "/common-infrastructure",
    response_model=TopologyNodeResponse,
    dependencies=[Depends(require_trusted_origin)],
)
async def common_infrastructure(
    payload: CommonInfrastructureRequest,
    service: Annotated[TopologyService, Depends(get_topology_service)],
    _user: Annotated[User, Depends(read_topology)],
) -> TopologyNode:
    return await service.common_infrastructure(payload.entities)


@router.get("/pons/{pon_id}/subscribers", response_model=list[TopologyNodeResponse])
async def subscribers_for_pon(
    pon_id: UUID,
    service: Annotated[TopologyService, Depends(get_topology_service)],
    _user: Annotated[User, Depends(read_topology)],
) -> list[TopologyNode]:
    return await service.subscribers_for_pon(pon_id)


@router.get("/subscribers/{subscriber_id}/olt", response_model=TopologyNodeResponse)
async def olt_for_subscriber(
    subscriber_id: str,
    service: Annotated[TopologyService, Depends(get_topology_service)],
    _user: Annotated[User, Depends(read_topology)],
) -> TopologyNode:
    return await service.olt_for_subscriber(subscriber_id)


@router.get("/olts/{olt_id}/upstream", response_model=TopologyNodeResponse)
async def upstream_for_olt(
    olt_id: UUID,
    service: Annotated[TopologyService, Depends(get_topology_service)],
    _user: Annotated[User, Depends(read_topology)],
) -> TopologyNode:
    return await service.upstream_for_olt(olt_id)


@router.get(
    "/interfaces/{interface_id}/downstream-devices",
    response_model=list[TopologyNodeResponse],
)
async def downstream_devices_for_interface(
    interface_id: UUID,
    service: Annotated[TopologyService, Depends(get_topology_service)],
    _user: Annotated[User, Depends(read_topology)],
) -> list[TopologyNode]:
    return await service.downstream_devices_for_interface(interface_id)
