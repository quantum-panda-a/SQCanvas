"""Unit tests for Python script code generation, script loading with diagnostics, and live hot-reload."""

import os
import time
from pathlib import Path
import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

import sqcanvas
from sqcanvas.codegen import (
    ScriptLoadError,
    export_python_script,
    generate_python_script,
    load_design_from_script,
)
from sqcanvas.components import ChargeClaw, CrossTransmon, DualPadTransmon, Launchpad
from sqcanvas.designs.design_planar import PlanarDesign
from sqcanvas.gui.main_window import MainWindow
from sqcanvas.gui.watcher import ScriptWatcher


@pytest.fixture(scope="session")
def qapp():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_python_codegen_empty_and_populated(tmp_path):
    """Test Python script code generation for both empty and multi-component designs."""
    # 1. Empty design
    empty_design = PlanarDesign()
    code_empty = generate_python_script(empty_design)
    assert "def build_design() -> PlanarDesign:" in code_empty
    assert "design = PlanarDesign()" in code_empty
    assert 'if __name__ == "__main__":' in code_empty

    # 2. Populated design with delta options
    design = PlanarDesign()
    DualPadTransmon(
        design,
        "Q1",
        options={"pos_x": "-1000um", "pos_y": "200um", "pad_width": "500um"},
    )
    ChargeClaw(
        design,
        "claw_1",
        options={"pos_x": "-1000um", "pos_y": "800um", "orientation": "90"},
    )

    code = generate_python_script(design)
    assert "from sqcanvas.components import (" in code
    assert "ChargeClaw," in code
    assert "DualPadTransmon," in code
    assert "name='Q1'" in code
    assert "'pos_x': '-1000um'" in code
    assert "'pad_width': '500um'" in code
    assert "name='claw_1'" in code
    assert "'orientation': '90'" in code

    # Save to file
    script_file = tmp_path / "test_chip.py"
    saved_path = export_python_script(design, script_file)
    assert saved_path.exists()
    assert saved_path.read_text(encoding="utf-8") == code


def test_script_loader_functional_and_global_style(tmp_path):
    """Test executing and loading designs from both functional and global variable style scripts."""
    # 1. Functional style
    func_script = tmp_path / "functional_chip.py"
    func_script.write_text(
        """
from sqcanvas.designs import PlanarDesign
from sqcanvas.components import DualPadTransmon, Launchpad

def build_design():
    d = PlanarDesign()
    DualPadTransmon(d, "Q_main", options={"pos_x": "0.0um", "pos_y": "0.0um", "pad_width": "420um"})
    Launchpad(d, "port1", options={"pos_x": "-2000um", "pos_y": "1000um"})
    return d
""",
        encoding="utf-8",
    )

    design1 = load_design_from_script(func_script)
    assert isinstance(design1, PlanarDesign)
    assert len(design1.components) == 2
    assert "Q_main" in design1.components
    assert "port1" in design1.components
    assert design1.components["Q_main"].options["pad_width"] == 420.0

    # 2. Global variable style
    global_script = tmp_path / "global_chip.py"
    global_script.write_text(
        """
from sqcanvas.designs import PlanarDesign
from sqcanvas.components import CrossTransmon

design = PlanarDesign()
CrossTransmon(design, "X1", options={"pos_x": "500um", "pos_y": "-500um"})
""",
        encoding="utf-8",
    )

    design2 = load_design_from_script(global_script)
    assert isinstance(design2, PlanarDesign)
    assert len(design2.components) == 1
    assert "X1" in design2.components


