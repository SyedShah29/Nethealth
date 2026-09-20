import asyncio

import structlog

from app.collectors.schemas import SyslogEvent
from app.collectors.syslog_receiver import serve_syslog
from app.core.config import get_settings
from app.core.logging import configure_logging


def _record_event(event: SyslogEvent) -> None:
    # Raw messages may contain operational or authentication details, so only
    # normalized metadata is emitted to logs.
    structlog.get_logger().info(
        "syslog_event_received",
        entity=event.device,
        event_type=event.event_type,
        facility=event.facility,
        severity=event.severity,
    )


async def _run() -> None:
    settings = get_settings()
    transport = await serve_syslog(
        settings.syslog_bind_host,
        settings.syslog_port,
        _record_event,
    )
    try:
        await asyncio.Future()
    finally:
        transport.close()


def main() -> None:
    settings = get_settings()
    configure_logging(settings)
    asyncio.run(_run())


if __name__ == "__main__":
    main()
