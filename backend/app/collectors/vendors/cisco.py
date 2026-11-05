# ruff: noqa
from app.collectors.snmp import SnmpCollector


class CiscoAdapter(SnmpCollector):
    """Cisco normalization adapter; vendor OIDs remain isolated here."""

    vendor = "cisco"
    oid_overrides = {
        "cpu": "1.3.6.1.4.1.9.2.1.57.0",
        "memory": "1.3.6.1.4.1.9.1.1.0",
        "temperature": "1.3.6.1.4.1.9.9.13.1.3.1.3.1",
        "power": "1.3.6.1.4.1.9.9.117.1.3.1.1.4.1",
        "fan": "1.3.6.1.4.1.9.9.13.1.5.1.3.1",
        "subscriber_sessions": "1.3.6.1.4.1.9.9.150.1.1.3.0",
        "rx_power": "1.3.6.1.4.1.9.9.706.1.2.1.1.6",
        "tx_power": "1.3.6.1.4.1.9.9.706.1.2.1.1.8",
    }
