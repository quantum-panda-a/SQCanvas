import os

import pytest
from PySide6.QtWidgets import QApplication

from qcanvas.components import DualPadTransmon
from qcanvas.designs.design_planar import PlanarDesign
from qcanvas.gui.canvas import MplCanvas
from qcanvas.gui.main_window import MainWindow, _demo_design


@pytest.fixture(scope="session")
def qapp():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_mpl_canvas_highlights_and_zoom(qapp):
    canvas = MplCanvas(width=4.0, height=3.0, dpi=80)
    assert canvas.axes is not None
    assert canvas.interaction is not None

    # Test highlight
    canvas.highlight_component("Q1", bounds=(-100.0, -50.0, 100.0, 50.0))
    assert len(canvas._highlights) == 2  # Rectangle patch + Text badge

    # Test clear highlight
    canvas.clear_highlight()
    assert len(canvas._highlights) == 0

    # Test all labels toggle
    bounds_map = {"Q1": (-100.0, -50.0, 100.0, 50.0), "Q2": (200.0, 100.0, 400.0, 200.0)}
    visible = canvas.toggle_all_labels(bounds_map)
    assert visible is True
    assert len(canvas._labels) == 2

    # Toggle off
    visible = canvas.toggle_all_labels(bounds_map)
    assert visible is False
    assert len(canvas._labels) == 0

    # Test zoom_to_rect
    canvas.zoom_to_rect((-50.0, -50.0, 50.0, 50.0))
    xlim = canvas.axes.get_xlim()
    ylim = canvas.axes.get_ylim()
    assert xlim[0] < -50.0 and xlim[1] > 50.0
    assert ylim[0] < -50.0 and ylim[1] > 50.0


def test_main_window_with_custom_and_demo_design(qapp):
    demo = _demo_design()
    assert len(demo.components) == 2

    # Window with demo design
    win = MainWindow(design=demo)
    assert win.windowTitle() == "QCanvas Viewer"
    assert win.component_table.rowCount() == 2
    assert win.component_table.item(0, 0).text() == "Q1"
    assert win.component_table.item(0, 1).text() == "DualPadTransmon"
    assert win.show_grid.isChecked() is True
    assert win.coord_label is not None
    assert win.hint_label is not None
    win.close()

    # Window with empty design
    empty_design = PlanarDesign()
    win2 = MainWindow(design=empty_design)
    assert win2.component_table.rowCount() == 0
    win2.close()


def test_main_window_live_reactive_updates(qapp):
    design = PlanarDesign()
    win = MainWindow(design=design)
    assert win.component_table.rowCount() == 0

    # Add Q1 dynamically -> GUI should automatically refresh and show 1 item with Type
    DualPadTransmon(design, "Q1")
    assert win.component_table.rowCount() == 1
    assert win.component_table.item(0, 0).text() == "Q1"
    assert win.component_table.item(0, 1).text() == "DualPadTransmon"

    # Add Q2 dynamically -> GUI should automatically show 2 items
    DualPadTransmon(design, "Q2")
    assert win.component_table.rowCount() == 2

    # Remove Q1 -> GUI should automatically show 1 item
    design.remove_component("Q1")
    assert win.component_table.rowCount() == 1
    assert win.component_table.item(0, 0).text() == "Q2"

    win.close()


def test_main_window_interaction_and_selection(qapp):
    demo = _demo_design()
    win = MainWindow(design=demo)

    # Hover coordinate update
    win._on_hover_coord(100.5, -250.2)
    assert "100.50" in win.coord_label.text()
    assert "-250.20" in win.coord_label.text()

    # Hover outside
    win._on_hover_coord(None, None)
    assert "--" in win.coord_label.text()

    # Select component Q1 directly
    win.select_component("Q1")
    assert win._selected_component == "Q1"
    assert len(win.canvas._highlights) > 0
    assert "Q1" in win.hint_label.text()

    # Clear selection
    win.clear_selection()
    assert win._selected_component is None
    assert len(win.canvas._highlights) == 0

    # Point pick hit on Q1 at (-2000um, 0um)
    hit = win._find_component_at(-2000.0, 0.0)
    assert hit == "Q1"

    # Point pick on empty space far away
    miss = win._find_component_at(99999.0, 99999.0)
    assert miss is None

    # Simulate canvas click on Q1
    win._on_canvas_click_point(-2000.0, 0.0)
    assert win._selected_component == "Q1"

    # Simulate canvas click on empty space
    win._on_canvas_click_point(99999.0, 99999.0)
    assert win._selected_component is None

    # Test grid toggle
    win.show_grid.setChecked(False)
    assert win.show_grid.isChecked() is False
    win.show_grid.setChecked(True)
    assert win.show_grid.isChecked() is True

    # Test shortcuts
    win._on_canvas_shortcut("a")  # fit_all
    win._on_canvas_shortcut("A")  # fit_chip
    win._on_canvas_shortcut("r")  # rebuild
    win._on_canvas_shortcut("l")  # toggle labels
    assert win.canvas.labels_visible is True
    win._on_canvas_shortcut("l")  # toggle off
    assert win.canvas.labels_visible is False

    win.close()
