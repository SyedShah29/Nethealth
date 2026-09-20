from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TopologyNodeType(StrEnum):
    TRANSIT = "TRANSIT"
    CORE = "CORE"
    BNG = "BNG"
    BRAS = "BRAS"
    AGGREGATION = "AGGREGATION"
    ACCESS = "ACCESS"
    OLT = "OLT"
    PON = "PON"
    ONU = "ONU"
    SUBSCRIBER = "SUBSCRIBER"


class TopologyNodeCreate(BaseModel):
    node_type: TopologyNodeType
    name: str = Field(min_length=1, max_length=160)
    entity_type: str | None = Field(default=None, min_length=1, max_length=32)
    entity_id: str | None = Field(default=None, min_length=1, max_length=255)
    status: str = Field(default="UNKNOWN", min_length=1, max_length=32)
    attributes: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_entity_reference(self) -> "TopologyNodeCreate":
        if (self.entity_type is None) != (self.entity_id is None):
            raise ValueError("entity_type and entity_id must be provided together")
        return self


class TopologyNodeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    status: str | None = Field(default=None, min_length=1, max_length=32)
    attributes: dict[str, Any] | None = None


class TopologyNodeResponse(TopologyNodeCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class TopologyEdgeCreate(BaseModel):
    source_node_id: UUID
    target_node_id: UUID
    interface_id: UUID | None = None
    relation: str = Field(default="DEPENDS_ON", min_length=1, max_length=32)
    attributes: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def reject_self_edge(self) -> "TopologyEdgeCreate":
        if self.source_node_id == self.target_node_id:
            raise ValueError("a topology edge cannot connect a node to itself")
        return self


class TopologyEdgeResponse(TopologyEdgeCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


class TopologyGraphResponse(BaseModel):
    nodes: list[TopologyNodeResponse]
    edges: list[TopologyEdgeResponse]


class EntityReference(BaseModel):
    entity_type: str = Field(min_length=1, max_length=32)
    entity_id: str = Field(min_length=1, max_length=255)


class CommonInfrastructureRequest(BaseModel):
    entities: list[EntityReference] = Field(min_length=2, max_length=1000)


class TopologyImpactResponse(BaseModel):
    source_node: TopologyNodeResponse
    downstream_nodes: list[TopologyNodeResponse]
    counts_by_type: dict[str, int]
