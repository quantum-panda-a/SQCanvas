import pytest
from shapely.geometry import Polygon

from qcanvas.components.base import Component
from qcanvas.components.transmon import CrossTransmon, DualPadTransmon, SinglePadTransmon
from qcanvas.designs.design_planar import PlanarDesign

from qcanvas.utility.attr_dict import AttrDict


class DummyComponent(Component):
    default_options = AttrDict(size="100um")

    def make(self):
        p = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        self.add_shape("dummy_shape", self.place(p))


def test_component_base():
    design = PlanarDesign()
    comp = DummyComponent(
        design,
        "D1",
        options={"pos_x": "1mm", "pos_y": "2mm", "orientation": "90", "layer": "2"},
    )
    assert comp.name == "D1"
    assert comp.origin == (1000.0, 2000.0)
    assert comp.rotation == 90.0
    assert comp.layer == 2
    assert comp.chip == "main"
    assert comp["size"] == pytest.approx(100.0)
    assert "DummyComponent" in repr(comp)

    # Rebuild
    comp.rebuild()
    assert len(design.shapes.by_component("D1")) == 1


def test_dual_pad_transmon():
    design = PlanarDesign()
    DualPadTransmon(
        design,
        "Q1",
        options={
            "pos_x": "0.0mm",
            "pos_y": "0.0mm",
            "pad_width": "450um",
            "pad_height": "100um",
            "pad_gap": "30um",
            "gap_top": "50um",
            "gap_down": "50um",
            "gap_left": "50um",
            "gap_right": "50um",
            "ground_guard": "15um",
        },
    )

    records = design.shapes.by_component("Q1")
    # ground, cutout, top metal, bottom metal, junction bridge
    assert len(records) == 5

    ground_rec = next(r for r in records if r.label == "ground")
    assert ground_rec.subtract is False
    assert not ground_rec.geometry.is_empty

    cutout_rec = next(r for r in records if r.label == "cutout")
    assert cutout_rec.subtract is True

    metal_recs = [r for r in records if r.label == "metal"]
    assert len(metal_recs) == 2  # 2 islands

    junc_rec = next(r for r in records if r.label == "junction")
    assert junc_rec.subtract is False

    # Test without ground guard (ground_guard=0)
    DualPadTransmon(design, "Q2", options={"ground_guard": "0um"})
    records_q2 = design.shapes.by_component("Q2")
    assert len(records_q2) == 4  # cutout, 2 metal islands, junction
    assert not any(r.label == "ground" for r in records_q2)


def test_dual_pad_transmon_defaults():
    design = PlanarDesign()
    assert DualPadTransmon.default_options.ground_guard == "30um"
    assert DualPadTransmon.default_options.gap_top == "35um"
    assert DualPadTransmon.default_options.gap_down == "35um"
    assert DualPadTransmon.default_options.gap_left == "35um"
    assert DualPadTransmon.default_options.gap_right == "35um"
    assert DualPadTransmon.default_options.pad_fillet == "0um"
    assert DualPadTransmon.default_options.cutout_fillet == "0um"

    q = DualPadTransmon(design, "Q_default")
    assert q.options.ground_guard == 30.0
    assert q.options.gap_top == 35.0
    assert q.options.gap_down == 35.0
    assert q.options.gap_left == 35.0
    assert q.options.gap_right == 35.0
    assert q.options.pad_fillet == 0.0
    assert q.options.cutout_fillet == 0.0

    records = design.shapes.by_component("Q_default")
    cutout_rec = next(r for r in records if r.label == "cutout")
    # pad_w=455, pad_h=90, pad_gap=30
    # cutout_w = 455 + 35 + 35 = 525
    # cutout_h = 2*90 + 30 + 35 + 35 = 280
    assert cutout_rec.geometry.bounds == pytest.approx((-262.5, -140.0, 262.5, 140.0))

    ground_rec = next(r for r in records if r.label == "ground")
    # ground_outer = cutout + 2*30um guard
    assert ground_rec.geometry.bounds == pytest.approx((-292.5, -170.0, 292.5, 170.0))


