# ruff: noqa
from app.collectors.snmp import SnmpCollector
class MikrotikAdapter(SnmpCollector):
    """MikroTik normalization adapter; vendor OIDs remain isolated here."""
    vendor = "mikrotik"
    oid_overrides = {"cpu": "1.3.6.1.4.1.14988.1.1.3.10.0", "memory": "1.3.6.1.4.1.14988.1.1.3.8.0", "temperature": "1.3.6.1.4.1.14988.1.1.3.6.0", "power": "1.3.6.1.4.1.14988.1.1.3.12.0", "fan": "1.3.6.1.4.1.14988.1.1.3.13.0"}
