import asyncio
from uuid import UUID

from celery import Celery

from app.collectors.runtime import due_assignment_ids, poll_assignment
from app.core.config import get_settings
from app.db.session import engine

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
        }
    },
)


@celery_app.task(name="nethealth.collectors.poll")  # type: ignore[untyped-decorator]
def poll_collector(assignment_id: str) -> dict[str, str]:
    """Execute one assignment while keeping credentials out of task arguments."""
    async def execute() -> dict[str, str]:
        try:
            return await poll_assignment(UUID(assignment_id))
        finally:
            await engine.dispose()

    return asyncio.run(execute())


@celery_app.task(name="nethealth.collectors.dispatch")  # type: ignore[untyped-decorator]
def dispatch_due_collectors() -> dict[str, object]:
    async def find_due() -> list[UUID]:
        try:
            return await due_assignment_ids()
        finally:
            await engine.dispose()

    assignment_ids = asyncio.run(find_due())
    for assignment_id in assignment_ids:
        poll_collector.delay(str(assignment_id))
    return {"status": "dispatched", "assignment_count": len(assignment_ids)}
