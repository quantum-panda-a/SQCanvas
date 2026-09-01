"""CAD-style canvas interaction handlers for SQCanvas GUI."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from matplotlib.patches import Rectangle

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.backend_bases import Event, KeyEvent, MouseEvent
    from matplotlib.figure import Figure


class CanvasInteraction:
    """Provides CAD-style navigation and interaction on a matplotlib Figure.

    Interactions:
      - **Scroll wheel**: Smooth zoom centered at cursor's data coordinates.
      - **Left click drag**: Pan the viewport.
      - **Left click release (without drag)**: Click-to-select point dispatch.
      - **Right click drag**: Rubber-band rectangle box-zoom.
      - **Double click**: Reset/autoscale view.
      - **Mouse hover**: Emits real-time data coordinates (X, Y).
    """

    def __init__(
        self,
        figure: Figure,
        ax: Axes,
        *,
        scale_factor: float = 1.15,
        on_hover: Callable[[float | None, float | None], None] | None = None,
        on_click_point: Callable[[float, float], None] | None = None,
        on_autoscale: Callable[[], None] | None = None,
        on_shortcut: Callable[[str], None] | None = None,
    ) -> None:
        self.figure = figure
        self.ax = ax
        self.scale_factor = scale_factor

        self.on_hover = on_hover
        self.on_click_point = on_click_point
        self.on_autoscale = on_autoscale
        self.on_shortcut = on_shortcut

        # Pan state
        self._press_pix: tuple[float, float] | None = None
        self._press_lims: tuple[tuple[float, float], tuple[float, float]] | None = None
        self._is_dragging: bool = False
        self._drag_threshold_px: float = 4.0

        # Box zoom state
        self._box_start_data: tuple[float, float] | None = None
        self._box_start_pix: tuple[float, float] | None = None
        self._box_patch: Rectangle | None = None

        self._cids: list[int] = []
        self._connect()

    def _connect(self) -> None:
        canvas = self.figure.canvas
        self._cids.append(canvas.mpl_connect("scroll_event", self._on_scroll))
        self._cids.append(canvas.mpl_connect("button_press_event", self._on_press))
        self._cids.append(canvas.mpl_connect("motion_notify_event", self._on_motion))
        self._cids.append(canvas.mpl_connect("button_release_event", self._on_release))
        self._cids.append(canvas.mpl_connect("key_press_event", self._on_key_press))

    def disconnect(self) -> None:
        """Disconnect all matplotlib event listeners."""
        canvas = self.figure.canvas
        for cid in self._cids:
            try:
                canvas.mpl_disconnect(cid)
            except Exception:
                pass
        self._cids.clear()
        self._remove_box_patch()

    def set_axes(self, ax: Axes) -> None:
        """Update the target axes after redraw or figure clear."""
        self._remove_box_patch()
        self.ax = ax

    # ----------------------------------------------------------------- Zoom
    def _on_scroll(self, event: MouseEvent) -> None:
        """Zoom centered at cursor data coordinates."""
        if event.inaxes != self.ax or not hasattr(event, "step") or event.step == 0:
            return

        x_data, y_data = event.xdata, event.ydata
        if x_data is None or y_data is None:
            return

        factor = self.scale_factor if event.step > 0 else 1.0 / self.scale_factor
        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()

        new_xmin, new_xmax = self._compute_zoom_range(x_min, x_max, x_data, factor)
        new_ymin, new_ymax = self._compute_zoom_range(y_min, y_max, y_data, factor)

        self.ax.set_xlim(new_xmin, new_xmax)
        self.ax.set_ylim(new_ymin, new_ymax)
        self.figure.canvas.draw_idle()

    @staticmethod
    def _compute_zoom_range(
        current_min: float, current_max: float, center: float, scale_factor: float
    ) -> tuple[float, float]:
        """Calculate new axis range keeping `center` in the same relative position."""
        total_span = (current_max - current_min) / scale_factor
        offset_ratio = (center - current_min) / (current_max - current_min) if current_max != current_min else 0.5
        new_min = center - offset_ratio * total_span
        new_max = center + (1.0 - offset_ratio) * total_span
        return new_min, new_max

    # ----------------------------------------------------------------- Mouse Press
    def _on_press(self, event: MouseEvent) -> None:
        if event.inaxes != self.ax:
            return

        # Double click -> Autoscale
        if getattr(event, "dblclick", False):
            if self.on_autoscale:
                self.on_autoscale()
            return

        # Left button: prepare Pan
        if event.button == 1:
            self._press_pix = (event.x, event.y)
            self._press_lims = (self.ax.get_xlim(), self.ax.get_ylim())
            self._is_dragging = False

        # Right button: prepare Box Zoom
        elif event.button == 3 and event.xdata is not None and event.ydata is not None:
            self._box_start_data = (event.xdata, event.ydata)
            self._box_start_pix = (event.x, event.y)

    # ----------------------------------------------------------------- Mouse Motion
    def _on_motion(self, event: MouseEvent) -> None:
        # 1. Real-time hover coordinate readout
        if self.on_hover:
            if event.inaxes == self.ax and event.xdata is not None and event.ydata is not None:
                self.on_hover(event.xdata, event.ydata)
            else:
                self.on_hover(None, None)

        # 2. Pan handling (Left mouse held)
        if event.button == 1 and self._press_pix is not None and self._press_lims is not None:
            dx_px = event.x - self._press_pix[0]
            dy_px = event.y - self._press_pix[1]

            if not self._is_dragging:
                if (dx_px**2 + dy_px**2) ** 0.5 >= self._drag_threshold_px:
                    self._is_dragging = True

            if self._is_dragging:
                (x_min_orig, x_max_orig), (y_min_orig, y_max_orig) = self._press_lims
                bbox = self.ax.bbox
                if bbox.width > 0 and bbox.height > 0:
                    dx_data = dx_px * (x_max_orig - x_min_orig) / bbox.width
                    dy_data = dy_px * (y_max_orig - y_min_orig) / bbox.height

                    self.ax.set_xlim(x_min_orig - dx_data, x_max_orig - dx_data)
                    self.ax.set_ylim(y_min_orig - dy_data, y_max_orig - dy_data)
                    self.figure.canvas.draw_idle()

        # 3. Box zoom preview (Right mouse held)
        elif event.button == 3 and self._box_start_data is not None and event.xdata is not None and event.ydata is not None:
            x0, y0 = self._box_start_data
            x1, y1 = event.xdata, event.ydata
            box_x = min(x0, x1)
            box_y = min(y0, y1)
            box_w = abs(x1 - x0)
            box_h = abs(y1 - y0)

            if self._box_patch is None:
                self._box_patch = Rectangle(
                    (box_x, box_y),
                    box_w,
                    box_h,
                    facecolor=(0.16, 0.45, 0.78, 0.15),
                    edgecolor=(0.16, 0.45, 0.78, 0.9),
                    linestyle="--",
                    linewidth=1.2,
                    zorder=1000,
                )
                self.ax.add_patch(self._box_patch)
            else:
                self._box_patch.set_xy((box_x, box_y))
                self._box_patch.set_width(box_w)
                self._box_patch.set_height(box_h)

            self.figure.canvas.draw_idle()

    # ----------------------------------------------------------------- Mouse Release
    def _on_release(self, event: MouseEvent) -> None:
        # Left button release
        if event.button == 1:
            if not self._is_dragging and event.inaxes == self.ax:
                if event.xdata is not None and event.ydata is not None and self.on_click_point:
                    self.on_click_point(event.xdata, event.ydata)

            self._press_pix = None
            self._press_lims = None
            self._is_dragging = False

        # Right button release (Box Zoom finish)
        elif event.button == 3:
            if self._box_start_data is not None and self._box_start_pix is not None and event.xdata is not None and event.ydata is not None:
                dx_px = abs(event.x - self._box_start_pix[0])
                dy_px = abs(event.y - self._box_start_pix[1])

                if dx_px > 5 and dy_px > 5:
                    x0, y0 = self._box_start_data
                    x1, y1 = event.xdata, event.ydata
                    x_min, x_max = min(x0, x1), max(x0, x1)
                    y_min, y_max = min(y0, y1), max(y0, y1)

                    self.ax.set_xlim(x_min, x_max)
                    self.ax.set_ylim(y_min, y_max)

            self._remove_box_patch()
            self._box_start_data = None
            self._box_start_pix = None
            self.figure.canvas.draw_idle()

    def _remove_box_patch(self) -> None:
        if self._box_patch is not None:
            try:
                self._box_patch.remove()
            except Exception:
                pass
            self._box_patch = None

    # ----------------------------------------------------------------- Keyboard
    def _on_key_press(self, event: KeyEvent) -> None:
        if not event.key or not self.on_shortcut:
            return
        self.on_shortcut(event.key)
