"""The QCanvas desktop viewer (ships with the default install)."""

from __future__ import annotations

import matplotlib

# Must be set before any matplotlib pyplot / backend import under Qt.
matplotlib.use("QtAgg")

from qcanvas.gui.main_window import MainWindow


def launch(design=None) -> MainWindow:
    """Create and show a :class:`MainWindow` for ``design``."""
    from PySide6.QtWidgets import QApplication

    QApplication.instance() or QApplication([])
    window = MainWindow(design=design)
    window.show()
    return window


def run(design=None) -> None:
    """Blocking entry point: launch the viewer and enter the Qt event loop."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    window = MainWindow(design=design)
    window.show()
    app.exec()


__all__ = ["MainWindow", "launch", "run"]
