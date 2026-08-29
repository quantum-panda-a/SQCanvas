import os

import pytest
from PySide6.QtWidgets import QApplication

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


def test_mpl_canvas(qapp):
    canvas = MplCanvas(width=4.0, height=3.0, dpi=80)
    assert canvas.axes is not None


def test_main_window_with_custom_and_demo_design(qapp):
    demo = _demo_design()
    assert len(demo.components) == 2

    # Window with demo design
    win = MainWindow(design=demo)
    assert win.windowTitle() == "QCanvas"
    assert win.component_list.count() == 2

    # Window with empty design
    empty_design = PlanarDesign()
    win2 = MainWindow(design=empty_design)
    assert win2.component_list.count() == 0


def test_main_window_live_reactive_updates(qapp):
    from qcanvas.components import TransmonPocket

    design = PlanarDesign()
    win = MainWindow(design=design)
    assert win.component_list.count() == 0

    # Add Q1 dynamically -> GUI should automatically refresh and show 1 item
    TransmonPocket(design, "Q1")
    assert win.component_list.count() == 1
    assert win.component_list.item(0).text() == "Q1"

    # Add Q2 dynamically -> GUI should automatically show 2 items
    TransmonPocket(design, "Q2")
    assert win.component_list.count() == 2

    # Remove Q1 -> GUI should automatically show 1 item
    design.remove_component("Q1")
    assert win.component_list.count() == 1
    assert win.component_list.item(0).text() == "Q2"

    win.close()
