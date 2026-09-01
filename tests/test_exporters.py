import os
import tempfile

import matplotlib.pyplot as plt
import pytest
from matplotlib.figure import Figure
from shapely.geometry import LineString, MultiPolygon, Polygon

from sqcanvas.components.qubits import DualPadTransmon
from sqcanvas.config import PRESET_THEMES
from sqcanvas.designs.design_planar import PlanarDesign
from sqcanvas.exporters.base import Exporter
from sqcanvas.exporters.gds import GdsExporter, export_gds
from sqcanvas.exporters.mpl import MatplotlibExporter, export_scene


def test_exporter_registry():
    assert "mpl" in Exporter.names()
    assert "gds" in Exporter.names()
    assert Exporter.for_name("mpl") is MatplotlibExporter
    assert Exporter.for_name("gds") is GdsExporter

    with pytest.raises(KeyError):
        Exporter.for_name("non_existent")

    exp = MatplotlibExporter()
    assert "MatplotlibExporter" in repr(exp)


def test_matplotlib_exporter():
    design = PlanarDesign()
    DualPadTransmon(design, "Q1", options={"pos_x": "-1mm"})
    DualPadTransmon(design, "Q2", options={"pos_x": "1mm"})

    fig = design.export("mpl")
    assert isinstance(fig, Figure)
    plt.close(fig)

    # Export with specific components and layers
    fig2 = export_scene(
        design,
        components=["Q1"],
        layers=[1],
        chip_outline=True,
        title="Custom Scene",
    )
    assert isinstance(fig2, Figure)
    plt.close(fig2)


def test_matplotlib_exporter_preset_themes():
    design = PlanarDesign()
    DualPadTransmon(design, "Q1")

    all_themes = ["cyber", "nordic", "aurora", "paper", "no002", "no005", "no008", "no009", "no013"]
    for theme_key in all_themes:
        fig = design.export("mpl", theme=theme_key, title=f"Theme: {theme_key}")
        assert isinstance(fig, Figure)
        assert fig.get_facecolor() is not None
        plt.close(fig)


def test_gds_exporter_positive_and_ground_plane():
    design = PlanarDesign()
    DualPadTransmon(design, "Q1", options={"pos_x": "0mm", "pos_y": "0mm"})

    # Add multipolygon and linestring with width
    p1 = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    p2 = Polygon([(200, 200), (300, 200), (300, 300), (200, 300)])
    multi_poly = MultiPolygon([p1, p2])
    design.add_shape("custom", "multi", multi_poly, layer=2)

    line = LineString([(0, 0), (500, 500)])
    design.add_shape("custom", "wire", line, layer=3, kind="path", width=10.0)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Standard export without ground plane
        out1 = os.path.join(tmpdir, "test1.gds")
        path1 = design.export("gds", filepath=out1, ground_plane=False)
        assert os.path.exists(path1)
        assert os.path.getsize(path1) > 0

        # Export with ground plane carving
        out2 = os.path.join(tmpdir, "test2.gds")
        path2 = export_gds(design, filepath=out2, ground_plane=True, ground_layer=1)
        assert os.path.exists(path2)
        assert os.path.getsize(path2) > 0

        # Verify ground plane polygon has hole cutlines (num vertices > 5)
        import gdstk
        lib = gdstk.read_gds(path2)
        cell = lib.top_level()[0]
        layer1_polys = [p for p in cell.polygons if p.layer == 1]
        assert len(layer1_polys) >= 1
        assert any(len(p.points) > 5 for p in layer1_polys)


def test_overlapping_ground_guards():
    design = PlanarDesign()
    DualPadTransmon(design, "Q1", options={"pos_x": "-400um", "pos_y": "0um", "ground_guard": "100um"})
    DualPadTransmon(
        design,
        "Q2",
        options={
            "pos_x": "400um",
            "pos_y": "0um",
            "orientation": "45",
            "ground_guard": "250um",
        },
    )

    # Matplotlib export test
    fig = design.export("mpl")
    assert isinstance(fig, Figure)
    plt.close(fig)

    # GDS export test without full chip ground plane
    with tempfile.TemporaryDirectory() as tmpdir:
        out = os.path.join(tmpdir, "overlap.gds")
        path = export_gds(design, filepath=out, ground_plane=False)
        assert os.path.exists(path)
        import gdstk

        lib = gdstk.read_gds(path)
        cell = lib.top_level()[0]
        ground_polys = [p for p in cell.polygons if p.layer == 1]
        assert len(ground_polys) >= 1
