"""Unit tests for newly added SQCanvas components:
- CircularTransmon
- ChargeTee, ChargeClaw, ChargeArc, ReadTee
- Launchpad, CPWOpen, CPWShort
- Text
- PackagingMarker
"""

import pytest

from sqcanvas.components import (
    ChargeArc,
    ChargeClaw,
    ChargeTee,
    CircularTransmon,
    CPWOpen,
    CPWShort,
    Launchpad,
    PackagingMarker,
    ReadTee,
    Text,
)
from sqcanvas.designs.design_planar import PlanarDesign


# ==============================================================================
# 1. CircularTransmon Tests
# ==============================================================================
def test_circular_transmon_defaults():
    design = PlanarDesign()
    q = CircularTransmon(design, "Q_circ")
    assert q.options.pad_radius == 150.0
    assert q.options.gap == 35.0
    assert q.options.inductor_width == 20.0
    assert q.options.ground_guard == 30.0

    records = design.shapes.by_component("Q_circ")
    # ground, cutout, metal, junction
    assert len(records) == 4

    metal_rec = next(r for r in records if r.label == "metal")
    assert metal_rec.subtract is False
    assert metal_rec.geometry.centroid.x == pytest.approx(0.0)
    assert metal_rec.geometry.centroid.y == pytest.approx(0.0)
    assert metal_rec.geometry.bounds[0] == pytest.approx(-150.0, rel=1e-2)
    assert metal_rec.geometry.bounds[2] == pytest.approx(150.0, rel=1e-2)

    cutout_rec = next(r for r in records if r.label == "cutout")
    assert cutout_rec.subtract is True
    # cutout radius = 150 + 35 = 185
    assert cutout_rec.geometry.bounds[0] == pytest.approx(-185.0, rel=1e-2)
    assert cutout_rec.geometry.bounds[2] == pytest.approx(185.0, rel=1e-2)

    junc_rec = next(r for r in records if r.label == "junction")
    assert junc_rec.subtract is False
    # junction in bottom gap: y in [-185, -150], x in [-10, 10]
    assert junc_rec.geometry.bounds == pytest.approx((-10.0, -185.0, 10.0, -150.0))
    assert junc_rec.geometry.centroid.x == pytest.approx(0.0)
    assert junc_rec.geometry.centroid.y == pytest.approx(-167.5)


def test_circular_transmon_rotation_and_guard_zero():
    design = PlanarDesign()
    CircularTransmon(
        design,
        "Q_circ_rot",
        options={
            "pos_x": "500um",
            "pos_y": "300um",
            "orientation": "90",
            "pad_radius": "100um",
            "gap": "30um",
            "inductor_width": "10um",
            "ground_guard": "0um",
        },
    )
    records = design.shapes.by_component("Q_circ_rot")
    assert len(records) == 3  # cutout, metal, junction (no ground)

    metal_rec = next(r for r in records if r.label == "metal")
    assert metal_rec.geometry.centroid.x == pytest.approx(500.0)
    assert metal_rec.geometry.centroid.y == pytest.approx(300.0)

    # Local unrotated junction at (0, -115) -> rotated 90 deg CCW: (115, 0) -> placed at (615, 300)
    junc_rec = next(r for r in records if r.label == "junction")
    assert junc_rec.geometry.centroid.x == pytest.approx(615.0)
    assert junc_rec.geometry.centroid.y == pytest.approx(300.0)


