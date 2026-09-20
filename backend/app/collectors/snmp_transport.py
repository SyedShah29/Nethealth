# ruff: noqa
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from app.collectors.errors import CollectorTransportError
from app.collectors.snmp import SnmpProfile

@dataclass(frozen=True, slots=True)
class SnmpUdpTransport:
    host: str
    profile: SnmpProfile
    port: int = 161
    timeout_seconds: float = 2.0
    retries: int = 1

    async def query(self, oid: str) -> Any | None:
        try:
            from pysnmp.hlapi.v3arch.asyncio import (  # type: ignore[import-not-found]
                CommunityData, ContextData, ObjectIdentity, ObjectType, SnmpEngine,
                UdpTransportTarget, UsmUserData, get_cmd,
            )
            if self.profile.version == "3":
                auth = UsmUserData(self.profile.username, self.profile.auth_secret or "", self.profile.privacy_secret)
            else:
                auth = CommunityData(self.profile.username)
            target = await UdpTransportTarget.create((self.host, self.port), timeout=self.timeout_seconds, retries=self.retries)
            indication, status, _, bindings = await get_cmd(SnmpEngine(), auth, target, ContextData(), ObjectType(ObjectIdentity(oid)))
            if indication or status: raise CollectorTransportError("SNMP request failed.")
            return bindings[0][1] if bindings else None
        except CollectorTransportError:
            raise
        except Exception as exc:
            raise CollectorTransportError("SNMP transport failed.") from exc

    async def walk(self, oid: str) -> list[tuple[str, object]]:
        """Walk a table subtree, returning OID/value pairs."""
        try:
            from pysnmp.hlapi.v3arch.asyncio import (
                CommunityData, ContextData, ObjectIdentity, ObjectType, SnmpEngine,
                UdpTransportTarget, UsmUserData, walk_cmd,
            )
            auth = UsmUserData(self.profile.username, self.profile.auth_secret or "", self.profile.privacy_secret) if self.profile.version == "3" else CommunityData(self.profile.username)
            target = await UdpTransportTarget.create((self.host, self.port), timeout=self.timeout_seconds, retries=self.retries)
            values: list[tuple[str, object]] = []
            async for indication, status, _, bindings in walk_cmd(SnmpEngine(), auth, target, ContextData(), ObjectType(ObjectIdentity(oid)), lexicographicMode=False):
                if indication or status: raise CollectorTransportError("SNMP table walk failed.")
                values.extend((str(name), value) for name, value in bindings)
            return values
        except CollectorTransportError:
            raise
        except Exception as exc:
            raise CollectorTransportError("SNMP table walk failed.") from exc
