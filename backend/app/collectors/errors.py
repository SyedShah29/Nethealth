class CollectorError(Exception):
    """Base error for a failed collector operation."""


class CollectorConfigurationError(CollectorError):
    """Collector configuration is incomplete or invalid."""


class CollectorTransportError(CollectorError):
    """The configured transport could not complete a read-only request."""
