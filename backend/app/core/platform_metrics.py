from collections import deque
from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class ApiMetricSnapshot:
    request_count: int
    error_count: int
    average_response_ms: float
    maximum_response_ms: float


class ApiMetrics:
    def __init__(self, sample_limit: int = 10_000) -> None:
        self._durations: deque[float] = deque(maxlen=sample_limit)
        self._request_count = 0
        self._error_count = 0
        self._lock = Lock()

    def observe(self, duration_ms: float, status_code: int) -> None:
        with self._lock:
            self._request_count += 1
            if status_code >= 500:
                self._error_count += 1
            self._durations.append(duration_ms)

    def snapshot(self) -> ApiMetricSnapshot:
        with self._lock:
            durations = list(self._durations)
            return ApiMetricSnapshot(
                request_count=self._request_count,
                error_count=self._error_count,
                average_response_ms=(
                    round(sum(durations) / len(durations), 3) if durations else 0.0
                ),
                maximum_response_ms=round(max(durations), 3) if durations else 0.0,
            )


api_metrics = ApiMetrics()
