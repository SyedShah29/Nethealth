from uuid import uuid4

import pytest
from pydantic import SecretStr

from app.collectors.errors import CollectorConfigurationError
from app.collectors.icmp import IcmpCollector
from app.collectors.runtime import build_collector
from app.collectors.vendors.cisco import CiscoAdapter
from app.core.config import Settings
from app.models.inventory import CollectorProfile, Device


def _settings(profile_json: str = "{}") -> Settings:
    return Settings(
        database_password=SecretStr("test-database-secret"),
        redis_password=SecretStr("test-redis-secret"),
        collector_profiles_json=SecretStr(profile_json),
    )


def _device(vendor: str | None = None) -> Device:
    return Device(
        id=uuid4(),
        name="edge",
        hostname="edge-1",
        management_ip="192.0.2.1",
        device_type="EDGE_ROUTER",
        site_id=uuid4(),
        vendor=vendor,
    )


def test_runtime_builds_icmp_collector_without_credentials() -> None:
    profile = CollectorProfile(name="icmp", collector_type="ICMP")
    collector = build_collector(_device(), profile, _settings())
    assert isinstance(collector, IcmpCollector)


def test_runtime_selects_vendor_adapter_from_secret_profile_configuration() -> None:
    profile = CollectorProfile(
        name="snmp",
        collector_type="SNMP",
        configuration_key="edge-v3",
    )
    settings = _settings(
        '{"edge-v3":{"version":"3","username":"monitor","auth_protocol":"SHA",'
        '"auth_secret":"not-a-real-secret","oid_overrides":{"cpu":"1.2.3"}}}'
    )
    collector = build_collector(_device("Cisco"), profile, settings)
    assert isinstance(collector, CiscoAdapter)
    assert collector.profile.username == "monitor"
    assert collector.oids["cpu"] == "1.2.3"


def test_runtime_rejects_missing_secret_profile_configuration() -> None:
    profile = CollectorProfile(
        name="snmp",
        collector_type="SNMP",
        configuration_key="missing",
    )
    with pytest.raises(CollectorConfigurationError):
        build_collector(_device(), profile, _settings())
