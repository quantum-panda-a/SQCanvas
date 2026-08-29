"""Figure helpers for matplotlib users.

These functions are intentionally free of any design knowledge: they draw a
list of shape records (as produced by :class:`qcanvas.shapes.ShapeStore`)
onto a matplotlib axes. The exporter layer composes them with the store.
"""

from __future__ import annotations

from collections.abc import Iterable

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from shapely.geometry import Polygon


def figure_spawn(figsize: tuple[float, float] = (8.0, 8.0)) -> tuple[Figure, Axes]:
    """Create a fresh matplotlib figure/axes pair."""
    fig, ax = plt.subplots(figsize=figsize)
    return fig, ax


def draw_records(
    ax: Axes,
    records: Iterable[dict],
    *,
    styles: dict | None = None,
    outline: bool = True,
    chip_outline: list[tuple[float, float]] | None = None,
) -> None:
    """Plot a sequence of shape records onto ``ax``.

    A record must be a dict with keys ``geometry`` (a shapely geometry) and
    optional ``subtract``, ``label``, and ``layer``. ``subtract=True`` shapes
    are drawn as outlines to indicate a carve-out.
    """
    styles = styles or {}
    for record in records:
        geom = record.get("geometry")
        if geom is None or geom.is_empty:
            continue
        subtract = bool(record.get("subtract", False))
        label = record.get("label", "")
        style = styles.get(label, {})
        if subtract:
            _plot_geom(ax, geom, facecolor="none", edgecolor="0.45", lw=0.7, linestyle="--")
            continue
        facecolor = style.get("facecolor", "0.15")
        edgecolor = style.get("edgecolor", "0.0")
        _plot_geom(ax, geom, facecolor=facecolor, edgecolor=edgecolor, lw=0.4)

    if outline:
        ax.set_aspect("equal", adjustable="box")
        ax.set_anchor("C")
    if chip_outline:
        xs = [p[0] for p in chip_outline]
        ys = [p[1] for p in chip_outline]
        ax.plot(xs, ys, color="0.35", lw=0.8, linestyle=":")


def _polygon_to_patch(poly: Polygon, **kwargs: object) -> PathPatch:
    vertices = list(poly.exterior.coords)
    codes = [Path.MOVETO] + [Path.LINETO] * (len(vertices) - 2) + [Path.CLOSEPOLY]
    for interior in poly.interiors:
        i_verts = list(interior.coords)
        vertices.extend(i_verts)
        codes.extend([Path.MOVETO] + [Path.LINETO] * (len(i_verts) - 2) + [Path.CLOSEPOLY])
    path = Path(vertices, codes)
    return PathPatch(path, **kwargs)


def _plot_geom(ax: Axes, geom, **patch_kwargs: object) -> None:
    if geom.geom_type == "Polygon":
        if not geom.is_empty:
            ax.add_patch(_polygon_to_patch(geom, **patch_kwargs))
    elif geom.geom_type == "MultiPolygon":
        for poly in geom.geoms:
            if not poly.is_empty:
                ax.add_patch(_polygon_to_patch(poly, **patch_kwargs))
    elif geom.geom_type in ("LineString", "LinearRing"):
        try:
            from matplotlib.collections import LineCollection

            coords = list(geom.coords)
            ax.add_collection(LineCollection([coords], colors=patch_kwargs.get("edgecolor", "0.0")))
        except Exception:  # noqa: BLE001
            return
    elif geom.geom_type == "MultiLineString":
        try:
            from matplotlib.collections import LineCollection

            lines = [list(line.coords) for line in geom.geoms]
            ax.add_collection(LineCollection(lines, colors=patch_kwargs.get("edgecolor", "0.0")))
        except Exception:  # noqa: BLE001
            return
