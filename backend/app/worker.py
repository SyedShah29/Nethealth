import asyncio
from datetime import UTC, datetime
from uuid import UUID

from celery import Celery
from redis import Redis

from app.collectors.runtime import due_assignment_ids, poll_assignment
from app.core.config import get_settings
from app.db.session import async_session_factory, engine
from app.repositories.operations import OperationsRepository
from app.repositories.workflows import WorkflowRepository
from app.services.workflows import EscalationService

settings = get_settings()
celery_app = Celery("nethealth", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "dispatch-due-collectors": {
            "task": "nethealth.collectors.dispatch",
            "schedule": 30.0,
        },
        "evaluate-incident-escalations": {
            "task": "nethealth.incidents.escalate",
            "schedule": 60.0,
        },
    },
)


def mark_worker_seen() -> None:
    client = Redis.from_url(settings.redis_url)
    try:
        client.set("nethealth:worker:last_seen", datetime.now(UTC).isoformat(), ex=180)
    finally:
        client.close()


@celery_app.task(name="nethealth.collectors.poll")  # type: ignore[untyped-decorator]
def poll_collector(assignment_id: str) -> dict[str, str]:
    """Execute one assignment while keeping credentials out of task arguments."""
    mark_worker_seen()

    async def execute() -> dict[str, str]:
        try:
            return await poll_assignment(UUID(assignment_id))
        finally:
            await engine.dispose()

    return asyncio.run(execute())


@celery_app.task(name="nethealth.collectors.dispatch")  # type: ignore[untyped-decorator]
def dispatch_due_collectors() -> dict[str, object]:
    mark_worker_seen()
    async def find_due() -> list[UUID]:
        try:
            return await due_assignment_ids()
        finally:
            await engine.dispose()

    assignment_ids = asyncio.run(find_due())
    for assignment_id in assignment_ids:
        poll_collector.delay(str(assignment_id))
    return {"status": "dispatched", "assignment_count": len(assignment_ids)}


@celery_app.task(name="nethealth.incidents.escalate")  # type: ignore[untyped-decorator]
def evaluate_incident_escalations() -> dict[str, object]:
    mark_worker_seen()
    async def execute() -> int:
        try:
            async with async_session_factory() as session:
                events = await EscalationService(
                    WorkflowRepository(session), OperationsRepository(session)
                ).evaluate()
                return len(events)
        finally:
            await engine.dispose()

    return {"status": "evaluated", "escalation_count": asyncio.run(execute())}
