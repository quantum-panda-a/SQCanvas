"""Unit tests for SQCanvas GUI multi-tab document management and script loading."""

import os

import pytest
from PySide6.QtWidgets import QApplication

from sqcanvas.components import CrossTransmon, DualPadTransmon
from sqcanvas.gui.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_multi_tab_creation_and_switching(qapp):
    """Test creating multiple design tabs and switching between them."""
    win = MainWindow(design=None)
    assert win.tab_widget.count() == 1
    assert "Untitled" in win.tab_widget.tabText(0)

    # Place a component in Tab 1
    DualPadTransmon(win.design, "Q1_tab1")
    assert win.component_table.rowCount() == 1
    assert win.component_table.item(0, 0).text() == "Q1_tab1"

    # Create Tab 2 (New Design)
    win.new_design()
    assert win.tab_widget.count() == 2
    assert win.tab_widget.currentIndex() == 1
    assert "Untitled" in win.tab_widget.tabText(1)
    assert win.component_table.rowCount() == 0  # Blank design

    # Place a component in Tab 2
    CrossTransmon(win.design, "X_tab2")
    assert win.component_table.rowCount() == 1
    assert win.component_table.item(0, 0).text() == "X_tab2"

    # Switch back to Tab 1
    win.tab_widget.setCurrentIndex(0)
    assert win.component_table.rowCount() == 1
    assert win.component_table.item(0, 0).text() == "Q1_tab1"
    assert "Q1_tab1" in win.design.components

    # Switch to Tab 2
    win.tab_widget.setCurrentIndex(1)
    assert win.component_table.rowCount() == 1
    assert win.component_table.item(0, 0).text() == "X_tab2"
    assert "X_tab2" in win.design.components

    win.close()


def test_tab_individual_closing(qapp):
    """Test closing individual tabs and verifying resource cleanup."""
    win = MainWindow(design=None)

    # Open examples to get 3 tabs
    win.load_example_design("transmons")
    win.load_example_design("xmon")
    assert win.tab_widget.count() == 3

    # Close middle tab (index 1: transmons example)
    win._on_tab_close_requested(1)
    assert win.tab_widget.count() == 2
    assert "Xmon" in win.tab_widget.tabText(1)

    # Close remaining tabs
    win._on_tab_close_requested(0)
    assert win.tab_widget.count() == 1

    win.close()


def test_tab_close_single_tab_closes_gui(qapp, monkeypatch):
    """Test that closing the only open tab is equivalent to closing the GUI."""
    win = MainWindow(design=None)
    assert win.tab_widget.count() == 1

    closed = False
    original_close = win.close

    def mock_close():
        nonlocal closed
        closed = True
        return original_close()

    monkeypatch.setattr(win, "close", mock_close)

    # Close the only tab
    win._on_tab_close_requested(0)
    assert closed is True


def test_close_tab_method_and_shortcut(qapp, monkeypatch):
    """Test win.close_tab() method closes tab or GUI when only one tab is open."""
    win = MainWindow(design=None)
    win.load_example_design("transmons")
    assert win.tab_widget.count() == 2

    # Close active tab (index 1) via close_tab()
    win.close_tab()
    assert win.tab_widget.count() == 1

    # Now with 1 tab left, close_tab() should trigger window close
    closed = False
    original_close = win.close

    def mock_close():
        nonlocal closed
        closed = True
        return original_close()

    monkeypatch.setattr(win, "close", mock_close)
    win.close_tab()
    assert closed is True


def test_open_script_with_open_gui_in_main_block_does_not_spawn_rogue_window(tmp_path, qapp):
    """Test opening a script containing design.open_gui() loads cleanly into a tab without extra windows."""
    script_content = """
from sqcanvas.designs import PlanarDesign
from sqcanvas.components import DualPadTransmon

def build_design():
    d = PlanarDesign()
    DualPadTransmon(d, "Q_script", options={"pos_x": "100um", "pos_y": "100um"})
    return d

if __name__ == "__main__":
    design = build_design()
    design.open_gui()
"""
    script_file = tmp_path / "script_with_gui_call.py"
    script_file.write_text(script_content, encoding="utf-8")

    win = MainWindow(design=None)

    # Open script
    win.open_python_script(script_file)

    # Verify tab was populated
    assert win.tab_widget.count() == 1  # Reused empty initial tab
    assert win.tab_widget.tabText(0) == "script_with_gui_call.py"
    assert "Q_script" in win.design.components
    assert "script_with_gui_call.py" in win.windowTitle()

    win.close()


