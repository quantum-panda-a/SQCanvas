"""A matplotlib canvas embedded in a Qt widget."""

from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class MplCanvas(FigureCanvas):
    """A matplotlib ``Figure`` shown as a Qt widget."""

    def __init__(self, parent=None, width: float = 6.0, height: float = 5.0, dpi: int = 100) -> None:
        super().__init__(Figure(figsize=(width, height), dpi=dpi))
        self.axes = self.figure.add_subplot(111)
        self.setParent(parent)


__all__ = ["MplCanvas", "NavigationToolbar"]
