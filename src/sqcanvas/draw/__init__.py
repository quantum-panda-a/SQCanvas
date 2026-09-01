"""Shapely-based geometry primitives (the drawing verbs of SQCanvas)."""

from shapely.geometry import LineString, Point, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from sqcanvas.draw import basic, mpl
from sqcanvas.draw.basic import (
    _iter_func_geom_,
    arc,
    buffer,
    circle,
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
    "arc",
    "basic",
    "buffer",
    "circle",
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
