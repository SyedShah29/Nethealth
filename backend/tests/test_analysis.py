from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.core.errors import AppError
from app.schemas.analysis import CorrelationRequest, FaultObservation
from app.services.analysis import (
    CorrelationService,
    classify_root_cause,
    correlation_classification,
    correlation_confidence,
    shared_dimension_evidence,
)


def test_correlation_classifies_supported_common_ancestors() -> None:
    assert correlation_classification("PON") == "PON_OUTAGE"
    assert correlation_classification("OLT") == "OLT_OUTAGE"
    assert correlation_classification("CORE") == "CORE_OUTAGE"
    assert correlation_classification(None) == "UNCORRELATED_FAULTS"


def test_correlation_confidence_is_discrete_and_evidence_derived() -> None:
    assert correlation_confidence(None, 1, False) == "LOW"
    assert correlation_confidence("UP", 20, False) == "MEDIUM"
    assert correlation_confidence("DOWN", 20, False) == "HIGH"
    assert correlation_confidence("DOWN", 20, True) == "CONFIRMED"


def test_shared_site_and_uplink_dimensions_are_preserved_as_evidence() -> None:
    first = SimpleNamespace(attributes={"site_id": "SITE-1", "uplink_id": "UPLINK-4"})
    second = SimpleNamespace(attributes={"site_id": "SITE-1", "uplink_id": "UPLINK-4"})
    assert shared_dimension_evidence([first, second]) == [
        {"fact": "shared_site_id", "value": "SITE-1"},
        {"fact": "shared_uplink_id", "value": "UPLINK-4"},
    ]


def test_pon_level_root_cause_is_evidence_based() -> None:
    classification, severity, evidence, checks = classify_root_cause(
        {
            "olt_reachable": True,
            "pon_down": True,
            "other_pons_healthy": True,
            "offline_subscriber_count": 118,
        },
        None,
    )
    assert classification == "PON_LEVEL_OUTAGE"
    assert severity == "HIGH"
    assert {item["fact"] for item in evidence} == {
        "olt_reachable",
        "pon_down",
        "other_pons_healthy",
        "offline_subscriber_count",
    }
    assert len(checks) == 3


def test_link_congestion_root_cause_requires_all_signals() -> None:
    classification, severity, _, checks = classify_root_cause(
        {
            "router_reachable": True,
            "uplink_utilization_pct": 98,
            "latency_increasing": True,
            "packet_loss_increasing": True,
        },
        None,
    )
    assert (classification, severity) == ("LINK_CONGESTION", "HIGH")
    assert checks


def test_subscriber_optical_fault_isolated_from_healthy_neighbors() -> None:
    classification, severity, evidence, _ = classify_root_cause(
        {
            "offline_subscriber_count": 1,
            "neighbors_healthy": True,
            "optical_degraded_before_disconnect": True,
        },
        None,
    )
    assert (classification, severity) == ("SUBSCRIBER_OPTICAL_FAULT", "MEDIUM")
    assert all("fact" in item and "value" in item for item in evidence)


def test_unknown_evidence_does_not_invent_a_diagnosis() -> None:
    classification, severity, evidence, checks = classify_root_cause({}, None)
    assert (classification, severity) == ("UNDETERMINED", "INFO")
    assert evidence == [{"fact": "matched_classifier", "value": False}]
    assert checks


def test_correlation_can_drive_root_cause_without_new_claims() -> None:
    classification, severity, evidence, _ = classify_root_cause({}, "PON_OUTAGE")
    assert (classification, severity) == ("PON_LEVEL_OUTAGE", "HIGH")
    assert evidence[0]["value"] == "PON_OUTAGE"


def test_olt_and_core_failures_have_deterministic_classifiers() -> None:
    olt = classify_root_cause(
        {"olt_reachable": False, "offline_subscriber_count": 20}, None
    )
    core = classify_root_cause(
        {"core_reachable": False, "offline_subscriber_count": 2000}, None
    )
    assert olt[:2] == ("OLT_LEVEL_OUTAGE", "CRITICAL")
    assert core[:2] == ("CORE_LEVEL_OUTAGE", "CRITICAL")


@pytest.mark.asyncio
async def test_correlation_rejects_observations_outside_window() -> None:
    now = datetime.now(UTC)
    request = CorrelationRequest(
        observations=[
            FaultObservation(entity_type="SUBSCRIBER", entity_id="SUB-1", observed_at=now),
            FaultObservation(
                entity_type="SUBSCRIBER",
                entity_id="SUB-2",
                observed_at=now + timedelta(seconds=61),
            ),
        ],
        window_seconds=60,
    )
    service = CorrelationService(object(), object(), 60)  # type: ignore[arg-type]
    with pytest.raises(AppError) as caught:
        await service.correlate(request)
    assert caught.value.code == "CORRELATION_WINDOW_EXCEEDED"
