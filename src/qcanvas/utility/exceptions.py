"""Exception types raised by QCanvas."""


class QCanvasError(Exception):
    """Base class for all errors raised intentionally by QCanvas."""


class DimensionError(QCanvasError, ValueError):
    """Raised when a dimension string cannot be parsed into micrometres."""


class ExportError(QCanvasError, RuntimeError):
    """Raised when an exporter cannot produce an artifact."""
