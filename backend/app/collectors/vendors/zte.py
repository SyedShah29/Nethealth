# ruff: noqa
from app.collectors.snmp import SnmpCollector
class ZteAdapter(SnmpCollector):
    """ZTE normalization adapter; vendor OIDs remain isolated here."""
    vendor = "zte"
    oid_overrides = {"cpu": "1.3.6.1.4.1.3902.1.2.1.1.1.5.0", "memory": "1.3.6.1.4.1.3902.1.2.1.1.1.6.0", "temperature": "1.3.6.1.4.1.3902.1.2.1.1.1.7.0", "power": "1.3.6.1.4.1.3902.1.2.1.1.1.8.0", "fan": "1.3.6.1.4.1.3902.1.2.1.1.1.9.0", "rx_power": "1.3.6.1.4.1.3902.1082.500.10.2.3.2.1.5", "tx_power": "1.3.6.1.4.1.3902.1082.500.10.2.3.2.1.6"}
