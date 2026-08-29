"""Shapely-based geometry primitives (the drawing verbs of QCanvas)."""

from shapely.geometry import LineString, Point, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from qcanvas.draw import basic, mpl
from qcanvas.draw.basic import (
    _iter_func_geom_,
    buffer,
    flip_merge,
    is_rectangle,
    rectangle,
    rotate,
    scale,
    subtract,
    translate,
    union,
)

__all__ = [
    "BaseGeometry",
    "LineString",
    "Point",
    "Polygon",
    "_iter_func_geom_",
    "basic",
    "buffer",
    "flip_merge",
    "is_rectangle",
    "mpl",
    "rectangle",
    "rotate",
    "scale",
    "subtract",
    "translate",
    "unary_union",
    "union",
]