def test_open_multiple_scripts_as_separate_tabs(tmp_path, qapp):
    """Test opening multiple scripts creates separate tabs and re-opening focuses existing tab."""
    script1 = tmp_path / "chip_alpha.py"
    script1.write_text(
        """
from sqcanvas.designs import PlanarDesign
from sqcanvas.components import DualPadTransmon

def build_design():
    d = PlanarDesign()
    DualPadTransmon(d, "Q_alpha")
    return d
""",
        encoding="utf-8",
    )

    script2 = tmp_path / "chip_beta.py"
    script2.write_text(
        """
from sqcanvas.designs import PlanarDesign
from sqcanvas.components import CrossTransmon

def build_design():
    d = PlanarDesign()
    CrossTransmon(d, "X_beta")
    return d
""",
        encoding="utf-8",
    )

    win = MainWindow(design=None)

    # 1. Open script 1 (replaces initial blank tab)
    win.open_python_script(script1)
    assert win.tab_widget.count() == 1
    assert win.tab_widget.tabText(0) == "chip_alpha.py"
    assert "Q_alpha" in win.design.components

    # 2. Open script 2 (opens as new tab)
    win.open_python_script(script2)
    assert win.tab_widget.count() == 2
    assert win.tab_widget.tabText(1) == "chip_beta.py"
    assert win.tab_widget.currentIndex() == 1
    assert "X_beta" in win.design.components

    # 3. Open script 1 again -> should switch back to tab 0 instead of opening 3rd tab
    win.open_python_script(script1)
    assert win.tab_widget.count() == 2
    assert win.tab_widget.currentIndex() == 0
    assert "Q_alpha" in win.design.components

    win.close()


def test_tab_hot_reload_isolates_changes(tmp_path, qapp):
    """Test that modifying a script externally reloads only that script's tab."""
    script_a = tmp_path / "chip_a.py"
    script_a.write_text(
        """
from sqcanvas.designs import PlanarDesign
from sqcanvas.components import DualPadTransmon

def build_design():
    d = PlanarDesign()
    DualPadTransmon(d, "Q_A1")
    return d
""",
        encoding="utf-8",
    )

    script_b = tmp_path / "chip_b.py"
    script_b.write_text(
        """
from sqcanvas.designs import PlanarDesign
from sqcanvas.components import CrossTransmon

def build_design():
    d = PlanarDesign()
    CrossTransmon(d, "X_B1")
    return d
""",
        encoding="utf-8",
    )

    win = MainWindow(design=None)
    win.open_python_script(script_a)
    win.open_python_script(script_b)
    assert win.tab_widget.count() == 2

    # Modify chip_a.py externally
    script_a.write_text(
        """
from sqcanvas.designs import PlanarDesign
from sqcanvas.components import DualPadTransmon

def build_design():
    d = PlanarDesign()
    DualPadTransmon(d, "Q_A1")
    DualPadTransmon(d, "Q_A2")
    return d
""",
        encoding="utf-8",
    )

    # Trigger hot-reload on chip_a
    win._on_file_watcher_modified(script_a.resolve())

    # Switch to tab 0 (chip_a) to check components
    win.tab_widget.setCurrentIndex(0)
    assert len(win.design.components) == 2
    assert "Q_A1" in win.design.components
    assert "Q_A2" in win.design.components

    # Switch to tab 1 (chip_b) and verify it was unaffected
    win.tab_widget.setCurrentIndex(1)
    assert len(win.design.components) == 1
    assert "X_B1" in win.design.components

    win.close()
