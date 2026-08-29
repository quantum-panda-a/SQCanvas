import pytest
from shapely.geometry import Polygon

from qcanvas.components.base import Component
from qcanvas.components.transmon import DualPadTransmon
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