# ==============================================================================
# 2. Coupler Tests (ChargeTee, ChargeClaw, ChargeArc, ReadTee)
# ==============================================================================
def test_charge_tee():
    design = PlanarDesign()
    ChargeTee(
        design,
        "T1",
        options={
            "pos_x": "100um",
            "pos_y": "200um",
            "orientation": "0",
            "trace_width": "10um",
            "trace_gap": "6um",
            "lead_length": "40um",
            "tee_width": "80um",
            "tee_height": "20um",
            "tee_gap": "10um",
        },
    )
    records = design.shapes.by_component("T1")
    assert len(records) == 3  # cutout, metal, ground

    cutout_rec = next(r for r in records if r.label == "cutout")
    metal_rec = next(r for r in records if r.label == "metal")
    ground_rec = next(r for r in records if r.label == "ground")

    # In local coords: port at (0, 0).
    # Shapes extend in -y direction from y=0 down to -lead_length - tee_height = -60.
    # Placed at (100, 200) -> x around 100, y from 140 to 200
    assert cutout_rec.subtract is True
    assert metal_rec.subtract is False
    assert ground_rec.subtract is False
    assert metal_rec.geometry.bounds[3] == pytest.approx(200.0)  # max y is port at 200
    assert metal_rec.geometry.bounds[1] == pytest.approx(140.0)  # min y is 200 - 60 = 140
    assert metal_rec.geometry.bounds[0] == pytest.approx(100.0 - 40.0)  # tee_width = 80
    assert metal_rec.geometry.bounds[2] == pytest.approx(100.0 + 40.0)

    # Test ground_guard=0um
    ChargeTee(design, "T2", options={"ground_guard": "0um"})
    records_t2 = design.shapes.by_component("T2")
    assert len(records_t2) == 2

    # Test tee_fillet and cutout_fillet
    ChargeTee(
        design,
        "T3",
        options={
            "pos_x": "0um",
            "pos_y": "0um",
            "tee_width": "100um",
            "tee_height": "30um",
            "tee_fillet": "5um",
            "cutout_fillet": "8um",
            "ground_guard": "30um",
        },
    )
    records_t3 = design.shapes.by_component("T3")
    metal_t3 = next(r for r in records_t3 if r.label == "metal")
    cutout_t3 = next(r for r in records_t3 if r.label == "cutout")
    ground_t3 = next(r for r in records_t3 if r.label == "ground")

    # Metal and cutout should have filleted vertices
    assert len(metal_t3.geometry.exterior.coords) > 10
    assert len(cutout_t3.geometry.exterior.coords) > 10
    # Ground shape has an unfilleted outer boundary (5 coords) and filleted inner hole
    assert len(ground_t3.geometry.exterior.coords) == 5
    assert len(ground_t3.geometry.interiors) == 1


def test_charge_claw():
    design = PlanarDesign()
    ChargeClaw(
        design,
        "C1",
        options={
            "pos_x": "0um",
            "pos_y": "0um",
            "lead_length": "50um",
            "claw_width": "100um",  # inner spacing
            "claw_length": "60um",
            "claw_width_trace": "10um",
        },
    )
    records = design.shapes.by_component("C1")
    assert len(records) == 3  # cutout, metal, ground
    metal_rec = next(r for r in records if r.label == "metal")

    # Metal: total outer width = 100 + 2*10 = 120 -> bounds in [-60, 60]
    # top at y=0, bottom at y = -50 - 10 - 60 = -120
    assert metal_rec.geometry.bounds[3] == pytest.approx(0.0)
    assert metal_rec.geometry.bounds[1] == pytest.approx(-120.0)
    assert metal_rec.geometry.bounds[0] == pytest.approx(-60.0)
    assert metal_rec.geometry.bounds[2] == pytest.approx(60.0)

    # Test ground_guard=0um
    ChargeClaw(design, "C2", options={"ground_guard": "0um"})
    assert len(design.shapes.by_component("C2")) == 2

    # Test claw_fillet and cutout_fillet with cutout_type=0
    ChargeClaw(
        design,
        "C3",
        options={
            "pos_x": "0um",
            "pos_y": "0um",
            "claw_width": "100um",
            "claw_length": "60um",
            "claw_width_trace": "10um",
            "claw_gap": "15um",
            "claw_fillet": "4um",
            "cutout_fillet": "5um",
            "cutout_type": 0,
        },
    )
    records_c3 = design.shapes.by_component("C3")
    metal_c3 = next(r for r in records_c3 if r.label == "metal")
    cutout_c3 = next(r for r in records_c3 if r.label == "cutout")
    assert len(metal_c3.geometry.exterior.coords) > 15
    assert len(cutout_c3.geometry.exterior.coords) > 15

    # Test cutout_type=1 (carving out the entire region between arms)
    ChargeClaw(
        design,
        "C4",
        options={
            "pos_x": "0um",
            "pos_y": "0um",
            "claw_width": "100um",
            "claw_length": "60um",
            "claw_width_trace": "10um",
            "claw_gap": "15um",
            "cutout_fillet": "5um",
            "cutout_type": 1,
        },
    )
    records_c4 = design.shapes.by_component("C4")
    cutout_c4 = next(r for r in records_c4 if r.label == "cutout")
    # cutout_type=1 carves out the area between the two arms, having larger area than cutout_type=0
    assert cutout_c4.geometry.area > cutout_c3.geometry.area
    # Both cutout_type=0 and cutout_type=1 have identical outer bounds including the upper gap
    assert cutout_c4.geometry.bounds == pytest.approx(cutout_c3.geometry.bounds)
    # For cutout_type=1, the point in the middle between arms (0, -80) is inside the cutout
    from shapely.geometry import Point
    assert cutout_c4.geometry.contains(Point(0.0, -80.0))


