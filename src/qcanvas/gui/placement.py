"""Interactive CAD placement controller and ghost preview engine for QCanvas."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, Rectangle
from matplotlib.text import Text

from qcanvas.components.registry import ComponentMeta

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from qcanvas.components.base import Component
    from qcanvas.designs.design_base import Design


class PlacementController:
    """Controls interactive component placement with real-time CAD ghost preview and grid snapping."""

    def __init__(
        self,
        figure: Figure,
        ax: Axes,
        *,
        grid_snap: float = 50.0,
    ) -> None:
        self.figure = figure
        self.ax = ax
        self.grid_snap: float = grid_snap
        self.active_meta: ComponentMeta | None = None
        self.rotation: float = 0.0  # Degrees

        self._artists: list[Any] = []
        self._last_raw_coord: tuple[float, float] | None = None
        self._last_snapped_coord: tuple[float, float] | None = None

    @property
    def is_active(self) -> bool:
        return self.active_meta is not None

    def set_axes(self, ax: Axes) -> None:
        """Update target axes after figure redraw."""
        self.clear_ghost()
        self.ax = ax

    def arm(self, meta: ComponentMeta, initial_rotation: float = 0.0) -> None:
        """Arm placement mode for the specified component."""
        self.clear_ghost()
        self.active_meta = meta
        self.rotation = initial_rotation
        self._last_raw_coord = None
        self._last_snapped_coord = None

    def disarm(self) -> None:
        """Exit placement mode and clear all temporary ghost indicators."""
        self.clear_ghost()
        self.active_meta = None
        self.rotation = 0.0
        self._last_raw_coord = None
        self._last_snapped_coord = None

    def set_grid_snap(self, snap_um: float) -> None:
        """Set grid snap step in micrometres (0.0 means snap disabled)."""
        self.grid_snap = max(0.0, snap_um)
        if self._last_raw_coord and self.is_active:
            self.handle_motion(*self._last_raw_coord)

    def snap_coord(self, x: float, y: float) -> tuple[float, float]:
        """Snap physical coordinate (x, y) to the active grid increment."""
        if self.grid_snap > 0.0:
            x_snap = round(x / self.grid_snap) * self.grid_snap
            y_snap = round(y / self.grid_snap) * self.grid_snap
            return (x_snap, y_snap)
        return (x, y)

    def rotate_cw(self) -> float:
        """Rotate pending component 90 degrees clockwise."""
        self.rotation = (self.rotation - 90.0) % 360.0
        if self._last_raw_coord and self.is_active:
            self.handle_motion(*self._last_raw_coord)
        return self.rotation

    def rotate_ccw(self) -> float:
        """Rotate pending component 90 degrees counter-clockwise."""
        self.rotation = (self.rotation + 90.0) % 360.0
        if self._last_raw_coord and self.is_active:
            self.handle_motion(*self._last_raw_coord)
        return self.rotation

    def get_next_unique_name(self, design: Design, meta: ComponentMeta) -> str:
        """Generate a clean, conflict-free name for the new component."""
        prefix = meta.default_prefix
        existing_names = set(design.components.keys()) if hasattr(design, "components") else set()

        if prefix.endswith("_"):
            idx = 1
            while f"{prefix}{idx}" in existing_names:
                idx += 1
            return f"{prefix}{idx}"
        else:
            # E.g. "Q1", "Q2"
            idx = 1
            while f"{prefix}{idx}" in existing_names:
                idx += 1
            return f"{prefix}{idx}"

    def handle_motion(self, x: float | None, y: float | None) -> tuple[float, float] | None:
        """Update ghost preview at mouse coordinate."""
        if not self.is_active or x is None or y is None:
            self.clear_ghost()
            return None

        self._last_raw_coord = (x, y)
        x_snap, y_snap = self.snap_coord(x, y)
        self._last_snapped_coord = (x_snap, y_snap)

        self._render_ghost(x_snap, y_snap)
        return (x_snap, y_snap)

    def handle_click(self, design: Design, x: float, y: float) -> Component | None:
        """Place the armed component on the design at the clicked (snapped) coordinate."""
        if not self.is_active or self.active_meta is None:
            return None

        x_snap, y_snap = self.snap_coord(x, y)
        comp_name = self.get_next_unique_name(design, self.active_meta)

        rot_val = int(self.rotation) if self.rotation.is_integer() else self.rotation
        options: dict[str, Any] = {
            "pos_x": f"{x_snap:.1f}um",
            "pos_y": f"{y_snap:.1f}um",
            "orientation": str(rot_val),
        }

        # Clear ghost before building to prevent visual artifacts
        self.clear_ghost()

        # Instantiate component into design
        comp = self.active_meta.cls(design, name=comp_name, options=options)
        return comp

    def clear_ghost(self) -> None:
        """Remove all temporary preview artists from the axes."""
        for artist in self._artists:
            try:
                artist.remove()
            except Exception:  # noqa: BLE001
                pass
        self._artists.clear()
        if self.figure.canvas:
            self.figure.canvas.draw_idle()

    def _render_ghost(self, x: float, y: float) -> None:
        """Render high-contrast CAD ghost preview indicator on the axes."""
        for artist in self._artists:
            try:
                artist.remove()
            except Exception:  # noqa: BLE001
                pass
        self._artists.clear()

        if self.active_meta is None:
            return

        # Adaptive sizing based on current viewport span
        try:
            x_min, x_max = self.ax.get_xlim()
            y_min, y_max = self.ax.get_ylim()
            span = max(abs(x_max - x_min), abs(y_max - y_min))
        except Exception:
            span = 4000.0

        marker_size = max(40.0, min(160.0, span * 0.04))
        box_w = max(200.0, min(500.0, span * 0.12))
        box_h = max(120.0, min(300.0, span * 0.08))

        # 1. Center Crosshair Reticle (+)
        line_h = Line2D(
            [x - marker_size, x + marker_size],
            [y, y],
            color="#00D2D3",
            linewidth=1.5,
            linestyle="-",
            alpha=0.9,
            zorder=850,
        )
        line_v = Line2D(
            [x, x],
            [y - marker_size, y + marker_size],
            color="#00D2D3",
            linewidth=1.5,
            linestyle="-",
            alpha=0.9,
            zorder=850,
        )
        self.ax.add_line(line_h)
        self.ax.add_line(line_v)
        self._artists.extend([line_h, line_v])

        # 2. Orientation Arrow
        rad = math.radians(self.rotation)
        arrow_len = marker_size * 1.5
        dx = arrow_len * math.cos(rad)
        dy = arrow_len * math.sin(rad)
        arrow = FancyArrowPatch(
            (x, y),
            (x + dx, y + dy),
            arrowstyle="-|>",
            mutation_scale=14,
            color="#FF9F43",
            linewidth=2.0,
            alpha=0.95,
            zorder=860,
        )
        self.ax.add_patch(arrow)
        self._artists.append(arrow)

        # 3. Translucent Bounding Placeholder Box
        # Rotate rectangle bounding box
        rect_patch = Rectangle(
            (x - box_w / 2.0, y - box_h / 2.0),
            box_w,
            box_h,
            facecolor=(0.0, 0.82, 0.83, 0.12),
            edgecolor="#00D2D3",
            linestyle="--",
            linewidth=1.2,
            zorder=840,
        )
        # Apply rotation transform around center
        import matplotlib.transforms as mtransforms

        t = (
            mtransforms.Affine2D().rotate_deg_around(x, y, self.rotation)
            + self.ax.transData
        )
        rect_patch.set_transform(t)
        self.ax.add_patch(rect_patch)
        self._artists.append(rect_patch)

        # 4. Floating HUD Tag Callout
        info_text = (
            f"  {self.active_meta.icon} {self.active_meta.display_name}\n"
            f"  Pos: ({x:+.1f}, {y:+.1f}) µm  ·  Rot: {self.rotation:.0f}°\n"
            f"  [Click] Place  ·  [R] Rotate  ·  [Esc] Cancel  "
        )
        offset_y = box_h * 0.7 + marker_size * 0.5
        tag = Text(
            x,
            y + offset_y,
            info_text,
            color="#FFFFFF",
            fontsize=9,
            fontfamily="sans-serif",
            fontweight="semibold",
            ha="center",
            va="bottom",
            zorder=870,
            bbox=dict(
                boxstyle="round,pad=0.4",
                facecolor="#161B22",
                edgecolor="#00ADB5",
                alpha=0.92,
                linewidth=1.0,
            ),
        )
        self.ax.add_artist(tag)
        self._artists.append(tag)

        self.figure.canvas.draw_idle()
