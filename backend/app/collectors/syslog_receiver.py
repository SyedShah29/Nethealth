# ruff: noqa
import asyncio
from collections.abc import Callable
from app.collectors.schemas import SyslogEvent
from app.collectors.syslog import normalize_syslog

class SyslogReceiver(asyncio.DatagramProtocol):
    def __init__(self, device: str, on_event: Callable[[SyslogEvent], None]) -> None:
        self.device = device; self.on_event = on_event
    def datagram_received(self, data: bytes, _address: tuple[str, int]) -> None:
        self.on_event(normalize_syslog(data.decode("utf-8", errors="replace"), self.device))

async def serve_syslog(host: str, port: int, device: str, on_event: Callable[[SyslogEvent], None]) -> asyncio.DatagramTransport:
    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(lambda: SyslogReceiver(device, on_event), local_addr=(host, port))
    return transport