def test_charge_arc():
    design = PlanarDesign()
    ChargeArc(
        design,
        "A1",
        options={
            "pos_x": "0um",
            "pos_y": "0um",
            "lead_length": "50um",
            "arc_radius": "100um",
            "arc_width": "10um",
            "arc_angle": "90",
            "arc_gap": "15um",
            "arc_fillet": "2um",
            "cutout_fillet": "4um",
            "ground_guard": "30um",
        },
    )
    records = design.shapes.by_component("A1")
    assert len(records) == 3  # cutout, metal, ground
    metal_rec = next(r for r in records if r.label == "metal")
    cutout_rec = next(r for r in records if r.label == "cutout")
    ground_rec = next(r for r in records if r.label == "ground")

    # Top of lead touches y=0
    assert metal_rec.geometry.bounds[3] == pytest.approx(0.0)
    assert metal_rec.geometry.is_valid
    assert cutout_rec.geometry.is_valid
    assert ground_rec.geometry.is_valid

    # Cutout strictly contains metal and leaves gap at the ends
    assert cutout_rec.geometry.contains(metal_rec.geometry)
    # The cutout bounds in x should be wider than metal bounds by at least arc_gap
    assert cutout_rec.geometry.bounds[0] < metal_rec.geometry.bounds[0] - 10.0
    assert cutout_rec.geometry.bounds[2] > metal_rec.geometry.bounds[2] + 10.0

    # Ground outer boundary is sharp rectangle without fillet (5 coords)
    assert len(ground_rec.geometry.exterior.coords) == 5

    ChargeArc(design, "A2", options={"ground_guard": "0um"})
    assert len(design.shapes.by_component("A2")) == 2


def test_read_tee():
    design = PlanarDesign()
    rt = ReadTee(
        design,
        "RT1",
        options={
            "pos_x": "0um",
            "pos_y": "0um",
            "down_length": "50um",
            "second_width": "10um",
            "second_gap": "6um",
            "coupling_length": "100um",
            "prime_length": "200um",
            "ground_guard": "30um",
        },
    )
    assert "fillet" not in rt.default_options
    assert "open_termination" not in rt.default_options
    assert rt.default_options.turn_radius == "20um"

    records = design.shapes.by_component("RT1")
    assert len(records) == 3  # cutout, metal, ground
    metal_rec = next(r for r in records if r.label == "metal")
    cutout_rec = next(r for r in records if r.label == "cutout")
    ground_rec = next(r for r in records if r.label == "ground")

    # Resonator outlet is at (0, 0), secondary stub goes upward
    assert metal_rec.geometry.bounds[1] == pytest.approx(0.0)
    assert cutout_rec.geometry.bounds[1] == pytest.approx(0.0)
    assert metal_rec.geometry.is_valid
    assert cutout_rec.geometry.is_valid
    assert ground_rec.geometry.is_valid
    # The curved bend contains more than 10 coords across geometries
    geoms = metal_rec.geometry.geoms if hasattr(metal_rec.geometry, "geoms") else [metal_rec.geometry]
    assert sum(len(g.exterior.coords) for g in geoms) > 10

    # Ground outer is a sharp rectangular boundary (5 coords)
    assert len(ground_rec.geometry.exterior.coords) == 5

    # Test turn_radius = 0 (straight mitered corner)
    ReadTee(design, "RT2", options={"turn_radius": "0um", "ground_guard": "0um"})
    assert len(design.shapes.by_component("RT2")) == 2


# ==============================================================================
# 3. Ports Tests (Launchpad, CPWOpen, CPWShort)
# ==============================================================================
def test_launchpad():
    design = PlanarDesign()
    Launchpad(
        design,
        "LP1",
        options={
            "pos_x": "1000um",
            "pos_y": "500um",
            "trace_width": "10um",
            "lead_length": "20um",
            "taper_length": "100um",
            "pad_width": "120um",
            "pad_length": "150um",
            "pad_gap": "50um",
        },
    )
    records = design.shapes.by_component("LP1")
    assert len(records) == 3  # cutout, metal, ground
    metal_rec = next(r for r in records if r.label == "metal")

    # In local coords: port is at (0, 0), structure extends along -x to -(20 + 100 + 150) = -270
    # Placed at (1000, 500) -> max x is 1000, min x is 1000 - 270 = 730
    assert metal_rec.geometry.bounds[2] == pytest.approx(1000.0)
    assert metal_rec.geometry.bounds[0] == pytest.approx(730.0)
    assert metal_rec.geometry.bounds[1] == pytest.approx(500.0 - 60.0)
    assert metal_rec.geometry.bounds[3] == pytest.approx(500.0 + 60.0)

    Launchpad(design, "LP2", options={"ground_guard": "0um"})
    assert len(design.shapes.by_component("LP2")) == 2


