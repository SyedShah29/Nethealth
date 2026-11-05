from collections.abc import Awaitable
from datetime import UTC, datetime, timedelta
from shutil import disk_usage
from time import perf_counter
from typing import cast

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.platform_metrics import api_metrics
from app.schemas.system import PlatformHealthResponse


class PlatformHealthService:
    def __init__(self, session: AsyncSession, redis: Redis) -> None:
        self.session = session
        self.redis = redis

    async def get(self) -> PlatformHealthResponse:
        started = perf_counter()
        await self.session.execute(text("SELECT 1"))
        database_latency_ms = round((perf_counter() - started) * 1000, 3)
        collector_rows = (
            await self.session.execute(
                text(
                    "SELECT current_health, count(*) FROM collector_status "
                    "GROUP BY current_health"
                )
            )
        ).all()
        failed_polls = int(
            (
                await self.session.execute(
                    text("SELECT count(*) FROM collector_status WHERE failure_count > 0")
                )
            ).scalar_one()
        )
        ingested = int(
            (
                await self.session.execute(
                    text("SELECT count(*) FROM metric_samples WHERE timestamp >= :since"),
                    {"since": datetime.now(UTC) - timedelta(minutes=5)},
                )
            ).scalar_one()
        )
        notification_failures = int(
            (
                await self.session.execute(
                    text(
                        "SELECT count(*) FROM notification_deliveries "
                        "WHERE status IN ('FAILED', 'ERROR')"
                    )
                )
            ).scalar_one()
        )
        database_size = int(
            (
                await self.session.execute(text("SELECT pg_database_size(current_database())"))
            ).scalar_one()
        )
        queue_depth = int(await cast(Awaitable[int], self.redis.llen("celery")))
        worker_seen = await self.redis.get("nethealth:worker:last_seen")
        worker_seen_text = worker_seen.decode() if isinstance(worker_seen, bytes) else worker_seen
        disk = disk_usage("/")
        api = api_metrics.snapshot()
        status = (
            "WARNING"
            if failed_polls or notification_failures or worker_seen_text is None
            else "HEALTHY"
        )
        return PlatformHealthResponse(
            status=status,
            collector_health={str(key): int(cast(int, value)) for key, value in collector_rows},
            worker={
                "status": "ONLINE" if worker_seen_text else "UNKNOWN",
                "last_seen": worker_seen_text,
            },
            queue_depth=queue_depth,
            database_latency_ms=database_latency_ms,
            api={
                "request_count": api.request_count,
                "error_count": api.error_count,
                "average_response_ms": api.average_response_ms,
                "maximum_response_ms": api.maximum_response_ms,
            },
            failed_polls=failed_polls,
            metrics_ingestion_per_minute=round(ingested / 5, 3),
            disk={
                "total_bytes": disk.total,
                "used_bytes": disk.used,
                "free_bytes": disk.free,
                "used_percent": round(disk.used / disk.total * 100, 3),
            },
            database_size_bytes=database_size,
            notification_failures=notification_failures,
        )
