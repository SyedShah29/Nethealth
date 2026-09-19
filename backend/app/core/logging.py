import logging
import sys
from collections.abc import MutableMapping
from typing import Any

import structlog

from app.core.config import Settings


def _add_required_fields(
    _logger: Any, _method_name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    event_dict.setdefault("event_name", event_dict.get("event"))
    event_dict.setdefault("entity", None)
    event_dict.setdefault("device_id", None)
    event_dict.setdefault("subscriber_id", None)
    event_dict.setdefault("incident_id", None)
    return event_dict


def _restore_event_field(
    _logger: Any, _method_name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    event_dict["event"] = event_dict.pop("event_name")
    return event_dict


def configure_logging(settings: Settings) -> None:
    logging.basicConfig(stream=sys.stdout, level=settings.log_level, format="%(message)s")
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
        _add_required_fields,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.processors.EventRenamer("message"),
            _restore_event_field,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level.upper())
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(service=settings.service_name)
