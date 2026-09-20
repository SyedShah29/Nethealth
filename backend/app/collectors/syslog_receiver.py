import asyncio
from collections.abc import Callable

from app.collectors.schemas import SyslogEvent
from app.collectors.syslog import normalize_syslog


class SyslogReceiver(asyncio.DatagramProtocol):
    def __init__(self, on_event: Callable[[SyslogEvent], None]) -> None:
        self.on_event = on_event

    def datagram_received(self, data: bytes, address: tuple[str, int]) -> None:
        self.on_event(
            normalize_syslog(
                data.decode("utf-8", errors="replace"),
                address[0],
            )
        )


async def serve_syslog(
    host: str,
    port: int,
    on_event: Callable[[SyslogEvent], None],
) -> asyncio.DatagramTransport:
    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: SyslogReceiver(on_event),
        local_addr=(host, port),
    )
    return transport
