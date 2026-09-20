# ruff: noqa
from datetime import datetime, timezone
from dataclasses import dataclass
from app.collectors.reliability import FailureTracker

@dataclass(slots=True)
class StatusTracker:
    failure_tracker: FailureTracker
    last_successful_poll: datetime | None = None
    last_failed_poll: datetime | None = None
    latency_ms: float | None = None
    health: str = "UNKNOWN"
    def success(self, latency_ms: float | None) -> None:
        self.failure_tracker.record_success(); self.last_successful_poll = datetime.now(timezone.utc); self.latency_ms = latency_ms; self.health = "HEALTHY"
    def failure(self) -> None:
        self.last_failed_poll = datetime.now(timezone.utc); self.health = "UNREACHABLE" if self.failure_tracker.record_failure() else "DEGRADED"
