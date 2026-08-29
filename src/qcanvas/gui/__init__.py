"""The QCanvas desktop viewer (ships with the default install)."""

from __future__ import annotations

import matplotlib

# Must be set before any matplotlib pyplot / backend import under Qt.
matplotlib.use("QtAgg")

from qcanvas.gui.main_window import MainWindow


def _is_in_ipython() -> bool:
    """Return True if executing inside an interactive IPython/Jupyter kernel."""
    try:
        from IPython import get_ipython

        return get_ipython() is not None
    except Exception:
        return False


def _enable_ipython_gui() -> None:
    """Hook Qt event processing into the active IPython/Jupyter loop if available."""
    try:
        from IPython import get_ipython

        ip = get_ipython()
        if ip is not None:
            for gui_backend in ("qt6", "qt"):
                try:
                    ip.enable_gui(gui_backend)
                    break
                except Exception:
                    pass
    except Exception:
        pass


def launch(design=None) -> MainWindow:
    """Create and show a :class:`MainWindow` for ``design`` non-blockingly.

    In interactive environments like Jupyter / IPython, this hooks the Qt event
    loop so cell execution continues immediately while the GUI stays open as a live dashboard.
    """
    _enable_ipython_gui()
    from PySide6.QtWidgets import QApplication

    QApplication.instance() or QApplication([])
    window = MainWindow(design=design)
    window.show()
    return window


def run(design=None) -> None:
    """Launch the viewer and enter the Qt event loop.

    If run inside an interactive IPython/Jupyter session, this automatically delegates
    to non-blocking mode (:func:`launch`) to avoid freezing the notebook kernel.
    In standard standalone Python scripts, it blocks until the window is closed.
    """
    _enable_ipython_gui()
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    window = MainWindow(design=design)
    window.show()

    if not _is_in_ipython():
        app.exec()


__all__ = ["MainWindow", "launch", "run"]
