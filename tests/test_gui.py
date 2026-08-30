import os

import pytest
from PySide6.QtWidgets import QApplication

from qcanvas.components import DualPadTransmon
from qcanvas.designs.design_planar import PlanarDesign
from qcanvas.gui.canvas import MplCanvas
from qcanvas.gui.inspector import PropertyInspector
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
    assert canvas.ruler is not None

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

    # Test zoom_to_rect and scale bar update
    canvas.zoom_to_rect((-50.0, -50.0, 50.0, 50.0))
    xlim = canvas.axes.get_xlim()
    ylim = canvas.axes.get_ylim()
    assert xlim[0] < -50.0 and xlim[1] > 50.0
    assert ylim[0] < -50.0 and ylim[1] > 50.0
    assert len(canvas._scale_bar_artists) > 0

    # Test scale bar toggle
    canvas.set_scale_bar_visible(False)
    assert len(canvas._scale_bar_artists) == 0
    canvas.set_scale_bar_visible(True)
    assert len(canvas._scale_bar_artists) > 0

    # Test crosshair cursor update
    canvas._update_crosshair(0.0, 0.0)
    assert canvas._crosshair_h.get_visible() is True
    assert canvas._crosshair_v.get_visible() is True
    canvas._update_crosshair(None, None)
    assert canvas._crosshair_h.get_visible() is False
    assert canvas._crosshair_v.get_visible() is False


def test_canvas_ruler_measurement(qapp):
    canvas = MplCanvas(width=4.0, height=3.0, dpi=80)
    ruler = canvas.ruler

    assert ruler.active is False
    ruler.toggle()
    assert ruler.active is True

    # Click first point
    msg1 = ruler.handle_click(0.0, 0.0)
    assert "Ruler start" in msg1
    assert ruler._start_pt == (0.0, 0.0)

    # Hover motion
    ruler.handle_motion(300.0, 400.0)
    assert len(ruler._artists) > 0

    # Click second point (finalize 3-4-5 triangle -> 500um distance)
    msg2 = ruler.handle_click(300.0, 400.0)
    assert "Dist = 500.00 um" in msg2
    assert "ΔX = 300.00 um" in msg2
    assert "ΔY = 400.00 um" in msg2

    ruler.clear()
    assert len(ruler._artists) == 0


def test_property_inspector_live_update(qapp):
    design = PlanarDesign()
    q1 = DualPadTransmon(design, "Q1", options={"pad_width": "400um", "pad_height": "80um"})

    inspector = PropertyInspector()
    inspector.set_component(q1)

    assert inspector.lbl_title.text() == "Q1"
    assert "pad_width" in inspector._input_fields
    assert "400" in inspector._input_fields["pad_width"].text()

    # Modify property and apply
    inspector._input_fields["pad_width"].setText("600um")
    inspector._on_apply_clicked()

    assert "600" in str(q1.options["pad_width"])

    # Clear inspector
    inspector.set_component(None)
    assert inspector.lbl_title.text() == "No Component Selected"


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
    assert win.show_scale_bar.isChecked() is True
    assert win.coord_label is not None
    assert win.hint_label is not None
    assert win.inspector is not None
    assert win.hud_toolbar is not None
    assert win.theme_combo is not None
    assert win.theme_combo.count() == 9

    # Test scale bar toggle in main window
    win.show_scale_bar.setChecked(False)
    assert win.canvas.scale_bar_visible is False
    win.show_scale_bar.setChecked(True)
    assert win.canvas.scale_bar_visible is True

    # Test theme preset switching across all 9 themes
    all_themes = ["nordic", "aurora", "paper", "no002", "no005", "no008", "no009", "no013", "cyber"]
    for theme_key in all_themes:
        win.set_theme_preset(theme_key)
        assert win.active_theme == theme_key
        assert win.canvas.current_theme == theme_key

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
    assert win.inspector.current_component.name == "Q1"

    # Clear selection
    win.clear_selection()
    assert win._selected_component is None
    assert len(win.canvas._highlights) == 0
    assert win.inspector.current_component is None

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

    # Test search filter
    win.search_input.setText("Q1")
    assert win.component_table.isRowHidden(0) is False
    assert win.component_table.isRowHidden(1) is True
    win.search_input.setText("")
    assert win.component_table.isRowHidden(1) is False

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

    # Test ruler toggle
    win._on_canvas_shortcut("m")
    assert win.canvas.ruler.active is True
    win._on_canvas_shortcut("m")
    assert win.canvas.ruler.active is False

    win.close()
