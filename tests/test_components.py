import pytest
from shapely.geometry import Polygon

from qcanvas.components.base import Component
from qcanvas.components.transmon import TransmonPocket
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


def test_transmon_pocket():
    design = PlanarDesign()
    TransmonPocket(
        design,
        "Q1",
        options={
            "pos_x": "0.0mm",
            "pos_y": "0.0mm",
            "pad_width": "450um",
            "pad_height": "100um",
            "pad_gap": "30um",
            "pocket_width": "700um",
            "pocket_height": "700um",
            "ground_guard": "15um",
        },
    )

    records = design.shapes.by_component("Q1")
    # ground, pocket, top metal, bottom metal, junction bridge
    assert len(records) == 5

    ground_rec = next(r for r in records if r.label == "ground")
    assert ground_rec.subtract is False
    assert not ground_rec.geometry.is_empty

    pocket_rec = next(r for r in records if r.label == "pocket")
    assert pocket_rec.subtract is True

    metal_recs = [r for r in records if r.label == "metal"]
    assert len(metal_recs) == 2  # 2 islands

    junc_rec = next(r for r in records if r.label == "junction")
    assert junc_rec.subtract is False

    # Test without ground guard (ground_guard=0)
    TransmonPocket(design, "Q2", options={"ground_guard": "0um"})
    records_q2 = design.shapes.by_component("Q2")
    assert len(records_q2) == 4  # pocket, 2 metal islands, junction
    assert not any(r.label == "ground" for r in records_q2)


def test_transmon_pocket_rotation():
    design = PlanarDesign()
    TransmonPocket(
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
