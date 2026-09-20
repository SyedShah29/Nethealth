# ruff: noqa
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
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

SnmpQuery = Callable[[str], Awaitable[object | None]]
SnmpWalk = Callable[[str], Awaitable[list[tuple[str, object]]]]

class SnmpCollector(DeviceCollector):
    collector_type = "SNMP"
    oid_overrides: dict[str, str] = {}
    def __init__(self, device_id: UUID, profile: SnmpProfile, query: SnmpQuery | None = None, interface_indexes: list[tuple[int, str]] | None = None, walk: SnmpWalk | None = None) -> None:
        super().__init__(device_id); self.profile = profile
        if profile.version not in {"2c", "3"}: raise CollectorConfigurationError("Unsupported SNMP version.")
        if profile.version == "3" and not profile.username: raise CollectorConfigurationError("SNMPv3 username is required.")
        self._query = query
        self.interface_indexes = interface_indexes or []
        self._walk = walk

    async def test_connection(self) -> bool:
        if self._query is None: raise CollectorConfigurationError("SNMP transport is not configured.")
        return await self._query("1.3.6.1.2.1.1.3.0") is not None

    async def collect_device_health(self) -> DeviceHealth:
        if self._query is None: raise CollectorConfigurationError("SNMP transport is not configured.")
        uptime = await self._query("1.3.6.1.2.1.1.3.0")
        uptime_seconds = int(uptime) if isinstance(uptime, (int, float, str)) else None
        return DeviceHealth(self.device_id, uptime is not None, None, None, uptime_seconds)

    async def collect_interfaces(self) -> list[InterfaceHealth]:
        if self._query is None: raise CollectorConfigurationError("SNMP transport is not configured.")
        results: list[InterfaceHealth] = []
        if self._walk is not None:
            rows = await self._walk("1.3.6.1.2.1.2.2.1.2")
            self.interface_indexes = [(int(oid.rsplit(".", 1)[-1]), str(value)) for oid, value in rows]
        for index, name in self.interface_indexes:
            in_octets = await self._query(f"1.3.6.1.2.1.2.2.1.10.{index}")
            out_octets = await self._query(f"1.3.6.1.2.1.2.2.1.16.{index}")
            errors = await self._query(f"1.3.6.1.2.1.2.2.1.14.{index}")
            discards = await self._query(f"1.3.6.1.2.1.2.2.1.19.{index}")
            results.append(InterfaceHealth(self.device_id, name, None, None, _int(in_octets), _int(out_octets), _int(errors), _int(discards)))
        return results

    async def collect_environment(self) -> list[EnvironmentReading]:
        if self._query is None: raise CollectorConfigurationError("SNMP transport is not configured.")
        readings: list[EnvironmentReading] = []
        defaults: list[tuple[str, str, str]] = [("cpu", "1.3.6.1.4.1.2021.11.9.0", "%"), ("memory", "1.3.6.1.4.1.2021.4.6.0", "bytes"), ("temperature", "1.3.6.1.4.1.2021.13.16.5.1.2.1", "celsius")]
        defaults += (("power", "1.3.6.1.4.1.2021.13.15.1.1.2.1", "watts"), ("fan", "1.3.6.1.4.1.2021.13.16.5.1.2.1", "rpm"))
        for metric, oid, unit in defaults:
            oid = self.oid_overrides.get(metric, oid)
            value = await self._query(oid)
            readings.append(EnvironmentReading(self.device_id, metric, _float(value), unit))
        return readings

    async def collect_optical_metrics(self) -> list[OpticalMetric]:
        if self._query is None: raise CollectorConfigurationError("SNMP transport is not configured.")
        readings: list[OpticalMetric] = []
        for index, name in self.interface_indexes:
            for metric, suffix, unit in (("rx_power", "1.3.6.1.2.1.2.2.1.10", "dBm"), ("tx_power", "1.3.6.1.2.1.2.2.1.16", "dBm")):
                value = await self._query(f"{suffix}.{index}")
                readings.append(OpticalMetric(self.device_id, name, metric, _float(value), unit))
        return readings

    async def collect_subscriber_sessions(self) -> list[dict[str, object]]:
        if self._query is None: raise CollectorConfigurationError("SNMP transport is not configured.")
        value = await self._query(self.oid_overrides.get("subscriber_sessions", "1.3.6.1.2.1.2.1.0"))
        return [{"device_id": str(self.device_id), "active_sessions": _int(value)}]

def _int(value: object | None) -> int | None:
    try: return int(str(value)) if value is not None else None
    except (TypeError, ValueError): return None

def _float(value: object | None) -> float | None:
    try: return float(str(value)) if value is not None else None
    except (TypeError, ValueError): return None
