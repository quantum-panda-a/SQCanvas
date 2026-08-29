"""A matplotlib canvas embedded in a Qt widget with CAD navigation and highlighting."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSizePolicy

from qcanvas.gui.interaction import CanvasInteraction

if TYPE_CHECKING:
    from matplotlib.artist import Artist


class MplCanvas(FigureCanvas):
    """A matplotlib ``Figure`` shown as a Qt widget with CAD interaction."""

    def __init__(
        self,
        parent: Any = None,
        width: float = 7.0,
        height: float = 6.0,
        dpi: int = 100,
    ) -> None:
        fig = Figure(figsize=(width, height), dpi=dpi, layout="constrained")
        try:
            engine = fig.get_layout_engine()
            if engine is not None:
                engine.set(h_pad=0.08, w_pad=0.08, rect=(0.02, 0.02, 0.96, 0.96))
        except Exception:
            pass
        super().__init__(fig)
        self.setParent(parent)

        self.axes = self.figure.add_subplot(111)

        # Qt Focus and Mouse Tracking for fluid interactions
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Overlay annotations
        self._highlights: list[Artist] = []
        self._labels: list[Artist] = []
        self.labels_visible: bool = False

        # CAD Interaction Controller
        self.interaction = CanvasInteraction(self.figure, self.axes)

    def set_interaction_callbacks(
        self,
        *,
        on_hover=None,
        on_click_point=None,
        on_autoscale=None,
        on_shortcut=None,
    ) -> None:
        """Bind high-level UI callbacks to canvas interactions."""
        self.interaction.on_hover = on_hover
        self.interaction.on_click_point = on_click_point
        self.interaction.on_autoscale = on_autoscale
        self.interaction.on_shortcut = on_shortcut

    def refresh_interaction_axes(self) -> None:
        """Inform interaction controller of new/cleared axes."""
        self.interaction.set_axes(self.axes)

    # ----------------------------------------------------------- Highlighting
    def clear_highlight(self) -> None:
        """Remove any active component highlight overlays."""
        for artist in self._highlights:
            try:
                artist.remove()
            except Exception:
                pass
        self._highlights.clear()
        self.draw_idle()

    def highlight_component(
        self,
        name: str,
        bounds: tuple[float, float, float, float] | None,
    ) -> None:
        """Draw an overlay rectangle and tag for the selected component."""
        self.clear_highlight()
        if bounds is None:
            return

        min_x, min_y, max_x, max_y = bounds
        pad_x = max((max_x - min_x) * 0.05, 5.0)
        pad_y = max((max_y - min_y) * 0.05, 5.0)

        box_x = min_x - pad_x
        box_y = min_y - pad_y
        box_w = (max_x - min_x) + 2 * pad_x
        box_h = (max_y - min_y) + 2 * pad_y

        # Bounding box highlight
        rect = Rectangle(
            (box_x, box_y),
            box_w,
            box_h,
            facecolor=(0.16, 0.62, 0.56, 0.12),
            edgecolor="#2a9d8f",
            linestyle="-",
            linewidth=1.5,
            zorder=500,
        )
        self.axes.add_patch(rect)
        self._highlights.append(rect)

        # Label tag above bounding box
        txt = self.axes.text(
            box_x,
            box_y + box_h + pad_y * 0.5,
            f" {name} ",
            color="white",
            fontsize=9,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#2a9d8f", edgecolor="none", alpha=0.9),
            zorder=501,
        )
        self._highlights.append(txt)
        self.draw_idle()

    # -------------------------------------------------------------- All labels
    def toggle_all_labels(self, component_bounds: dict[str, tuple[float, float, float, float]]) -> bool:
        """Toggle persistent labels on all components. Returns new state."""
        self.labels_visible = not self.labels_visible

        # Clear existing labels
        for artist in self._labels:
            try:
                artist.remove()
            except Exception:
                pass
        self._labels.clear()

        if self.labels_visible:
            for name, (min_x, min_y, max_x, max_y) in component_bounds.items():
                cx = (min_x + max_x) / 2.0
                cy = (min_y + max_y) / 2.0
                txt = self.axes.text(
                    cx,
                    cy,
                    name,
                    color="#e76f51",
                    fontsize=9,
                    fontweight="bold",
                    ha="center",
                    va="center",
                    bbox=dict(boxstyle="round,pad=0.25", facecolor="#ffffff", edgecolor="#e76f51", alpha=0.85, lw=1.0),
                    zorder=450,
                )
                self._labels.append(txt)

        self.draw_idle()
        return self.labels_visible

    # ------------------------------------------------------------- View limits
    def zoom_to_rect(
        self,
        bounds: tuple[float, float, float, float],
        margin_ratio: float = 0.1,
    ) -> None:
        """Zoom view limits to comfortably frame `(min_x, min_y, max_x, max_y)`."""
        min_x, min_y, max_x, max_y = bounds
        span_x = max(max_x - min_x, 10.0)
        span_y = max(max_y - min_y, 10.0)

        # Equal aspect ratio fit
        center_x = (min_x + max_x) / 2.0
        center_y = (min_y + max_y) / 2.0
        max_span = max(span_x, span_y) * (1.0 + margin_ratio)

        self.axes.set_xlim(center_x - max_span / 2.0, center_x + max_span / 2.0)
        self.axes.set_ylim(center_y - max_span / 2.0, center_y + max_span / 2.0)
        self.draw_idle()


__all__ = ["MplCanvas"]