def test_dual_pad_transmon_asymmetric_gaps():
    design = PlanarDesign()
    DualPadTransmon(
        design,
        "Q_asym",
        options={
            "pad_width": "400um",
            "pad_height": "100um",
            "pad_gap": "20um",
            "gap_top": "40um",
            "gap_down": "20um",
            "gap_left": "10um",
            "gap_right": "50um",
            "ground_guard": "30um",
        },
    )
    records = design.shapes.by_component("Q_asym")
    cutout_rec = next(r for r in records if r.label == "cutout")
    # pad_w=400 -> x in [-200, 200]
    # xmin = -200 - 10 = -210, xmax = 200 + 50 = 250
    # top_pad y in [10, 110] -> ymax = 110 + 40 = 150
    # bot_pad y in [-110, -10] -> ymin = -110 - 20 = -130
    assert cutout_rec.geometry.bounds == pytest.approx((-210.0, -130.0, 250.0, 150.0))


def test_dual_pad_transmon_fillets():
    design = PlanarDesign()
    DualPadTransmon(
        design,
        "Q_fillet",
        options={
            "pad_fillet": "10um",
            "cutout_fillet": "15um",
            "ground_guard": "30um",
        },
    )
    records = design.shapes.by_component("Q_fillet")
    cutout_rec = next(r for r in records if r.label == "cutout")
    metal_recs = [r for r in records if r.label == "metal"]
    ground_rec = next(r for r in records if r.label == "ground")

    # Pads should have rounded corners (more than 5 exterior vertices)
    for m in metal_recs:
        assert len(m.geometry.exterior.coords) > 5
        assert m.geometry.is_valid

    # Cutout should have rounded corners
    assert len(cutout_rec.geometry.exterior.coords) > 5
    assert cutout_rec.geometry.is_valid

    # Ground ring should subtract rounded cutout cleanly
    assert ground_rec.geometry.is_valid
    assert not ground_rec.geometry.is_empty


def test_dual_pad_transmon_rotation():
    design = PlanarDesign()
    DualPadTransmon(
        design,
        "Q_rot",
        options={
            "pos_x": "2000um",
            "pos_y": "1000um",
            "orientation": "90",
            "pad_gap": "30um",
            "pad_height": "90um",
            "ground_guard": "10um",
        },
    )
    records = design.shapes.by_component("Q_rot")
    metal_recs = [r for r in records if r.label == "metal"]
    # At 90 deg rotation, island_y = 60um on Y axis rotates to X axis (-60um, +60um) relative to origin (2000, 1000)
    c1 = metal_recs[0].geometry.centroid
    c2 = metal_recs[1].geometry.centroid
    xs = sorted([c1.x, c2.x])
    ys = [c1.y, c2.y]
    assert xs[0] == pytest.approx(1940.0)
    assert xs[1] == pytest.approx(2060.0)
    assert ys[0] == pytest.approx(1000.0)
    assert ys[1] == pytest.approx(1000.0)


def test_unimplemented_make():
    design = PlanarDesign()
    with pytest.raises(NotImplementedError):
        Component(design, "RawComp")


def test_single_pad_transmon_defaults():
    design = PlanarDesign()
    assert SinglePadTransmon.default_options.pad_width == "455um"
    assert SinglePadTransmon.default_options.pad_height == "90um"
    assert SinglePadTransmon.default_options.inductor_width == "20um"
    assert SinglePadTransmon.default_options.gap_top == "35um"
    assert SinglePadTransmon.default_options.gap_down == "35um"
    assert SinglePadTransmon.default_options.gap_left == "35um"
    assert SinglePadTransmon.default_options.gap_right == "35um"
    assert SinglePadTransmon.default_options.pad_fillet == "0um"
    assert SinglePadTransmon.default_options.cutout_fillet == "0um"
    assert SinglePadTransmon.default_options.ground_guard == "30um"

    q = SinglePadTransmon(design, "Q_single_default")
    assert q.options.pad_width == 455.0
    assert q.options.pad_height == 90.0
    assert q.options.inductor_width == 20.0
    assert q.options.gap_top == 35.0
    assert q.options.gap_down == 35.0

    records = design.shapes.by_component("Q_single_default")
    # ground, cutout, metal, junction
    assert len(records) == 4

    metal_rec = next(r for r in records if r.label == "metal")
    assert metal_rec.subtract is False
    assert metal_rec.geometry.bounds == pytest.approx((-227.5, -45.0, 227.5, 45.0))
    assert metal_rec.geometry.centroid.x == pytest.approx(0.0)
    assert metal_rec.geometry.centroid.y == pytest.approx(0.0)

    cutout_rec = next(r for r in records if r.label == "cutout")
    assert cutout_rec.subtract is True
    # cutout_w = 455 + 35 + 35 = 525, cutout_h = 90 + 35 + 35 = 160
    assert cutout_rec.geometry.bounds == pytest.approx((-262.5, -80.0, 262.5, 80.0))

    ground_rec = next(r for r in records if r.label == "ground")
    assert ground_rec.subtract is False
    assert ground_rec.geometry.bounds == pytest.approx((-292.5, -110.0, 292.5, 110.0))

    junc_rec = next(r for r in records if r.label == "junction")
    assert junc_rec.subtract is False
    # junction in bottom gap: x in [-10, 10], y from -80 to -45
    assert junc_rec.geometry.bounds == pytest.approx((-10.0, -80.0, 10.0, -45.0))


