from datetime import datetime
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.metrics import MetricSample
from app.schemas.metrics import (
    MetricQuery,
    MetricResolution,
    MetricSampleCreate,
)

AGGREGATE_VIEWS = {
    MetricResolution.FIVE_MINUTES: "metric_samples_5m",
    MetricResolution.HOURLY: "metric_samples_hourly",
    MetricResolution.DAILY: "metric_samples_daily",
}


class MetricRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_many(self, samples: list[MetricSampleCreate]) -> None:
        self.session.add_all(
            [MetricSample(**sample.model_dump(mode="python")) for sample in samples]
        )
        await self.session.flush()

    async def latest_value(
        self,
        entity_type: str,
        entity_id: str,
        metric_name: str,
        before: datetime,
    ) -> MetricSample | None:
        result = await self.session.execute(
            select(MetricSample)
            .where(
                MetricSample.entity_type == entity_type,
                MetricSample.entity_id == entity_id,
                MetricSample.metric_name == metric_name,
                MetricSample.timestamp < before,
            )
            .order_by(MetricSample.timestamp.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def query_raw(self, query: MetricQuery) -> list[MetricSample]:
        statement = select(MetricSample).where(
            MetricSample.timestamp >= query.start,
            MetricSample.timestamp < query.end,
        )
        if query.entity_type is not None:
            statement = statement.where(MetricSample.entity_type == query.entity_type.value)
        if query.entity_id is not None:
            statement = statement.where(MetricSample.entity_id == query.entity_id)
        if query.metric_name is not None:
            statement = statement.where(MetricSample.metric_name == query.metric_name)
        if query.source is not None:
            statement = statement.where(MetricSample.source == query.source)
        result = await self.session.execute(
            statement.order_by(MetricSample.timestamp).limit(query.limit)
        )
        return list(result.scalars())

    async def query_aggregate(self, query: MetricQuery) -> list[dict[str, Any]]:
        view = AGGREGATE_VIEWS[query.resolution]
        clauses = ["bucket >= :start", "bucket < :end"]
        params: dict[str, Any] = {
            "start": query.start,
            "end": query.end,
            "limit": query.limit,
        }
        for field in ("entity_type", "entity_id", "metric_name", "source"):
            value = getattr(query, field)
            if value is not None:
                clauses.append(f"{field} = :{field}")
                params[field] = value.value if field == "entity_type" else value
        statement = text(
            "SELECT bucket, entity_type, entity_id, metric_name, unit, source, tags, "
            "value_avg, value_min, value_max, value_sum, sample_count "
            f"FROM {view} WHERE {' AND '.join(clauses)} "
            "ORDER BY bucket LIMIT :limit"
        )
        result = await self.session.execute(statement, params)
        return [dict(row) for row in result.mappings().all()]
