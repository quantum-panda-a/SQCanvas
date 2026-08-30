"""A matplotlib canvas embedded in a Qt widget with dark CAD navigation and highlighting."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.text import Text
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSizePolicy

from qcanvas.config import get_theme
from qcanvas.gui.interaction import CanvasInteraction
from qcanvas.gui.ruler import CanvasRuler
from qcanvas.gui.theme import Palette

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
        theme: str = "cyber",
    ) -> None:
        self.current_theme: str = theme
        theme_cfg = get_theme(self.current_theme)

        fig = Figure(figsize=(width, height), dpi=dpi, layout="constrained")
        fig.patch.set_facecolor(theme_cfg.canvas_bg)

        try:
            engine = fig.get_layout_engine()
            if engine is not None:
                engine.set(h_pad=0.04, w_pad=0.04, rect=(0.01, 0.01, 0.99, 0.99))
        except Exception:
            pass

        super().__init__(fig)
        self.setParent(parent)

        self.axes = self.figure.add_subplot(111)
        self.axes.set_facecolor(theme_cfg.canvas_bg)

        # Qt Focus, Mouse Tracking and KLayout-style Crosshair Cursor
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Overlay annotations
        self._highlights: list[Artist] = []
        self._labels: list[Artist] = []
        self._scale_bar_artists: list[Artist] = []
        self.labels_visible: bool = False
        self.scale_bar_visible: bool = True
        self.crosshair_visible: bool = True

        # KLayout-style CAD Full-Span Crosshair
        self._crosshair_h = Line2D(
            [0, 0], [0, 0],
            color=theme_cfg.crosshair_color,
            linewidth=0.75,
            linestyle="--",
            alpha=0.6,
            zorder=700,
            visible=False,
        )
        self._crosshair_v = Line2D(
            [0, 0], [0, 0],
            color=theme_cfg.crosshair_color,
            linewidth=0.75,
            linestyle="--",
            alpha=0.6,
            zorder=700,
            visible=False,
        )
        self.axes.add_line(self._crosshair_h)
        self.axes.add_line(self._crosshair_v)

        # CAD Interaction Controller
        self.interaction = CanvasInteraction(self.figure, self.axes)

        # CAD Distance Ruler Tool
        self.ruler = CanvasRuler(self.figure, self.axes)

    def set_theme(self, theme_name: str) -> None:
        """Switch active color palette theme and update canvas appearance."""
        theme_cfg = get_theme(theme_name)
        self.current_theme = theme_cfg.key

        self.figure.patch.set_facecolor(theme_cfg.canvas_bg)
        self.axes.set_facecolor(theme_cfg.canvas_bg)

        self._crosshair_h.set_color(theme_cfg.crosshair_color)
        self._crosshair_v.set_color(theme_cfg.crosshair_color)

        self.update_scale_bar()
        self.draw_idle()

    def set_interaction_callbacks(
        self,
        *,
        on_hover=None,
        on_click_point=None,
        on_autoscale=None,
        on_shortcut=None,
    ) -> None:
        """Bind high-level UI callbacks to canvas interactions with ruler and crosshair integration."""
        def _wrapped_hover(x: float | None, y: float | None):
            self._update_crosshair(x, y)
            if self.ruler.active:
                self.ruler.handle_motion(x, y)
            if on_hover:
                on_hover(x, y)

        def _wrapped_click(x: float, y: float):
            if self.ruler.active:
                status = self.ruler.handle_click(x, y)
                if on_shortcut and status:
                    on_shortcut(f"ruler_status:{status}")
                return
            if on_click_point:
                on_click_point(x, y)

        self.interaction.on_hover = _wrapped_hover
        self.interaction.on_click_point = _wrapped_click
        self.interaction.on_autoscale = on_autoscale
        self.interaction.on_shortcut = on_shortcut

    def refresh_interaction_axes(self) -> None:
        """Inform interaction controller and ruler of new/cleared axes."""
        theme_cfg = get_theme(self.current_theme)
        self.axes.set_facecolor(theme_cfg.canvas_bg)

        # Re-attach crosshair lines if axes cleared
        if self._crosshair_h not in self.axes.lines:
            self.axes.add_line(self._crosshair_h)
        if self._crosshair_v not in self.axes.lines:
            self.axes.add_line(self._crosshair_v)

        self.interaction.set_axes(self.axes)
        self.ruler.set_axes(self.axes)
        self.update_scale_bar()

    # ----------------------------------------------------------- CAD Crosshair Cursor
    def _update_crosshair(self, x: float | None, y: float | None) -> None:
        """Update KLayout-style full-span reticle cursor across the axes."""
        if not self.crosshair_visible or x is None or y is None:
            if self._crosshair_h.get_visible() or self._crosshair_v.get_visible():
                self._crosshair_h.set_visible(False)
                self._crosshair_v.set_visible(False)
                self.draw_idle()
            return

        try:
            x_min, x_max = self.axes.get_xlim()
            y_min, y_max = self.axes.get_ylim()
        except Exception:  # noqa: BLE001
            return

        self._crosshair_h.set_data([x_min, x_max], [y, y])
        self._crosshair_h.set_visible(True)

        self._crosshair_v.set_data([x, x], [y_min, y_max])
        self._crosshair_v.set_visible(True)

        self.draw_idle()

    # ----------------------------------------------------------- Dynamic Scale Bar
    def set_scale_bar_visible(self, visible: bool) -> None:
        """Toggle physical engineering scale bar visibility."""
        self.scale_bar_visible = visible
        self.update_scale_bar()
        self.draw_idle()

    def update_scale_bar(self) -> None:
        """Render or update dynamic physical engineering scale bar with active theme colors."""
        for artist in self._scale_bar_artists:
            try:
                artist.remove()
            except Exception:  # noqa: BLE001
                pass
        self._scale_bar_artists.clear()

        if not self.scale_bar_visible:
            return

        try:
            x_min, x_max = self.axes.get_xlim()
            y_min, y_max = self.axes.get_ylim()
        except Exception:  # noqa: BLE001
            return

        span_x = abs(x_max - x_min)
        span_y = abs(y_max - y_min)
        if span_x <= 0 or span_y <= 0:
            return

        # Target bar width is ~18% of viewport span
        target_len = span_x * 0.18

        # Calculate standard step (1, 2, 5 * 10^k)
        exponent = math.floor(math.log10(target_len))
        fraction = target_len / (10**exponent)
        if fraction < 1.5:
            step = 1.0
        elif fraction < 3.5:
            step = 2.0
        elif fraction < 7.5:
            step = 5.0
        else:
            step = 10.0
        bar_len = step * (10**exponent)

        # Format label with engineering units (nm, um, mm)
        if bar_len >= 1000.0:
            label_text = f"{bar_len / 1000.0:g} mm"
        elif bar_len < 1.0:
            label_text = f"{bar_len * 1000.0:g} nm"
        else:
            label_text = f"{bar_len:g} μm"

        # Position in bottom right corner with margin
        margin_x = span_x * 0.04
        margin_y = span_y * 0.04
        bar_x1 = x_max - margin_x
        bar_x0 = bar_x1 - bar_len
        bar_y = y_min + margin_y
        tick_h = span_y * 0.015

        theme_cfg = get_theme(self.current_theme)
        color = theme_cfg.scale_color
        bg_color = Palette.BG_DARKEST if theme_cfg.is_dark else "#F1F5F9"
        text_color = "#FFFFFF" if theme_cfg.is_dark else "#1E293B"

        # Horizontal bar
        bar_line = Line2D([bar_x0, bar_x1], [bar_y, bar_y], color=color, linewidth=2.0, zorder=800)
        # Left tick
        tick_l = Line2D([bar_x0, bar_x0], [bar_y - tick_h / 2, bar_y + tick_h / 2], color=color, linewidth=2.0, zorder=800)
        # Right tick
        tick_r = Line2D([bar_x1, bar_x1], [bar_y - tick_h / 2, bar_y + tick_h / 2], color=color, linewidth=2.0, zorder=800)

        # Text label badge
        txt = Text(
            (bar_x0 + bar_x1) / 2.0,
            bar_y + tick_h * 1.2,
            f" {label_text} ",
            color=text_color,
            fontsize=8,
            fontweight="bold",
            ha="center",
            va="bottom",
            bbox={
                "boxstyle": "round,pad=0.2",
                "facecolor": bg_color,
                "edgecolor": color,
                "alpha": 0.88,
                "lw": 0.9,
            },
            zorder=801,
        )

        self.axes.add_line(bar_line)
        self.axes.add_line(tick_l)
        self.axes.add_line(tick_r)
        self.axes.add_artist(txt)
        self._scale_bar_artists.extend([bar_line, tick_l, tick_r, txt])

    # ----------------------------------------------------------- Highlighting
    def clear_highlight(self) -> None:
        """Remove any active component highlight overlays."""
        for artist in self._highlights:
            try:
                artist.remove()
            except Exception:  # noqa: BLE001
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

        theme_cfg = get_theme(self.current_theme)
        accent = theme_cfg.crosshair_color

        # Bounding box highlight with glowing accent
        rect = Rectangle(
            (box_x, box_y),
            box_w,
            box_h,
            facecolor=(0.0, 0.82, 0.83, 0.12) if theme_cfg.is_dark else (0.12, 0.47, 0.71, 0.12),
            edgecolor=accent,
            linestyle="-",
            linewidth=1.8,
            zorder=500,
        )
        self.axes.add_patch(rect)
        self._highlights.append(rect)

        # Label tag above bounding box
        txt = self.axes.text(
            box_x,
            box_y + box_h + pad_y * 0.4,
            f" {name} ",
            color=Palette.BG_DARKEST if theme_cfg.is_dark else "#FFFFFF",
            fontsize=9,
            fontweight="bold",
            bbox={
                "boxstyle": "round,pad=0.25",
                "facecolor": accent,
                "edgecolor": "none",
                "alpha": 0.95,
            },
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
            except Exception:  # noqa: BLE001
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
                    color=Palette.ACCENT_AMBER,
                    fontsize=9,
                    fontweight="bold",
                    ha="center",
                    va="center",
                    bbox={
                        "boxstyle": "round,pad=0.25",
                        "facecolor": Palette.BG_SURFACE,
                        "edgecolor": Palette.ACCENT_AMBER,
                        "alpha": 0.92,
                        "lw": 1.0,
                    },
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
        self.update_scale_bar()
        self.draw_idle()


__all__ = ["MplCanvas"]
