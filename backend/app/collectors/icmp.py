# ruff: noqa
from collections.abc import Awaitable, Callable
import asyncio
import re
from uuid import UUID
from app.collectors.base import DeviceCollector
from app.collectors.errors import CollectorTransportError
from app.collectors.schemas import DeviceHealth, InterfaceHealth

Probe = Callable[[str], Awaitable[float | None]]

async def system_probe(address: str, timeout_seconds: float = 2.0) -> float | None:
    """Run one platform ping and return latency; no command is run with shell expansion."""
    command = ["ping", "-n", "1", "-w", str(int(timeout_seconds * 1000)), address] if __import__("sys").platform == "win32" else ["ping", "-c", "1", "-W", str(max(1, int(timeout_seconds))), address]
    try:
        process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        output, _ = await asyncio.wait_for(process.communicate(), timeout_seconds + 1)
    except (OSError, asyncio.TimeoutError):
        return None
    if process.returncode != 0: return None
    match = re.search(rb"(?:time[=<]|Average = )\s*(\d+(?:\.\d+)?)", output, re.IGNORECASE)
    return float(match.group(1)) if match else 0.0

class IcmpCollector(DeviceCollector):
    collector_type = "ICMP"

    def __init__(self, device_id: UUID, management_ip: str, probe: Probe, attempts: int = 3) -> None:
        super().__init__(device_id); self.management_ip = management_ip; self._probe = probe
        if attempts < 1: raise ValueError("ICMP attempts must be positive.")
        self.attempts = attempts

    async def test_connection(self) -> bool:
        return await self._probe(self.management_ip) is not None

    async def collect_device_health(self) -> DeviceHealth:
        results = [await self._probe(self.management_ip) for _ in range(self.attempts)]
        successful = [value for value in results if value is not None]
        packet_loss = ((self.attempts - len(successful)) / self.attempts) * 100
        latency = sum(successful) / len(successful) if successful else None
        return DeviceHealth(self.device_id, bool(successful), latency, packet_loss)

    async def collect_interfaces(self) -> list[InterfaceHealth]:
        return []