def test_single_pad_transmon_asymmetric_and_fillet():
    design = PlanarDesign()
    SinglePadTransmon(
        design,
        "Q_single_asym",
        options={
            "pad_width": "400um",
            "pad_height": "100um",
            "inductor_width": "15um",
            "gap_top": "40um",
            "gap_down": "20um",
            "gap_left": "10um",
            "gap_right": "50um",
            "pad_fillet": "8um",
            "cutout_fillet": "12um",
            "ground_guard": "25um",
        },
    )
    records = design.shapes.by_component("Q_single_asym")
    metal_rec = next(r for r in records if r.label == "metal")
    cutout_rec = next(r for r in records if r.label == "cutout")
    junc_rec = next(r for r in records if r.label == "junction")

    # Pad centroid is at (0, 0)
    assert metal_rec.geometry.centroid.x == pytest.approx(0.0)
    assert metal_rec.geometry.centroid.y == pytest.approx(0.0)
    # Filleted pad and cutout have more vertices than 5
    assert len(metal_rec.geometry.exterior.coords) > 5
    assert len(cutout_rec.geometry.exterior.coords) > 5

    # Cutout: x in [-200 - 10, 200 + 50] = [-210, 250], y in [-50 - 20, 50 + 40] = [-70, 90]
    assert cutout_rec.geometry.bounds == pytest.approx((-210.0, -70.0, 250.0, 90.0))

    # Junction: x in [-7.5, 7.5], y in [-70, -50]
    assert junc_rec.geometry.bounds == pytest.approx((-7.5, -70.0, 7.5, -50.0))


def test_single_pad_transmon_ground_guard_zero():
    design = PlanarDesign()
    SinglePadTransmon(design, "Q_single_noguard", options={"ground_guard": "0um"})
    records = design.shapes.by_component("Q_single_noguard")
    assert len(records) == 3
    assert not any(r.label == "ground" for r in records)


def test_single_pad_transmon_placement_and_rotation():
    design = PlanarDesign()
    SinglePadTransmon(
        design,
        "Q_single_rot",
        options={
            "pos_x": "1000um",
            "pos_y": "500um",
            "orientation": "90",
            "pad_width": "400um",
            "pad_height": "100um",
            "gap_down": "30um",
            "inductor_width": "20um",
        },
    )
    records = design.shapes.by_component("Q_single_rot")
    metal_rec = next(r for r in records if r.label == "metal")
    junc_rec = next(r for r in records if r.label == "junction")

    # Pad center placed at (1000, 500)
    assert metal_rec.geometry.centroid.x == pytest.approx(1000.0)
    assert metal_rec.geometry.centroid.y == pytest.approx(500.0)

    # In local unrotated: junction is at (0, -pad_h/2 - gap/2) = (0, -50 - 15) = (0, -65)
    # Rotated 90 deg CCW: (0, -65) -> (+65, 0) -> Translated: (1065, 500)
    assert junc_rec.geometry.centroid.x == pytest.approx(1065.0)
    assert junc_rec.geometry.centroid.y == pytest.approx(500.0)


