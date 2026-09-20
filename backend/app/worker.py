from celery import Celery

from app.core.config import get_settings

settings = get_settings()
celery_app = Celery("nethealth", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(name="nethealth.collectors.poll")  # type: ignore[untyped-decorator]
def poll_collector(device_id: str, collector_type: str) -> dict[str, str]:
    """Queue boundary for configured collector workers.

    Credential material and target configuration are resolved by the worker
    service; task arguments contain identifiers only.
    """
    return {"device_id": device_id, "collector_type": collector_type, "status": "queued"}
