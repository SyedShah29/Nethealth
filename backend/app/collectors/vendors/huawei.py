# ruff: noqa
from app.collectors.snmp import SnmpCollector
class HuaweiAdapter(SnmpCollector):
    """Huawei normalization adapter; vendor OIDs remain isolated here."""
    vendor = "huawei"
    oid_overrides = {"cpu": "1.3.6.1.4.1.2011.6.3.1.1.4.0", "memory": "1.3.6.1.4.1.2011.6.3.1.1.5.0", "temperature": "1.3.6.1.4.1.2011.6.3.1.1.6.0", "power": "1.3.6.1.4.1.2011.6.3.1.1.7.0", "fan": "1.3.6.1.4.1.2011.6.3.1.1.8.0", "subscriber_sessions": "1.3.6.1.4.1.2011.6.3.1.1.9.0", "rx_power": "1.3.6.1.4.1.2011.6.145.1.1.1.2.11.4", "tx_power": "1.3.6.1.4.1.2011.6.145.1.1.1.2.11.5"}
