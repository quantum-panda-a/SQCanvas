"""Unit tests for Component Registry, Component Palette Widget, and Placement Engine."""

import os
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from sqcanvas.components import (
    COMPONENT_CATALOG,
    CrossTransmon,
    DualPadTransmon,
    get_component_catalog,
    get_component_meta,
)
from sqcanvas.designs.design_planar import PlanarDesign
from sqcanvas.gui.main_window import MainWindow, _xmon_example_design
from sqcanvas.gui.palette import ComponentPaletteWidget
from sqcanvas.gui.placement import PlacementController


@pytest.fixture(scope="session")
def qapp():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_component_registry():
    """Verify component catalog discovery and retrieval."""
    catalog = get_component_catalog()
    assert len(catalog) >= 15
    assert any(m.cls is DualPadTransmon for m in catalog)
    assert any(m.cls is CrossTransmon for m in catalog)

    meta_transmon = get_component_meta("DualPadTransmon")
    assert meta_transmon is not None
    assert meta_transmon.category == "Qubits"
    assert meta_transmon.default_prefix == "Q"

    meta_by_cls = get_component_meta(CrossTransmon)
    assert meta_by_cls is not None
    assert "Cross" in meta_by_cls.display_name


def test_component_palette_widget(qapp):
    """Test palette widget UI, searching, and snap selection."""
    palette = ComponentPaletteWidget()
    assert palette.tree.topLevelItemCount() >= 4  # Qubits, Couplers, Ports, Markers, Text

    # Test searching
    palette.search_input.setText("transmon")
    # Tree should filter items without crashing
    assert palette.tree.topLevelItemCount() > 0

    palette.search_input.setText("")

    # Test snap selection
    assert palette.get_current_grid_snap() == 50.0
    palette.combo_snap.setCurrentIndex(1)  # 10 um
    assert palette.get_current_grid_snap() == 10.0

    # Test arming component
    meta = get_component_meta("DualPadTransmon")
    palette.set_active_component(meta)
    assert palette.active_meta == meta
    assert not palette.btn_cancel_placement.isHidden()

    # Test disarming
    palette.set_active_component(None)
    assert palette.active_meta is None
    assert palette.btn_cancel_placement.isHidden()


def test_placement_controller(qapp):
    """Test placement controller snapping, rotation, ghost preview, and component placement."""
    from matplotlib.figure import Figure

    fig = Figure()
    ax = fig.add_subplot(111)
    ax.set_xlim(-1000, 1000)
    ax.set_ylim(-1000, 1000)

    placement = PlacementController(fig, ax, grid_snap=50.0)
    assert placement.is_active is False

    # Snapping
    assert placement.snap_coord(123.4, 488.1) == (100.0, 500.0)

    # Arming
    meta = get_component_meta("DualPadTransmon")
    placement.arm(meta)
    assert placement.is_active is True

    # Rotation
    assert placement.rotation == 0.0
    placement.rotate_cw()
    assert placement.rotation == 270.0
    placement.rotate_ccw()
    assert placement.rotation == 0.0

    # Ghost motion
    snapped = placement.handle_motion(102.0, 198.0)
    assert snapped == (100.0, 200.0)
    assert len(placement._artists) >= 3  # crosshairs, arrow, box, text

    # Place component on design
    design = PlanarDesign()
    comp = placement.handle_click(design, 100.0, 200.0)
    assert comp is not None
    assert comp.name == "Q1"
    assert "Q1" in design.components
    assert len(placement._artists) == 0  # ghost cleared on placement

    # Place second component -> should auto-increment to Q2
    placement.arm(meta)
    comp2 = placement.handle_click(design, 500.0, 500.0)
    assert comp2 is not None
    assert comp2.name == "Q2"
    assert "Q2" in design.components


def test_main_window_blank_startup_and_placement_workflow(qapp):
    """Test MainWindow blank startup and end-to-end interactive component placement."""
    # 1. Blank startup (design=None)
    win = MainWindow(design=None)
    assert win.design is not None
    assert len(win.design.components) == 0
    assert win.palette_dock is not None
    assert win.palette is not None

    # 2. Select component in palette to arm placement
    meta = get_component_meta("DualPadTransmon")
    win._on_palette_component_selected(meta)
    assert win.canvas.placement.is_active is True
    assert "Placing" in win.status_dot.text()

    # 3. Rotate placement with 'R' shortcut
    win._on_canvas_shortcut("r")
    assert win.canvas.placement.rotation == 270.0

    # 4. Click canvas to place component
    win._on_canvas_click_point(0.0, 0.0)
    assert len(win.design.components) == 1
    assert "Q1" in win.design.components
    assert win.canvas.placement.is_active is False
    assert win._selected_component == "Q1"
    assert win.inspector.lbl_title.text() == "Q1"

    # 5. Load example design
    win.load_example_design("xmon")
    assert len(win.design.components) == 3
    assert "Q1" in win.design.components
    assert "claw_1" in win.design.components
    assert "port_in" in win.design.components

    # 6. Reset to blank design
    win.new_design()
    assert len(win.design.components) == 0
    assert win._selected_component is None
