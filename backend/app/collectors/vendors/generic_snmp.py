# ruff: noqa
from app.collectors.snmp import SnmpCollector

class GenericSnmpAdapter(SnmpCollector):
    """Generic adapter boundary for standardized SNMP implementations."""
