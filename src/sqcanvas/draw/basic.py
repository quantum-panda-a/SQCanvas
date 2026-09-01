"""Shapely-based drawing primitives.

This module is the geometry "verbs" layer: it knows how to create and combine
shapes, but nothing about designs, components, or exporters. Coordinates are
plain floats in design units (micrometres).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import shapely.affinity
import shapely.ops
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry

from sqcanvas.utility.geom_utils import get_poly_pts


def rectangle(
    w: float,
    h: float,
    xoff: float = 0.0,
    yoff: float = 0.0,
    fillet: float = 0.0,
    quad_segs: int = 32,
) -> Polygon:
    """Create an axis-aligned rectangle of width ``w`` and height ``h`` with optional corner fillet.

    ``(xoff, yoff)`` is the rectangle centre.
    ``fillet`` is the corner rounding radius.
    ``quad_segs`` is the number of segments per quarter circle (default 32).
    Returns a shapely ``Polygon``.
    """
    if fillet <= 0.0:
        poly = shapely.geometry.box(-w / 2.0, -h / 2.0, w / 2.0, h / 2.0)
    else:
        r = min(float(fillet), w / 2.0, h / 2.0)
        inner = shapely.geometry.box(-w / 2.0 + r, -h / 2.0 + r, w / 2.0 - r, h / 2.0 - r)
        poly = inner.buffer(r, join_style=1, quad_segs=quad_segs)

    if xoff == 0.0 and yoff == 0.0:
        return poly
    return shapely.affinity.translate(poly, xoff=xoff, yoff=yoff)


def circle(
    radius: float,
    xoff: float = 0.0,
    yoff: float = 0.0,
    quad_segs: int = 32,
) -> Polygon:
    """Create a circle of given ``radius`` centred at ``(xoff, yoff)``."""
    return shapely.geometry.Point(float(xoff), float(yoff)).buffer(
        float(radius), quad_segs=quad_segs
    )


def arc(
    radius: float,
    width: float,
    start_angle: float,
    end_angle: float,
    xoff: float = 0.0,
    yoff: float = 0.0,
    fillet: float = 0.0,
    quad_segs: int = 32,
) -> Polygon:
    """Create an annular arc strip centered at ``(xoff, yoff)`` with optional corner fillet.

    ``radius`` is the center-line radius of the arc.
    ``width`` is the radial thickness of the arc strip.
    ``start_angle`` and ``end_angle`` are angles in degrees (CCW from positive x-axis).
    ``fillet`` is the corner rounding radius.
    ``quad_segs`` is the number of segments per quarter circle (default 32).
    """
    import math

    import numpy as np

    radius = float(radius)
    width = float(width)
    start_angle = float(start_angle)
    end_angle = float(end_angle)
    fillet = float(fillet)

    if fillet <= 0.0:
        r_in = max(0.0, radius - width / 2.0)
        r_out = radius + width / 2.0
        deg_diff = end_angle - start_angle
        num_pts = max(4, int(abs(deg_diff) / 90.0 * quad_segs) + 1)
        angles_rad = np.radians(np.linspace(start_angle, end_angle, num_pts))

        outer_x = float(xoff) + r_out * np.cos(angles_rad)
        outer_y = float(yoff) + r_out * np.sin(angles_rad)
        inner_x = float(xoff) + r_in * np.cos(angles_rad[::-1])
        inner_y = float(yoff) + r_in * np.sin(angles_rad[::-1])

        coords = list(zip(outer_x, outer_y, strict=False)) + list(zip(inner_x, inner_y, strict=False))
        return Polygon(coords)

    r = min(fillet, width / 2.0)
    d_theta = math.degrees(r / max(1e-6, radius))
    deg_span = end_angle - start_angle
    if 2.0 * d_theta >= deg_span:
        d_theta = deg_span / 2.0 - 1e-4

    if r >= width / 2.0 - 1e-6:
        deg_diff = end_angle - start_angle
        num_pts_line = max(4, int(abs(deg_diff) / 90.0 * quad_segs) + 1)
        angles_rad = np.radians(np.linspace(start_angle, end_angle, num_pts_line))
        line_x = float(xoff) + radius * np.cos(angles_rad)
        line_y = float(yoff) + radius * np.sin(angles_rad)
        line = shapely.geometry.LineString(list(zip(line_x, line_y, strict=False)))
        return line.buffer(width / 2.0, cap_style=1, quad_segs=quad_segs)

    inner_poly = arc(
        radius,
        width - 2.0 * r,
        start_angle + d_theta,
        end_angle - d_theta,
        xoff=xoff,
        yoff=yoff,
        fillet=0.0,
        quad_segs=quad_segs,
    )
    return inner_poly.buffer(r, join_style=1, quad_segs=quad_segs)



def translate(geom: BaseGeometry, x: float = 0.0, y: float = 0.0) -> BaseGeometry:
    """Translate a geometry by ``(x, y)``."""
    return shapely.affinity.translate(geom, xoff=float(x), yoff=float(y))


def rotate(geom: BaseGeometry, angle: float, origin: Any = (0.0, 0.0)) -> BaseGeometry:
    """Rotate a geometry by ``angle`` degrees counter-clockwise about ``origin`` (default: origin (0, 0))."""
    return shapely.affinity.rotate(geom, angle, origin=origin)


def scale(geom: BaseGeometry, x: float = 1.0, y: float = 1.0, origin: Any = "center") -> BaseGeometry:
    """Scale a geometry about ``origin`` by factors ``x`` and ``y``."""
    return shapely.affinity.scale(geom, xfact=float(x), yfact=float(y), origin=origin)


def subtract(geom: BaseGeometry, tool: BaseGeometry) -> BaseGeometry:
    """Carve ``tool`` out of ``geom`` (``geom - tool``)."""
    return geom.difference(tool)


def union(*polys: BaseGeometry) -> BaseGeometry:
    """Union two or more geometries into one."""
    if len(polys) == 1 and isinstance(polys[0], (list, tuple)):
        polys = tuple(polys[0])
    if not polys:
        raise ValueError("union() needs at least one geometry.")
    if len(polys) == 1:
        return polys[0]
    return shapely.ops.unary_union(polys)


def buffer(geom: BaseGeometry, distance: float, join_style: int = 1, cap_style: int = 2) -> BaseGeometry:
    """Buffer a geometry by ``distance`` (rounded joins, square caps by default)."""
    return geom.buffer(float(distance), join_style=join_style, cap_style=cap_style)


def flip_merge(line: BaseGeometry, xfact: float = -1, yfact: float = 1, origin: Any = (0, 0)) -> list[tuple[float, float]]:
    """Mirror a ``LineString`` across an axis and join it to its original.

    Returns a coordinate list suitable for building a closed polygon.
    """
    flipped = shapely.affinity.scale(line, xfact=float(xfact), yfact=float(yfact), origin=origin)
    return list(line.coords) + list(reversed(flipped.coords))


def is_rectangle(geom: BaseGeometry) -> bool:
    """Return ``True`` if ``geom`` is a four-vertex orthogonal polygon."""
    if not isinstance(geom, Polygon) or len(geom.exterior.coords) != 5:
        return False
    pts = get_poly_pts(geom)
    for i in range(4):
        v1 = pts[(i + 1) % 4] - pts[i % 4]
        v2 = pts[(i + 2) % 4] - pts[(i + 1) % 4]
        if abs(v1[0] * v2[0] + v1[1] * v2[1]) > 1e-9:
            return False
    return True


def _iter_func_geom_(func, objs: Any, *args: Any, overwrite: bool = False, **kwargs: Any) -> Any:
    """Apply a geometry function to every geometry inside ``objs``.

    Handles a single geometry, a dict of names -> geometries, or a list of
    geometries, mirroring the two common shapes the component layer produces.
    """
    if isinstance(objs, BaseGeometry):
        return func(objs, *args, **kwargs)
    if isinstance(objs, Mapping):
        result = {}
        for key, val in objs.items():
            result[key] = _iter_func_geom_(func, val, *args, overwrite=overwrite, **kwargs)
        return result
    if isinstance(objs, (list, tuple)):
        return [_iter_func_geom_(func, val, *args, overwrite=overwrite, **kwargs) for val in objs]
    return objs
