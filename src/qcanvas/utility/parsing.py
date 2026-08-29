"""Small parsing helpers for options that arrive as strings."""

from __future__ import annotations

from typing import Any

from qcanvas.utility.attr_dict import AttrDict
from qcanvas.utility.units import parse_dimension


def is_true(value: Any) -> bool:
    """Return ``True`` for common truthy string representations."""
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on", "y", "t"}


def parse_value(value: Any) -> Any:
    """Coerce an option to a Python value.

    Strings that look like dimensions are converted to micrometres (floats).
    Literal strings are returned as-is.
    """
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return value
        try:
            return parse_dimension(stripped)
        except Exception:  # noqa: BLE001 - fall through to a literal string
            return value
    return value


def walk_options(options: dict[str, Any]) -> AttrDict:
    """Recursively parse all dimension-looking values in an options mapping."""
    result = AttrDict()
    for key, value in options.items():
        if isinstance(value, dict):
            result[key] = walk_options(value)
        elif isinstance(value, (list, tuple)):
            result[key] = [walk_options(v) if isinstance(v, dict) else parse_value(v) for v in value]
        else:
            result[key] = parse_value(value)
    return result


def to_key_path(path: str) -> list[str]:
    """Split a dotted key path, e.g. ``"chip.size.size_x"`` -> a list of parts."""
    return [part for part in path.split(".") if part]


def get_path(options: Any, path: str, default: Any = None) -> Any:
    """Fetch a nested value from ``options`` by a dotted path."""
    node = options
    for part in to_key_path(path):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return default
    return node


def set_path(options: AttrDict, path: str, value: Any) -> None:
    """Set a nested value by a dotted path, creating intermediate nodes."""
    parts = to_key_path(path)
    node = options
    for part in parts[:-1]:
        node = node.setdefault(part, AttrDict())
    node[parts[-1]] = value
