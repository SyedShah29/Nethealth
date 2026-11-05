# ruff: noqa
from dataclasses import dataclass


@dataclass(slots=True)
class FailureTracker:
    threshold: int = 3
    failures: int = 0

    def record_success(self) -> None:
        self.failures = 0

    def record_failure(self) -> bool:
        self.failures += 1
        return self.failures >= self.threshold
