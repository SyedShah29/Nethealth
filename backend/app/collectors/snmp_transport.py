from dataclasses import dataclass
from typing import Any

from app.collectors.errors import CollectorConfigurationError, CollectorTransportError
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
            from pysnmp.hlapi.v3arch.asyncio import (
                ContextData,
                ObjectIdentity,
                ObjectType,
                SnmpEngine,
                UdpTransportTarget,
                get_cmd,
            )

            auth = _authentication(self.profile)
            target = await UdpTransportTarget.create(
                (self.host, self.port), timeout=self.timeout_seconds, retries=self.retries
            )
            indication, status, _, bindings = await get_cmd(
                SnmpEngine(), auth, target, ContextData(), ObjectType(ObjectIdentity(oid))
            )
            if indication or status:
                raise CollectorTransportError("SNMP request failed.")
            return bindings[0][1] if bindings else None
        except (CollectorConfigurationError, CollectorTransportError):
            raise
        except Exception as exc:
            raise CollectorTransportError("SNMP transport failed.") from exc

    async def walk(self, oid: str) -> list[tuple[str, object]]:
        try:
            from pysnmp.hlapi.v3arch.asyncio import (
                ContextData,
                ObjectIdentity,
                ObjectType,
                SnmpEngine,
                UdpTransportTarget,
                walk_cmd,
            )

            auth = _authentication(self.profile)
            target = await UdpTransportTarget.create(
                (self.host, self.port), timeout=self.timeout_seconds, retries=self.retries
            )
            values: list[tuple[str, object]] = []
            async for indication, status, _, bindings in walk_cmd(
                SnmpEngine(),
                auth,
                target,
                ContextData(),
                ObjectType(ObjectIdentity(oid)),
                lexicographicMode=False,
            ):
                if indication or status:
                    raise CollectorTransportError("SNMP table walk failed.")
                values.extend((str(name), value) for name, value in bindings)
            return values
        except (CollectorConfigurationError, CollectorTransportError):
            raise
        except Exception as exc:
            raise CollectorTransportError("SNMP table walk failed.") from exc


def _authentication(profile: SnmpProfile) -> Any:
    from pysnmp.hlapi.v3arch.asyncio import (
        CommunityData,
        UsmUserData,
        usmAesCfb128Protocol,
        usmDESPrivProtocol,
        usmHMACMD5AuthProtocol,
        usmHMACSHAAuthProtocol,
        usmNoAuthProtocol,
        usmNoPrivProtocol,
    )

    if profile.version == "2c":
        return CommunityData(profile.username)
    auth_protocols = {
        None: usmNoAuthProtocol,
        "NONE": usmNoAuthProtocol,
        "MD5": usmHMACMD5AuthProtocol,
        "SHA": usmHMACSHAAuthProtocol,
    }
    privacy_protocols = {
        None: usmNoPrivProtocol,
        "NONE": usmNoPrivProtocol,
        "DES": usmDESPrivProtocol,
        "AES": usmAesCfb128Protocol,
    }
    auth_key = profile.auth_protocol.upper() if profile.auth_protocol else None
    privacy_key = profile.privacy_protocol.upper() if profile.privacy_protocol else None
    if auth_key not in auth_protocols or privacy_key not in privacy_protocols:
        raise CollectorConfigurationError("Unsupported SNMP security protocol.")
    if auth_key not in {None, "NONE"} and not profile.auth_secret:
        raise CollectorConfigurationError("SNMP authentication secret is required.")
    if privacy_key not in {None, "NONE"} and not profile.privacy_secret:
        raise CollectorConfigurationError("SNMP privacy secret is required.")
    if privacy_key not in {None, "NONE"} and auth_key in {None, "NONE"}:
        raise CollectorConfigurationError("SNMP privacy requires authentication.")
    return UsmUserData(
        profile.username,
        profile.auth_secret,
        profile.privacy_secret,
        authProtocol=auth_protocols[auth_key],
        privProtocol=privacy_protocols[privacy_key],
    )
