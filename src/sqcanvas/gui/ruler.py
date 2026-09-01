"""Interactive CAD distance measurement tool for SQCanvas."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch

from sqcanvas.gui.theme import Palette

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure


class CanvasRuler:
    """CAD ruler overlay for interactive point-to-point distance measurement."""

    def __init__(self, figure: Figure, ax: Axes, unit: str = "um") -> None:
        self.figure = figure
        self.ax = ax
        self.unit = unit
        self.active: bool = False

        self._start_pt: tuple[float, float] | None = None
        self._artists: list[Any] = []

    def set_axes(self, ax: Axes) -> None:
        self.clear()
        self.ax = ax

    def activate(self) -> None:
        """Activate ruler measurement mode."""
        self.clear()
        self.active = True

    def deactivate(self) -> None:
        """Deactivate ruler measurement mode."""
        self.clear()
        self.active = False

    def toggle(self) -> bool:
        """Toggle active state and return new state."""
        if self.active:
            self.deactivate()
        else:
            self.activate()
        return self.active

    def clear(self) -> None:
        """Clear all active measurement artists."""
        for artist in self._artists:
            try:
                artist.remove()
            except Exception:  # noqa: BLE001
                pass
        self._artists.clear()
        self._start_pt = None
        if self.figure.canvas:
            self.figure.canvas.draw_idle()

    def handle_click(self, x: float, y: float) -> str | None:
        """Handle canvas click in ruler mode. Returns status text if measurement completed."""
        if not self.active:
            return None

        if self._start_pt is None:
            # First point selected
            self._start_pt = (x, y)
            self._render_preview(x, y, is_final=False)
            return f"Ruler start: ({x:+.2f}, {y:+.2f}) {self.unit} — Click second point to measure"
        else:
            # Second point selected -> finalize measurement
            x0, y0 = self._start_pt
            dx = abs(x - x0)
            dy = abs(y - y0)
            dist = math.hypot(x - x0, y - y0)
            self._render_preview(x, y, is_final=True)
            self._start_pt = None  # Reset for next measurement
            return f"Measured: ΔX = {dx:.2f} {self.unit}, ΔY = {dy:.2f} {self.unit}, Dist = {dist:.2f} {self.unit}"

    def handle_motion(self, x: float | None, y: float | None) -> None:
        """Update live measurement line preview on mouse move."""
        if not self.active or self._start_pt is None or x is None or y is None:
            return
        self._render_preview(x, y, is_final=False)

    def _render_preview(self, x1: float, y1: float, is_final: bool = False) -> None:
        """Draw measurement line, guide projections, and dimension callout."""
        # Clear existing transient artists
        for artist in self._artists:
            try:
                artist.remove()
            except Exception:  # noqa: BLE001
                pass
        self._artists.clear()

        if self._start_pt is None:
            return

        x0, y0 = self._start_pt
        dx = x1 - x0
        dy = y1 - y0
        dist = math.hypot(dx, dy)
        mid_x = (x0 + x1) / 2.0
        mid_y = (y0 + y1) / 2.0

        line_color = Palette.ACCENT_CYAN if not is_final else Palette.ACCENT_AMBER
        badge_bg = Palette.BG_DARKEST

        # 1. Main dimension line with arrowheads
        arrow = FancyArrowPatch(
            (x0, y0),
            (x1, y1),
            arrowstyle="<->",
            mutation_scale=12,
            color=line_color,
            linewidth=1.8,
            linestyle="-",
            zorder=600,
        )
        self.ax.add_patch(arrow)
        self._artists.append(arrow)

        # 2. Start and end cross markers
        marker0 = Line2D([x0], [y0], marker="+", color=line_color, markersize=10, markeredgewidth=1.5, zorder=601)
        marker1 = Line2D([x1], [y1], marker="+", color=line_color, markersize=10, markeredgewidth=1.5, zorder=601)
        self.ax.add_line(marker0)
        self.ax.add_line(marker1)
        self._artists.extend([marker0, marker1])

        # 3. Orthogonal projection guides (ΔX and ΔY dashed lines)
        if abs(dx) > 1e-3 and abs(dy) > 1e-3:
            guidex = Line2D([x0, x1], [y0, y0], color=Palette.TEXT_MUTED, linestyle=":", linewidth=1.0, zorder=599)
            guidey = Line2D([x1, x1], [y0, y1], color=Palette.TEXT_MUTED, linestyle=":", linewidth=1.0, zorder=599)
            self.ax.add_line(guidex)
            self.ax.add_line(guidey)
            self._artists.extend([guidex, guidey])

        # 4. Dimension Callout Badge Text
        label_text = f" {dist:.2f} {self.unit}\n (ΔX: {abs(dx):.1f}, ΔY: {abs(dy):.1f}) "
        txt = self.ax.text(
            mid_x,
            mid_y,
            label_text,
            color=line_color,
            fontsize=8.5,
            fontweight="bold",
            ha="center",
            va="center",
            bbox={
                "boxstyle": "round,pad=0.3",
                "facecolor": badge_bg,
                "edgecolor": line_color,
                "alpha": 0.92,
                "lw": 1.2,
            },
            zorder=602,
        )
        self._artists.append(txt)
        self.figure.canvas.draw_idle()


__all__ = ["CanvasRuler"]
