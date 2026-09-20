from __future__ import annotations

from typing import Any
from uuid import UUID

from app.core.errors import AppError
from app.models.analysis import OutageCorrelation, RootCauseAssessment
from app.models.topology import TopologyNode
from app.repositories.analysis import AnalysisRepository
from app.repositories.topology import TopologyRepository
from app.schemas.analysis import CorrelationRequest, RootCauseRequest
from app.services.topology import TopologyGraph

UNHEALTHY_STATUSES = {"RED", "CRITICAL", "DOWN", "UNREACHABLE"}
CORRELATION_DIMENSIONS = (
    "site_id",
    "olt_id",
    "pon_id",
    "access_switch_id",
    "aggregation_switch_id",
    "uplink_id",
    "router_id",
)


def correlation_classification(node_type: str | None) -> str:
    mapping = {
        "PON": "PON_OUTAGE",
        "OLT": "OLT_OUTAGE",
        "CORE": "CORE_OUTAGE",
        "TRANSIT": "TRANSIT_OUTAGE",
        "BNG": "BNG_OUTAGE",
        "BRAS": "BRAS_OUTAGE",
        "AGGREGATION": "AGGREGATION_OUTAGE",
        "ACCESS": "ACCESS_OUTAGE",
    }
    return mapping.get(node_type or "", "UNCORRELATED_FAULTS")


def correlation_confidence(
    ancestor_status: str | None,
    affected_count: int,
    component_failure_confirmed: bool,
) -> str:
    ancestor_unhealthy = (
        ancestor_status is not None and ancestor_status.upper() in UNHEALTHY_STATUSES
    )
    if component_failure_confirmed and ancestor_unhealthy:
        return "CONFIRMED"
    if ancestor_unhealthy and affected_count >= 2:
        return "HIGH"
    if ancestor_status is not None and affected_count >= 2:
        return "MEDIUM"
    return "LOW"


