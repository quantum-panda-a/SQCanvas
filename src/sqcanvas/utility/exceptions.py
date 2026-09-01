"""Exception types raised by SQCanvas."""


class SQCanvasError(Exception):
    """Base class for all errors raised intentionally by SQCanvas."""


class DimensionError(SQCanvasError, ValueError):
    """Raised when a dimension string cannot be parsed into micrometres."""


class ExportError(SQCanvasError, RuntimeError):
    """Raised when an exporter cannot produce an artifact."""
