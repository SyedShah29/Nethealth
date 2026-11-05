from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from random import Random
from typing import Any


@dataclass(frozen=True)
class SimulatorScale:
    olts: int = 20
    pons: int = 320
    onus: int = 10_000
    subscribers: int = 10_000
    switches: int = 20
    core_routers: int = 4

    def validate(self) -> None:
        values = asdict(self)
        if any(value < 1 for value in values.values()):
            raise ValueError("simulator scale values must be positive")
        if self.pons < self.olts or self.onus < self.pons or self.subscribers > self.onus:
            raise ValueError("simulator hierarchy is inconsistent")


class FailureKind(StrEnum):
    ONU_FAILURE = "ONU_FAILURE"
    PON_FAILURE = "PON_FAILURE"
    OLT_FAILURE = "OLT_FAILURE"
    ACCESS_SWITCH_FAILURE = "ACCESS_SWITCH_FAILURE"
    AGGREGATION_FAILURE = "AGGREGATION_FAILURE"
    CORE_FAILURE = "CORE_FAILURE"
    CONGESTION = "CONGESTION"
    OPTICAL_DEGRADATION = "OPTICAL_DEGRADATION"
    PACKET_LOSS = "PACKET_LOSS"
    LATENCY_SPIKE = "LATENCY_SPIKE"


@dataclass(frozen=True)
class SimulatedFailure:
    kind: FailureKind
    entity_id: str
    expected_diagnosis: str
    affected_subscribers: int
    evidence: list[dict[str, Any]]


class NetworkSimulator:
    """Deterministic, read-only synthetic network generator."""

    def __init__(self, scale: SimulatorScale | None = None, seed: int = 10482) -> None:
        self.scale = scale or SimulatorScale()
        self.scale.validate()
        self.random = Random(seed)

    def snapshot(self, sample_index: int = 0) -> dict[str, Any]:
        random = Random(self.random.random() + sample_index)
        return {
            "sample_index": sample_index,
            "scale": asdict(self.scale),
            "metrics": {
                "cpu_percent": round(random.uniform(15, 75), 3),
                "memory_percent": round(random.uniform(20, 80), 3),
                "traffic_percent": round(random.uniform(10, 92), 3),
                "latency_ms": round(random.uniform(1, 35), 3),
                "packet_loss_percent": round(random.uniform(0, 2), 3),
                "optical_rx_dbm": round(random.uniform(-25, -14), 3),
                "disconnects": random.randrange(0, 20),
            },
        }

    def trigger(self, kind: FailureKind, entity_index: int = 0) -> SimulatedFailure:
        if entity_index < 0:
            raise ValueError("entity index must not be negative")
        subscribers_per_pon = max(1, self.scale.subscribers // self.scale.pons)
        subscribers_per_olt = max(1, self.scale.subscribers // self.scale.olts)
        mapping: dict[FailureKind, tuple[str, str, int, dict[str, Any]]] = {
            FailureKind.ONU_FAILURE: ("ONU", "SUBSCRIBER_OPTICAL_FAULT", 1, {"online": False}),
            FailureKind.PON_FAILURE: (
                "PON",
                "PON_OUTAGE",
                subscribers_per_pon,
                {"pon_online": False},
            ),
            FailureKind.OLT_FAILURE: (
                "OLT",
                "OLT_OUTAGE",
                subscribers_per_olt,
                {"olt_reachable": False},
            ),
            FailureKind.ACCESS_SWITCH_FAILURE: (
                "SWITCH",
                "ACCESS_OUTAGE",
                subscribers_per_olt,
                {"reachable": False},
            ),
            FailureKind.AGGREGATION_FAILURE: (
                "AGGREGATION",
                "AGGREGATION_OUTAGE",
                self.scale.subscribers // 2,
                {"reachable": False},
            ),
            FailureKind.CORE_FAILURE: (
                "CORE",
                "CORE_OUTAGE",
                self.scale.subscribers,
                {"reachable": False},
            ),
            FailureKind.CONGESTION: (
                "INTERFACE",
                "LINK_CONGESTION",
                self.scale.subscribers // 4,
                {"utilization_percent": 98.0},
            ),
            FailureKind.OPTICAL_DEGRADATION: (
                "ONU",
                "SUBSCRIBER_OPTICAL_FAULT",
                1,
                {"rx_dbm": -29.0},
            ),
            FailureKind.PACKET_LOSS: (
                "INTERFACE",
                "PACKET_LOSS",
                self.scale.subscribers // 4,
                {"packet_loss_percent": 35.0},
            ),
            FailureKind.LATENCY_SPIKE: (
                "INTERFACE",
                "LATENCY_DEGRADATION",
                self.scale.subscribers // 4,
                {"latency_ms": 250.0},
            ),
        }
        entity_type, diagnosis, affected, fact = mapping[kind]
        return SimulatedFailure(
            kind=kind,
            entity_id=f"{entity_type}-{entity_index + 1}",
            expected_diagnosis=diagnosis,
            affected_subscribers=affected,
            evidence=[{"fact": key, "value": value} for key, value in fact.items()],
        )

    def disconnect_storm(self, count: int = 5_000, window_seconds: int = 30) -> dict[str, Any]:
        if not 1 <= count <= self.scale.subscribers:
            raise ValueError("disconnect count exceeds simulated subscribers")
        if window_seconds < 1:
            raise ValueError("window must be positive")
        shared_pon = "PON-4"
        return {
            "events_ingested": count,
            "window_seconds": window_seconds,
            "incidents_created": 1,
            "classification": "PON_OUTAGE",
            "shared_dependency": shared_pon,
            "affected_subscribers": count,
        }
