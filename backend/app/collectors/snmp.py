from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from uuid import UUID

from app.collectors.base import DeviceCollector
from app.collectors.errors import CollectorConfigurationError
from app.collectors.schemas import DeviceHealth, EnvironmentReading, InterfaceHealth, OpticalMetric


@dataclass(frozen=True, slots=True)
class SnmpProfile:
    version: str = "3"
    username: str = ""
    auth_protocol: str | None = None
    privacy_protocol: str | None = None
    auth_secret: str | None = None
    privacy_secret: str | None = None
    oid_overrides: dict[str, str] = field(default_factory=dict)


SnmpQuery = Callable[[str], Awaitable[object | None]]
SnmpWalk = Callable[[str], Awaitable[list[tuple[str, object]]]]


class SnmpCollector(DeviceCollector):
    collector_type = "SNMP"
    oid_overrides: dict[str, str] = {}

    def __init__(
        self,
        device_id: UUID,
        profile: SnmpProfile,
        query: SnmpQuery | None = None,
        interface_indexes: list[tuple[int, str]] | None = None,
        walk: SnmpWalk | None = None,
    ) -> None:
        super().__init__(device_id)
        self.profile = profile
        if profile.version not in {"2c", "3"}:
            raise CollectorConfigurationError("Unsupported SNMP version.")
        if profile.version == "3" and not profile.username:
            raise CollectorConfigurationError("SNMPv3 username is required.")
        self._query = query
        self.oids = {**self.oid_overrides, **profile.oid_overrides}
        self.interface_indexes = interface_indexes or []
        self._walk = walk

    async def test_connection(self) -> bool:
        return await self._required_query("uptime", "1.3.6.1.2.1.1.3.0") is not None

    async def collect_device_health(self) -> DeviceHealth:
        uptime = await self._required_query("uptime", "1.3.6.1.2.1.1.3.0")
        cpu = await self._required_query("cpu", "1.3.6.1.4.1.2021.11.9.0")
        memory = await self._memory_percent()
        return DeviceHealth(
            self.device_id,
            uptime is not None,
            None,
            None,
            _timeticks_seconds(uptime),
            _float(cpu),
            memory,
        )

    async def collect_interfaces(self) -> list[InterfaceHealth]:
        if self._query is None:
            raise CollectorConfigurationError("SNMP transport is not configured.")
        if self._walk is not None:
            rows = await self._walk("1.3.6.1.2.1.2.2.1.2")
            self.interface_indexes = [
                (int(oid.rsplit(".", 1)[-1]), str(value)) for oid, value in rows
            ]
        results: list[InterfaceHealth] = []
        for index, name in self.interface_indexes:
            values = {
                "admin": await self._query(f"1.3.6.1.2.1.2.2.1.7.{index}"),
                "oper": await self._query(f"1.3.6.1.2.1.2.2.1.8.{index}"),
                "in_octets": await self._query(f"1.3.6.1.2.1.2.2.1.10.{index}"),
                "out_octets": await self._query(f"1.3.6.1.2.1.2.2.1.16.{index}"),
                "in_errors": await self._query(f"1.3.6.1.2.1.2.2.1.14.{index}"),
                "out_errors": await self._query(f"1.3.6.1.2.1.2.2.1.20.{index}"),
                "in_discards": await self._query(f"1.3.6.1.2.1.2.2.1.13.{index}"),
                "out_discards": await self._query(f"1.3.6.1.2.1.2.2.1.19.{index}"),
            }
            results.append(
                InterfaceHealth(
                    self.device_id,
                    name,
                    _interface_status(values["admin"]),
                    _interface_status(values["oper"]),
                    _int(values["in_octets"]),
                    _int(values["out_octets"]),
                    _sum_optional(values["in_errors"], values["out_errors"]),
                    _sum_optional(values["in_discards"], values["out_discards"]),
                )
            )
        return results

    async def collect_environment(self) -> list[EnvironmentReading]:
        defaults = {
            "cpu": ("1.3.6.1.4.1.2021.11.9.0", "%"),
            "temperature": ("1.3.6.1.4.1.2021.13.16.5.1.2.1", "celsius"),
        }
        readings: list[EnvironmentReading] = []
        for metric, (default_oid, unit) in defaults.items():
            value = await self._required_query(metric, default_oid)
            readings.append(EnvironmentReading(self.device_id, metric, _float(value), unit))
        for metric, unit in (("power", "watts"), ("fan", "rpm")):
            oid = self.oids.get(metric)
            if oid is not None:
                readings.append(
                    EnvironmentReading(
                        self.device_id,
                        metric,
                        _float(await self._query_oid(oid)),
                        unit,
                    )
                )
        readings.append(
            EnvironmentReading(self.device_id, "memory", await self._memory_percent(), "%")
        )
        return readings

    async def collect_optical_metrics(self) -> list[OpticalMetric]:
        readings: list[OpticalMetric] = []
        for metric, unit in (("rx_power", "dBm"), ("tx_power", "dBm")):
            oid_base = self.oids.get(metric)
            if oid_base is None:
                continue
            for index, name in self.interface_indexes:
                readings.append(
                    OpticalMetric(
                        self.device_id,
                        name,
                        metric,
                        _float(await self._query_oid(f"{oid_base}.{index}")),
                        unit,
                    )
                )
        onu_entities = await self._walk_entities("onu_identifier")
        onu_metrics = {
            "onu_rx_power": ("rx_optical_power", "dBm"),
            "onu_tx_power": ("tx_optical_power", "dBm"),
            "onu_temperature": ("temperature", "celsius"),
            "onu_voltage": ("voltage", "volts"),
            "onu_status": ("online_state", "state"),
            "onu_distance": ("distance", "meters"),
        }
        for suffix, entity_id in onu_entities:
            for oid_key, (metric, unit) in onu_metrics.items():
                oid_base = self.oids.get(oid_key)
                if oid_base is None:
                    continue
                raw_value = await self._query_oid(f"{oid_base}.{suffix}")
                value = (
                    _online_state(raw_value)
                    if oid_key == "onu_status"
                    else _float(raw_value)
                )
                readings.append(
                    OpticalMetric(
                        self.device_id,
                        f"onu:{suffix}",
                        metric,
                        value,
                        unit,
                        entity_type="ONU",
                        entity_id=entity_id,
                    )
                )
        return readings

    async def collect_subscriber_sessions(self) -> list[dict[str, object]]:
        subscriber_entities = await self._walk_entities("subscriber_identifier")
        if subscriber_entities:
            metric_oids = {
                "session_state": "subscriber_session_state",
                "session_uptime": "subscriber_session_uptime",
                "download_rate": "subscriber_download_rate",
                "upload_rate": "subscriber_upload_rate",
                "disconnect_events": "subscriber_disconnect_events",
            }
            sessions: list[dict[str, object]] = []
            for suffix, entity_id in subscriber_entities:
                session: dict[str, object] = {"subscriber_id": entity_id}
                for metric, oid_key in metric_oids.items():
                    oid_base = self.oids.get(oid_key)
                    if oid_base is not None:
                        session[metric] = _int(
                            await self._query_oid(f"{oid_base}.{suffix}")
                        )
                sessions.append(session)
            return sessions
        oid = self.oids.get("subscriber_sessions")
        if oid is None:
            return []
        return [
            {
                "device_id": str(self.device_id),
                "active_sessions": _int(await self._query_oid(oid)),
            }
        ]

    async def _walk_entities(self, oid_key: str) -> list[tuple[str, str]]:
        oid_base = self.oids.get(oid_key)
        if oid_base is None or self._walk is None:
            return []
        rows = await self._walk(oid_base)
        return [
            (oid.removeprefix(f"{oid_base}."), str(value))
            for oid, value in rows
            if oid.startswith(f"{oid_base}.")
        ]

    async def _required_query(self, metric: str, default_oid: str) -> object | None:
        return await self._query_oid(self.oids.get(metric, default_oid))

    async def _memory_percent(self) -> float | None:
        override = self.oids.get("memory")
        if override is not None:
            return _float(await self._query_oid(override))
        total = _float(await self._query_oid("1.3.6.1.4.1.2021.4.5.0"))
        available = _float(await self._query_oid("1.3.6.1.4.1.2021.4.6.0"))
        if total is None or available is None or total <= 0:
            return None
        return max(0.0, min(100.0, ((total - available) / total) * 100))

    async def _query_oid(self, oid: str) -> object | None:
        if self._query is None:
            raise CollectorConfigurationError("SNMP transport is not configured.")
        return await self._query(oid)


def _int(value: object | None) -> int | None:
    try:
        return int(str(value)) if value is not None else None
    except (TypeError, ValueError):
        return None


def _float(value: object | None) -> float | None:
    try:
        return float(str(value)) if value is not None else None
    except (TypeError, ValueError):
        return None


def _sum_optional(*values: object | None) -> int | None:
    parsed = [_int(value) for value in values]
    present = [value for value in parsed if value is not None]
    return sum(present) if present else None


def _interface_status(value: object | None) -> str | None:
    parsed = _int(value)
    if parsed is None:
        return None
    return {1: "UP", 2: "DOWN", 3: "TESTING"}.get(parsed, "UNKNOWN")


def _online_state(value: object | None) -> float | None:
    parsed = _int(value)
    if parsed is not None:
        return 1.0 if parsed == 1 else 0.0
    normalized = str(value).strip().casefold() if value is not None else ""
    if normalized in {"online", "up", "active"}:
        return 1.0
    if normalized in {"offline", "down", "inactive"}:
        return 0.0
    return None


def _timeticks_seconds(value: object | None) -> int | None:
    ticks = _int(value)
    return ticks // 100 if ticks is not None else None
