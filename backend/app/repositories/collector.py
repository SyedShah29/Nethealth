# ruff: noqa
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.collectors.status import StatusTracker
from app.models.collector import CollectorStatusRecord

class CollectorStatusRepository:
    def __init__(self, session: AsyncSession) -> None: self.session = session
    async def save(self, device_id: UUID, collector_type: str, worker: str | None, status: StatusTracker) -> CollectorStatusRecord:
        result = await self.session.execute(select(CollectorStatusRecord).where(CollectorStatusRecord.device_id == device_id, CollectorStatusRecord.collector_type == collector_type))
        record = result.scalar_one_or_none()
        if record is None:
            record = CollectorStatusRecord(device_id=device_id, collector_type=collector_type)
            self.session.add(record)
        record.last_successful_poll = status.last_successful_poll
        record.last_failed_poll = status.last_failed_poll
        record.failure_count = status.failure_tracker.failures
        record.latency_ms = status.latency_ms
        record.current_health = status.health
        record.current_worker = worker
        await self.session.flush()
        return record

    async def list(self, device_id: UUID | None = None) -> list[CollectorStatusRecord]:
        query = select(CollectorStatusRecord).order_by(CollectorStatusRecord.updated_at.desc())
        if device_id is not None: query = query.where(CollectorStatusRecord.device_id == device_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