def test_cpw_open_and_short():
    design = PlanarDesign()
    CPWOpen(
        design,
        "Open1",
        options={
            "pos_x": "0um",
            "pos_y": "0um",
            "width": "10um",
            "gap": "6um",
            "termination_gap": "8um",
        },
    )
    records_open = design.shapes.by_component("Open1")
    assert len(records_open) == 2  # cutout, ground
    assert records_open[0].subtract is False or records_open[1].subtract is False

    CPWOpen(design, "Open2", options={"ground_guard": "0um"})
    assert len(design.shapes.by_component("Open2")) == 1

    CPWShort(
        design,
        "Short1",
        options={
            "pos_x": "100um",
            "pos_y": "0um",
            "width": "10um",
        },
    )
    records_short = design.shapes.by_component("Short1")
    assert len(records_short) == 2  # metal, ground

    CPWShort(design, "Short2", options={"ground_guard": "0um"})
    assert len(design.shapes.by_component("Short2")) == 1


# ==============================================================================
# 4. Text Component Tests
# ==============================================================================
def test_text_component():
    design = PlanarDesign()
    Text(
        design,
        "Txt1",
        options={
            "pos_x": "0um",
            "pos_y": "0um",
            "text": "Q1",
            "size": "100um",
            "align_x": "center",
            "align_y": "center",
            "subtract": False,
        },
    )
    records = design.shapes.by_component("Txt1")
    assert len(records) == 1
    rec = records[0]
    assert rec.label == "metal"
    assert rec.subtract is False
    assert rec.geometry.is_valid
    # Center alignment puts centroid near (0, 0)
    assert rec.geometry.centroid.x == pytest.approx(0.0, abs=15.0)
    assert rec.geometry.centroid.y == pytest.approx(0.0, abs=15.0)

    # Subtracted text with ground_guard
    Text(
        design,
        "Txt2",
        options={"text": "CHIP_A", "subtract": True},
    )
    records_t2 = design.shapes.by_component("Txt2")
    assert len(records_t2) == 2  # ground, cutout
    cutout_rec = next(r for r in records_t2 if r.label == "cutout")
    assert cutout_rec.subtract is True

    # Subtracted text with ground_guard=0um
    Text(
        design,
        "Txt3",
        options={"text": "CHIP_B", "subtract": True, "ground_guard": "0um"},
    )
    assert len(design.shapes.by_component("Txt3")) == 1


# ==============================================================================
# 5. PackagingMarker Tests
# ==============================================================================
@pytest.mark.parametrize(
    "mtype", ["cross_box", "cross", "circle_cross", "corner_l", "square"]
)
def test_packaging_marker_types(mtype):
    design = PlanarDesign()
    PackagingMarker(
        design,
        f"M_{mtype}",
        options={
            "pos_x": "200um",
            "pos_y": "300um",
            "marker_type": mtype,
            "size": "150um",
            "cross_width": "15um",
            "subtract": False,
        },
    )
    records = design.shapes.by_component(f"M_{mtype}")
    assert len(records) == 1
    rec = records[0]
    assert rec.geometry.is_valid
    assert not rec.geometry.is_empty

    # Subtracted marker with ground_guard
    PackagingMarker(
        design,
        f"M_{mtype}_sub",
        options={
            "marker_type": mtype,
            "subtract": True,
        },
    )
    records_sub = design.shapes.by_component(f"M_{mtype}_sub")
    assert len(records_sub) == 2  # ground, cutout


# ==============================================================================
# 6. Exporter Compatibility Test
# ==============================================================================
def test_all_new_components_in_design_export():
    design = PlanarDesign()
    CircularTransmon(design, "Q1", options={"pos_x": "-1000um", "pos_y": "0um"})
    ChargeTee(design, "T1", options={"pos_x": "-1000um", "pos_y": "500um"})
    ChargeClaw(design, "C1", options={"pos_x": "0um", "pos_y": "500um"})
    ChargeArc(design, "A1", options={"pos_x": "1000um", "pos_y": "500um"})
    ReadTee(design, "RT1", options={"pos_x": "0um", "pos_y": "-500um"})
    Launchpad(design, "LP1", options={"pos_x": "-2000um", "pos_y": "0um"})
    CPWOpen(design, "Open1", options={"pos_x": "2000um", "pos_y": "0um"})
    CPWShort(design, "Short1", options={"pos_x": "2000um", "pos_y": "500um"})
    Text(design, "Lbl", options={"pos_x": "0um", "pos_y": "0um", "text": "QPU-1"})
    PackagingMarker(design, "Mark", options={"pos_x": "3000um", "pos_y": "3000um"})

    # Test Matplotlib export
    fig = design.export("mpl")
    assert fig is not None
    import matplotlib.pyplot as plt

    plt.close(fig)

    # Test GDS export
    import os
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        out = os.path.join(tmpdir, "all_components.gds")
        path = design.export("gds", filepath=out, ground_plane=False)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0