def test_cross_transmon_defaults():
    design = PlanarDesign()
    assert CrossTransmon.default_options.cross_width == "20um"
    assert CrossTransmon.default_options.cross_length == "200um"
    assert CrossTransmon.default_options.cross_gap == "20um"
    assert CrossTransmon.default_options.inductor_width == "20um"
    assert CrossTransmon.default_options.ground_guard == "30um"

    q = CrossTransmon(design, "Q_cross_default")
    assert q.options.cross_width == 20.0
    assert q.options.cross_length == 200.0
    assert q.options.cross_gap == 20.0
    assert q.options.inductor_width == 20.0
    assert q.options.ground_guard == 30.0

    records = design.shapes.by_component("Q_cross_default")
    assert len(records) == 4  # ground, cutout, metal, junction

    metal_rec = next(r for r in records if r.label == "metal")
    assert metal_rec.subtract is False
    assert metal_rec.geometry.bounds == pytest.approx((-200.0, -200.0, 200.0, 200.0))
    assert metal_rec.geometry.centroid.x == pytest.approx(0.0)
    assert metal_rec.geometry.centroid.y == pytest.approx(0.0)
    # Cross shape area: horizontal bar (400 * 20) + vertical bar (20 * 400) - intersection (20 * 20) = 8000 + 8000 - 400 = 15600
    assert metal_rec.geometry.area == pytest.approx(15600.0)

    cutout_rec = next(r for r in records if r.label == "cutout")
    assert cutout_rec.subtract is True
    assert cutout_rec.geometry.bounds == pytest.approx((-220.0, -220.0, 220.0, 220.0))
    # Cutout area: (440 * 60) + (60 * 440) - (60 * 60) = 26400 + 26400 - 3600 = 49200
    assert cutout_rec.geometry.area == pytest.approx(49200.0)

    ground_rec = next(r for r in records if r.label == "ground")
    assert ground_rec.subtract is False
    # Outer ground dimension: 2 * (200 + 20 + 30) = 500 -> bounds [-250, -250, 250, 250]
    assert ground_rec.geometry.bounds == pytest.approx((-250.0, -250.0, 250.0, 250.0))

    junc_rec = next(r for r in records if r.label == "junction")
    assert junc_rec.subtract is False
    # Junction in south gap: x in [-10, 10], y from -220 to -200
    assert junc_rec.geometry.bounds == pytest.approx((-10.0, -220.0, 10.0, -200.0))
    assert junc_rec.geometry.centroid.x == pytest.approx(0.0)
    assert junc_rec.geometry.centroid.y == pytest.approx(-210.0)


def test_cross_transmon_ground_guard_zero():
    design = PlanarDesign()
    CrossTransmon(design, "Q_cross_noguard", options={"ground_guard": "0um"})
    records = design.shapes.by_component("Q_cross_noguard")
    assert len(records) == 3
    assert not any(r.label == "ground" for r in records)


def test_cross_transmon_placement_and_rotation():
    design = PlanarDesign()
    CrossTransmon(
        design,
        "Q_cross_rot",
        options={
            "pos_x": "1500um",
            "pos_y": "-500um",
            "orientation": "180",
            "cross_length": "150um",
            "cross_width": "30um",
            "cross_gap": "25um",
            "inductor_width": "20um",
        },
    )
    records = design.shapes.by_component("Q_cross_rot")
    metal_rec = next(r for r in records if r.label == "metal")
    junc_rec = next(r for r in records if r.label == "junction")

    # Center is placed at (1500, -500)
    assert metal_rec.geometry.centroid.x == pytest.approx(1500.0)
    assert metal_rec.geometry.centroid.y == pytest.approx(-500.0)

    # Local unrotated junction: centroid is at (0, -cross_length - cross_gap / 2) = (0, -150 - 12.5) = (0, -162.5)
    # Rotated 180 deg: (0, +162.5) -> Translated: (1500, -500 + 162.5) = (1500, -337.5)
    assert junc_rec.geometry.centroid.x == pytest.approx(1500.0)
    assert junc_rec.geometry.centroid.y == pytest.approx(-337.5)


def test_cross_transmon_fillets():
    design = PlanarDesign()
    CrossTransmon(
        design,
        "Q_cross_fillet",
        options={
            "cross_length": "200um",
            "cross_width": "20um",
            "cross_gap": "20um",
            "cross_fillet": "5um",
            "cutout_fillet": "8um",
            "ground_guard": "30um",
        },
    )
    records = design.shapes.by_component("Q_cross_fillet")
    metal_rec = next(r for r in records if r.label == "metal")
    cutout_rec = next(r for r in records if r.label == "cutout")
    ground_rec = next(r for r in records if r.label == "ground")

    assert metal_rec.geometry.is_valid
    assert cutout_rec.geometry.is_valid
    assert ground_rec.geometry.is_valid
    assert not ground_rec.geometry.is_empty

    # Filleted cross and cutout have rounded corners (> 13 vertices)
    assert len(metal_rec.geometry.exterior.coords) > 13
    assert len(cutout_rec.geometry.exterior.coords) > 13


