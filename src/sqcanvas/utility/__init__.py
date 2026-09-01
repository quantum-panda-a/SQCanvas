"""Generic, dependency-light helpers used across SQCanvas."""

from sqcanvas.utility.attr_dict import AttrDict
from sqcanvas.utility.exceptions import DimensionError, ExportError, SQCanvasError
from sqcanvas.utility.geom_utils import Vector, get_poly_pts, round_coordinate_sequence
from sqcanvas.utility.parsing import get_path, is_true, parse_value, set_path, walk_options
from sqcanvas.utility.units import format_dimension, parse_dimension

__all__ = [
    "AttrDict",
    "DimensionError",
    "ExportError",
    "SQCanvasError",
    "Vector",
    "format_dimension",
    "get_path",
    "get_poly_pts",
    "is_true",
    "parse_dimension",
    "parse_value",
    "round_coordinate_sequence",
    "set_path",
    "walk_options",
]
