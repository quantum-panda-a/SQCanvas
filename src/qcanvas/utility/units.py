"""Physical dimension parsing and formatting.

QCanvas stores all geometry coordinates in **micrometres** as floats. This
module converts human-friendly strings like ``"455um"`` or ``"1mm"`` into those
floats and back, so no other module has to reason about unit prefixes.
"""

from __future__ import annotations

import re
from typing import Any

from qcanvas.utility.exceptions import DimensionError

# Conversion factor from each accepted unit to micrometres.
_TO_UM: dict[str, float] = {
    "nm": 1.0e-3,
    "um": 1.0,
    "\u03bcm": 1.0,  # greek mu
    "\u03bc": 1.0,
    "\u00b5m": 1.0,  # micro sign
    "\u00b5": 1.0,
    "micron": 1.0,
    "microns": 1.0,
    "mm": 1.0e3,
    "cm": 1.0e4,
    "m": 1.0e6,
}

_NUMBER_PATTERN = re.compile(
    r"^\s*([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s*([a-zA-Z\u00b5\u03bc()]*)\s*$"
)


def _normalise_unit(unit: str) -> str:
    return unit.lower().strip().replace("meters", "m").replace("meter", "m")


def parse_dimension(value: Any) -> float:
    """Parse a dimension into micrometres (float).

    Accepts either a plain number (treated as already in micrometres) or a
    length string such as ``"10um"``, ``"1 mm"``, or ``"2micron"``.

    Raises:
        DimensionError: if the string cannot be interpreted as a length.
    """
    if isinstance(value, bool):
        raise DimensionError(f"Cannot interpret boolean {value!r} as a dimension.")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, (list, tuple)) and value:
        return parse_dimension(value[0])
    if not isinstance(value, str):
        raise DimensionError(f"Cannot interpret {value!r} as a dimension.")

    match = _NUMBER_PATTERN.match(value)
    if not match:
        raise DimensionError(f"Could not parse dimension {value!r}.")

    number = float(match.group(1))
    unit = _normalise_unit(match.group(2))
    if not unit:
        return number
    factor = _TO_UM.get(unit)
    if factor is None:
        raise DimensionError(f"Unsupported unit {unit!r} in {value!r}.")
    return number * factor


def format_dimension(value: float, unit: str = "um", decimals: int = 4) -> str:
    """Format a float (in micrometres) as a dimension string with ``unit``."""
    factor = _TO_UM.get(_normalise_unit(unit))
    if factor is None:
        raise DimensionError(f"Unsupported unit {unit!r}.")
    scaled = float(value) / factor
    return f"{scaled:.{decimals}g}{unit}"