def shared_dimension_evidence(nodes: list[Any]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for dimension in CORRELATION_DIMENSIONS:
        values = [node.attributes.get(dimension) for node in nodes]
        if values and values[0] is not None and all(value == values[0] for value in values):
            evidence.append(
                {"fact": f"shared_{dimension}", "value": values[0]}
            )
    return evidence


def lowest_common_failing_ancestor(
    graph: TopologyGraph, node_ids: list[UUID]
) -> TopologyNode | None:
    common_ancestors = graph.common_ancestors(node_ids)
    return next(
        (
            item
            for item in common_ancestors
            if item.status.upper() in UNHEALTHY_STATUSES
        ),
        common_ancestors[0] if common_ancestors else None,
    )


class CorrelationService:
    def __init__(
        self,
        analysis_repository: AnalysisRepository,
        topology_repository: TopologyRepository,
        default_window_seconds: int,
    ) -> None:
        self.analysis_repository = analysis_repository
        self.topology_repository = topology_repository
        self.default_window_seconds = default_window_seconds

    async def correlate(self, request: CorrelationRequest) -> OutageCorrelation:
        window_seconds = request.window_seconds or self.default_window_seconds
        timestamps = [item.observed_at for item in request.observations]
        window_started_at = min(timestamps)
        window_ended_at = max(timestamps)
        observed_span = (window_ended_at - window_started_at).total_seconds()
        if observed_span > window_seconds:
            raise AppError(
                "CORRELATION_WINDOW_EXCEEDED",
                "Fault observations exceed the configured correlation window.",
                422,
            )

        topology_nodes, topology_edges = (
            await self.topology_repository.list_nodes(),
            await self.topology_repository.list_edges(),
        )
        graph = TopologyGraph(topology_nodes, topology_edges)
        affected_nodes = []
        for observation in request.observations:
            node = await self.topology_repository.find_node(
                observation.entity_type, observation.entity_id
            )
            if node is None:
                raise AppError(
                    "TOPOLOGY_ENTITY_NOT_FOUND",
                    "An affected entity is not represented in topology.",
                    404,
                )
            affected_nodes.append(node)

        ancestor = lowest_common_failing_ancestor(
            graph, [item.id for item in affected_nodes]
        )
        classification = correlation_classification(
            ancestor.node_type if ancestor is not None else None
        )
        downstream_subscribers = (
            [
                item
                for item in graph.descendants(ancestor.id)
                if item.node_type == "SUBSCRIBER"
            ]
            if ancestor is not None
            else []
        )
        affected_subscriber_ids = {
            item.id for item in affected_nodes if item.node_type == "SUBSCRIBER"
        }
        subscriber_ratio = (
            len(affected_subscriber_ids) / len(downstream_subscribers)
            if downstream_subscribers
            else 0.0
        )
        component_confirmed = any(
            observation.evidence.get("component_failure_confirmed") is True
            for observation in request.observations
        )
        confidence = correlation_confidence(
            ancestor.status if ancestor is not None else None,
            len(affected_nodes),
            component_confirmed,
        )

        evidence: list[dict[str, Any]] = [
            {
                "fact": "correlation_window_seconds",
                "value": window_seconds,
            },
            {
                "fact": "affected_entity_count",
                "value": len(request.observations),
            },
        ]
        if ancestor is not None:
            evidence.extend(
                [
                    {
                        "fact": "common_ancestor",
                        "node_id": str(ancestor.id),
                        "node_type": ancestor.node_type,
                        "name": ancestor.name,
                        "status": ancestor.status,
                    },
                    {
                        "fact": "affected_subscriber_ratio",
                        "affected": len(affected_subscriber_ids),
                        "total_downstream": len(downstream_subscribers),
                        "ratio": round(subscriber_ratio, 4),
                    },
                ]
            )
        evidence.extend(shared_dimension_evidence(affected_nodes))

        item = await self.analysis_repository.add_correlation(
            OutageCorrelation(
                window_started_at=window_started_at,
                window_ended_at=window_ended_at,
                window_seconds=window_seconds,
                common_ancestor_node_id=ancestor.id if ancestor else None,
                classification=classification,
                confidence=confidence,
                affected_count=len(request.observations),
                affected_entities=[
                    {
                        "entity_type": observation.entity_type.upper(),
                        "entity_id": observation.entity_id,
                    }
                    for observation in request.observations
                ],
                evidence=evidence,
            )
        )
        await self.analysis_repository.session.commit()
        return item

    async def list_correlations(self, limit: int) -> list[OutageCorrelation]:
        return await self.analysis_repository.list_correlations(limit)


def classify_root_cause(
    signals: dict[str, bool | float | int | str],
    correlation_class: str | None,
) -> tuple[str, str, list[dict[str, Any]], list[str]]:
    offline_value = signals.get("offline_subscriber_count", 0)
    offline_count = (
        int(offline_value)
        if isinstance(offline_value, (int, float)) and not isinstance(offline_value, bool)
        else 0
    )
    utilization_value = signals.get("uplink_utilization_pct", 0)
    utilization = (
        float(utilization_value)
        if isinstance(utilization_value, (int, float))
        and not isinstance(utilization_value, bool)
        else 0.0
    )
    cases: list[
        tuple[bool, str, str, list[str], list[str]]
    ] = [
        (
            signals.get("olt_reachable") is True
            and signals.get("pon_down") is True
            and signals.get("other_pons_healthy") is True
            and offline_count >= 2,
            "PON_LEVEL_OUTAGE",
            "HIGH",
            ["olt_reachable", "pon_down", "other_pons_healthy", "offline_subscriber_count"],
            [
                "Check the PON interface state and alarms.",
                "Inspect the feeder fiber.",
                "Inspect the splitter and distribution path.",
            ],
        ),
        (
            signals.get("router_reachable") is True
            and utilization >= 90
            and signals.get("latency_increasing") is True
            and signals.get("packet_loss_increasing") is True,
            "LINK_CONGESTION",
            "HIGH",
            [
                "router_reachable",
                "uplink_utilization_pct",
                "latency_increasing",
                "packet_loss_increasing",
            ],
            [
                "Check uplink utilization and queue drops.",
                "Check traffic distribution and upstream capacity.",
            ],
        ),
        (
            offline_count == 1
            and signals.get("neighbors_healthy") is True
            and signals.get("optical_degraded_before_disconnect") is True,
            "SUBSCRIBER_OPTICAL_FAULT",
            "MEDIUM",
            [
                "offline_subscriber_count",
                "neighbors_healthy",
                "optical_degraded_before_disconnect",
            ],
            [
                "Inspect the subscriber drop fiber and connectors.",
                "Measure optical power at the ONU and distribution point.",
            ],
        ),
        (
            signals.get("olt_reachable") is False and offline_count >= 2,
            "OLT_LEVEL_OUTAGE",
            "CRITICAL",
            ["olt_reachable", "offline_subscriber_count"],
            ["Check OLT power, uplinks, and management reachability."],
        ),
        (
            signals.get("core_reachable") is False and offline_count >= 2,
            "CORE_LEVEL_OUTAGE",
            "CRITICAL",
            ["core_reachable", "offline_subscriber_count"],
            ["Check core device reachability, power, and upstream links."],
        ),
    ]
    for matched, classification, severity, keys, recommendations in cases:
        if matched:
            return (
                classification,
                severity,
                [{"fact": key, "value": signals.get(key)} for key in keys],
                recommendations,
            )

    correlation_mapping = {
        "PON_OUTAGE": (
            "PON_LEVEL_OUTAGE",
            "HIGH",
            ["Check the PON interface, feeder fiber, and distribution path."],
        ),
        "OLT_OUTAGE": (
            "OLT_LEVEL_OUTAGE",
            "CRITICAL",
            ["Check OLT reachability, power, and uplinks."],
        ),
        "CORE_OUTAGE": (
            "CORE_LEVEL_OUTAGE",
            "CRITICAL",
            ["Check core reachability and upstream connectivity."],
        ),
    }
    if correlation_class in correlation_mapping:
        classification, severity, recommendations = correlation_mapping[correlation_class]
        return (
            classification,
            severity,
            [{"fact": "correlation_classification", "value": correlation_class}],
            recommendations,
        )
    return (
        "UNDETERMINED",
        "INFO",
        [{"fact": "matched_classifier", "value": False}],
        ["Collect additional reachability, topology, optical, and performance evidence."],
    )


class RootCauseService:
    def __init__(self, repository: AnalysisRepository) -> None:
        self.repository = repository

    async def classify(self, request: RootCauseRequest) -> RootCauseAssessment:
        correlation = None
        if request.correlation_id is not None:
            correlation = await self.repository.get_correlation(request.correlation_id)
            if correlation is None:
                raise AppError(
                    "CORRELATION_NOT_FOUND", "Correlation result not found.", 404
                )
        classification, severity, evidence, recommended_checks = classify_root_cause(
            request.signals,
            correlation.classification if correlation is not None else None,
        )
        assessment = await self.repository.add_assessment(
            RootCauseAssessment(
                correlation_id=request.correlation_id,
                classification=classification,
                severity=severity,
                evidence=evidence,
                affected_entities=[item.model_dump() for item in request.affected_entities],
                recommended_checks=recommended_checks,
            )
        )
        await self.repository.session.commit()
        return assessment

    async def get(self, item_id: UUID) -> RootCauseAssessment:
        assessment = await self.repository.get_assessment(item_id)
        if assessment is None:
            raise AppError(
                "ROOT_CAUSE_NOT_FOUND", "Root cause assessment not found.", 404
            )
        return assessment

    async def list(self, limit: int) -> list[RootCauseAssessment]:
        return await self.repository.list_assessments(limit)
