"""A GDSII exporter — writes a ``.gds`` file using gdstk."""

from __future__ import annotations

from pathlib import Path

import gdstk
import numpy as np
from shapely.geometry import box

from qcanvas.draw import union
from qcanvas.exporters.base import Exporter

# Geometry is authored in micrometres; the GDS database unit is a micrometer.
_UM_TO_DB = 1.0


class GdsExporter(Exporter):
    """Export a design to a GDSII file.

    Positive shapes are written to their layer. When ``ground_plane`` is set,
    a chip-sized ground polygon is created and any ``subtract`` shapes are
    carved out of it before being written to the ground layer.
    """

    name = "gds"

    def export(
        self,
        design,
        *,
        filepath: str | Path = "qcanvas.gds",
        ground_plane: bool = False,
        ground_layer: int = 1,
        ground_datatype: int = 0,
    ) -> str:
        return export_gds(
            design,
            filepath=filepath,
            ground_plane=ground_plane,
            ground_layer=ground_layer,
            ground_datatype=ground_datatype,
        )


def export_gds(
    design,
    *,
    filepath: str | Path = "qcanvas.gds",
    ground_plane: bool = False,
    ground_layer: int = 1,
    ground_datatype: int = 0,
) -> str:
    """Serialize ``design`` to a GDSII file and return the resolved path."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    library = gdstk.Library(unit=1.0e-6, precision=1.0e-6)
    top = library.new_cell(design.name or "TOP")
    records = design.shapes.as_records()

    subtracts = [r.geometry for r in records if r.subtract and not r.geometry.is_empty]
    ground_records = [r.geometry for r in records if r.label == "ground" and not r.subtract and not r.geometry.is_empty]
    other_records = [
        r
        for r in records
        if not r.helper and not r.subtract and r.label != "ground" and not r.geometry.is_empty
    ]

    if ground_plane and hasattr(design, "chip_extent"):
        cx, cy = design.chip_centre()
        w, h = design.chip_extent()
        chip_box = box(cx - w / 2.0, cy - h / 2.0, cx + w / 2.0, cy + h / 2.0)
        ground_geoms = [chip_box] + ground_records
        ground = union(*ground_geoms)
        if subtracts:
            ground = ground.difference(union(*subtracts))
        if not ground.is_empty:
            _add_geometry(top, ground, layer=ground_layer, datatype=ground_datatype, width=None)
    elif ground_records:
        ground = union(*ground_records)
        if subtracts:
            ground = ground.difference(union(*subtracts))
        if not ground.is_empty:
            _add_geometry(top, ground, layer=ground_layer, datatype=ground_datatype, width=None)

    for record in other_records:
        _add_geometry(top, record.geometry, layer=record.layer, datatype=0, width=record.width)

    # Junk-free export: use the parent directory as workdir so relative paths resolve.
    library.write_gds(str(filepath))
    return str(filepath)


def _add_geometry(top, geom, *, layer: int, datatype: int, width: float | None) -> None:
    kind = geom.geom_type
    if kind == "Polygon":
        _add_polygon(top, geom, layer=layer, datatype=datatype)
    elif kind == "MultiPolygon":
        for poly in geom.geoms:
            _add_polygon(top, poly, layer=layer, datatype=datatype)
    elif kind == "LineString" and width:
        top.add(gdstk.FlexPath(_um_to_db(geom.coords), width * _UM_TO_DB, layer=layer, datatype=datatype))


def _add_polygon(top, geom, *, layer: int, datatype: int) -> None:
    """Add a shapely polygon to a GDS cell, carving out any interior holes via boolean difference."""
    if geom.is_empty:
        return
    exterior_coords = _um_to_db(geom.exterior.coords)
    if not geom.interiors:
        top.add(gdstk.Polygon(exterior_coords, layer=layer, datatype=datatype))
    else:
        outer = gdstk.Polygon(exterior_coords)
        inners = [gdstk.Polygon(_um_to_db(interior.coords)) for interior in geom.interiors]
        result = gdstk.boolean([outer], inners, "not", layer=layer, datatype=datatype)
        for poly in result:
            top.add(poly)


def _um_to_db(coords) -> np.ndarray:
    return np.asarray(list(coords), dtype=float) * _UM_TO_DB
