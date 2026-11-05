# ruff: noqa
from datetime import datetime, timezone
from app.collectors.schemas import SyslogEvent


def normalize_syslog(
    message: str, device: str, *, timestamp: datetime | None = None
) -> SyslogEvent:
    value = message.strip()
    facility = severity = None
    if value.startswith("<") and ">" in value:
        prefix, value = value[1:].split(">", 1)
        try:
            priority = int(prefix)
            facility, severity = priority // 8, priority % 8
        except ValueError:
            pass
    normalized = value.strip().lower()
    event_type = "syslog.message"
    for marker, category in (
        ("link down", "interface.down"),
        ("link up", "interface.up"),
        ("authentication failure", "security.authentication_failure"),
        ("temperature", "environment.temperature"),
        ("power", "environment.power"),
    ):
        if marker in normalized:
            event_type = category
            break
    return SyslogEvent(
        device,
        timestamp or datetime.now(timezone.utc),
        facility,
        severity,
        value.strip(),
        event_type,
    )