def test_script_loader_diagnostics_and_errors(tmp_path):
    """Test precise error diagnostics on broken or missing scripts."""
    # 1. Non-existent file
    with pytest.raises(ScriptLoadError) as exc_info:
        load_design_from_script(tmp_path / "non_existent.py")
    assert exc_info.value.error_type == "FileNotFoundError"

    # 2. Syntax error
    syntax_err_file = tmp_path / "broken_syntax.py"
    syntax_err_file.write_text(
        """
from sqcanvas.designs import PlanarDesign

def build_design():
    design = PlanarDesign(
    # Missing closing parenthesis!
""",
        encoding="utf-8",
    )

    with pytest.raises(ScriptLoadError) as exc_info:
        load_design_from_script(syntax_err_file)
    err = exc_info.value
    assert err.error_type == "SyntaxError"
    assert err.line_number is not None
    report = err.format_diagnostic_report()
    assert "SyntaxError" in report
    assert "broken_syntax.py" in report

    # 3. Runtime error inside factory
    runtime_err_file = tmp_path / "broken_runtime.py"
    runtime_err_file.write_text(
        """
from sqcanvas.designs import PlanarDesign

def build_design():
    d = PlanarDesign()
    raise ValueError("Invalid qubit parameter configured!")
""",
        encoding="utf-8",
    )

    with pytest.raises(ScriptLoadError) as exc_info:
        load_design_from_script(runtime_err_file)
    err2 = exc_info.value
    assert "ValueError" in err2.error_type
    assert "Invalid qubit parameter" in err2.message

    # 4. No design found
    empty_file = tmp_path / "no_design.py"
    empty_file.write_text("x = 42\nprint('hello')\n", encoding="utf-8")
    with pytest.raises(ScriptLoadError) as exc_info:
        load_design_from_script(empty_file)
    assert exc_info.value.error_type == "DesignNotFoundError"


def test_top_level_helpers_and_aliases(tmp_path):
    """Test top-level sqcanvas.to_python and sqcanvas.load_script."""
    design = PlanarDesign()
    DualPadTransmon(design, "Q1")

    py_str = sqcanvas.to_python(design)
    assert "DualPadTransmon" in py_str

    script_path = tmp_path / "alias_test.py"
    sqcanvas.export_python_script(design, script_path)

    reloaded = sqcanvas.load_script(script_path)
    assert "Q1" in reloaded.components


def test_script_watcher_live_reload(tmp_path, qapp):
    """Test ScriptWatcher detecting file modification events."""
    test_file = tmp_path / "watched_script.py"
    test_file.write_text("# Initial", encoding="utf-8")

    watcher = ScriptWatcher(debounce_ms=50)
    received_paths = []
    watcher.file_modified.connect(lambda p: received_paths.append(p))

    watcher.watch(test_file)
    assert watcher.is_watching is True
    assert watcher.active_path == test_file.resolve()

    # Modify file
    time.sleep(0.02)
    test_file.write_text("# Modified 1", encoding="utf-8")

    # Process Qt event loop for debounce timer
    for _ in range(15):
        time.sleep(0.02)
        QCoreApplication.processEvents()

    assert len(received_paths) >= 1
    assert received_paths[0] == test_file.resolve()

    watcher.unwatch()
    assert watcher.is_watching is False


def test_main_window_open_save_and_hot_reload(tmp_path, qapp):
    """Test MainWindow script open, save, window title, and hot reload workflows."""
    win = MainWindow(design=None)
    assert win.windowTitle() == "SQCanvas Viewer"

    # 1. Place a component and save script
    DualPadTransmon(win.design, "Q1", options={"pos_x": "100um", "pos_y": "200um"})
    script_path = tmp_path / "my_gui_saved.py"
    win.save_python_script(filepath=script_path)

    assert script_path.exists()
    assert win._active_script_path == script_path.resolve()
    assert "my_gui_saved.py" in win.windowTitle()

    # 2. Reset design
    win.new_design()
    assert len(win.design.components) == 0
    assert win._active_script_path is None
    assert win.windowTitle() == "SQCanvas Viewer"

    # 3. Open saved script
    win.open_python_script(filepath=script_path)
    assert len(win.design.components) == 1
    assert "Q1" in win.design.components
    assert win._active_script_path == script_path.resolve()

    # 4. Simulate external edit and hot-reload
    script_path.write_text(
        """
from sqcanvas.designs import PlanarDesign
from sqcanvas.components import CrossTransmon, ChargeClaw

def build_design():
    d = PlanarDesign()
    CrossTransmon(d, "X_reload", options={"pos_x": "0um", "pos_y": "0um"})
    ChargeClaw(d, "claw_reload", options={"pos_x": "0um", "pos_y": "500um"})
    return d
""",
        encoding="utf-8",
    )

    # Trigger hot-reload slot
    win._on_file_watcher_modified(script_path.resolve())
    assert len(win.design.components) == 2
    assert "X_reload" in win.design.components
    assert "claw_reload" in win.design.components
    assert "Reloaded" in win.status_dot.text()

    win.close()
