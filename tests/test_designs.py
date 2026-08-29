import pytest
from shapely.geometry import Point

from qcanvas.components.transmon import DualPadTransmon
from qcanvas.designs.design_base import Design
from qcanvas.designs.design_planar import PlanarDesign


def test_design_base():
    design = Design(metadata={"project": "test_qcanvas"})
    assert design.name == "Design"
    assert design.units == "um"

    # Add shape directly
    rec = design.add_shape("custom", "pt", Point(0, 0), layer=1)
    assert rec.component == "custom"
    assert len(design.shapes) == 1

    # Component registration
    t1 = DualPadTransmon(design, "Q1")
    assert "Q1" in design.components
    assert design.get_components() == [t1]

    # Duplicate component name without overwrite raises ValueError
    with pytest.raises(ValueError):
        DualPadTransmon(design, "Q1")

    # Rebuild single component and full design
    design.rebuild_component("Q1")
    design.rebuild()
    assert "Q1" in design.components

    with pytest.raises(KeyError):
        design.rebuild_component("NonExistent")

    # Remove component
    design.remove_component("Q1")
    assert "Q1" not in design.components
    assert len(design.shapes.by_component("Q1")) == 0

    with pytest.raises(KeyError):
        design.remove_component("NonExistent")


def test_design_overwrite():
    design = Design(overwrite_enabled=True)
    DualPadTransmon(design, "Q1")
    DualPadTransmon(design, "Q1")
    assert "Q1" in design.components


def test_design_exporter_lookup():
    design = Design()
    mpl_exp = design.exporter("mpl")
    assert mpl_exp.name == "mpl"
    # Caching check
    assert design.exporter("mpl") is mpl_exp

    with pytest.raises(KeyError):
        design.exporter("unknown_exporter_type")


def test_planar_design():
    design = PlanarDesign()
    assert design.name == "PlanarDesign"
    assert design.main_chip is not None
    assert design.chip_centre() == (0.0, 0.0)
    assert design.chip_extent() == (9000.0, 6000.0)


def test_design_listeners():
    design = PlanarDesign()
    events = []

    def callback(d):
        events.append(len(d.components))

    design.add_listener(callback)
    DualPadTransmon(design, "Q1")
    assert events == [1]

    DualPadTransmon(design, "Q2")
    assert events == [1, 2]

    design.remove_component("Q1")
    assert events == [1, 2, 1]

    design.remove_listener(callback)
    DualPadTransmon(design, "Q3")
    assert events == [1, 2, 1]
