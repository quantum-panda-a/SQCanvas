"""A matplotlib exporter — produces a :class:`matplotlib.figure.Figure`."""

from __future__ import annotations

from collections.abc import Iterable

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from sqcanvas.config import get_theme
from sqcanvas.draw import union
from sqcanvas.draw.mpl import draw_records
from sqcanvas.exporters.base import Exporter


class MatplotlibExporter(Exporter):
    """Export a design to a matplotlib figure.

    This is the default exporter and backs both the headless ``view()`` helper
    and the Qt desktop viewer.
    """

    name = "mpl"

    def export(
        self,
        design,
        *,
        ax: Axes | None = None,
        figsize: tuple[float, float] = (8.0, 8.0),
        components: Iterable[str] | None = None,
        layers: Iterable[int] | None = None,
        chip_outline: bool = True,
        grid: bool = True,
        title: str | None = None,
        dark_mode: bool | None = None,
        theme: str | None = None,
    ) -> Figure:
        return export_scene(
            design,
            ax=ax,
            figsize=figsize,
            components=components,
            layers=layers,
            chip_outline=chip_outline,
            grid=grid,
            title=title,
            dark_mode=dark_mode,
            theme=theme,
        )


def export_scene(
    design,
    *,
    ax: Axes | None = None,
    figsize: tuple[float, float] = (8.0, 8.0),
    components: Iterable[str] | None = None,
    layers: Iterable[int] | None = None,
    chip_outline: bool = True,
    grid: bool = True,
    title: str | None = None,
    dark_mode: bool | None = None,
    theme: str | None = None,
) -> Figure:
    """Build a matplotlib scene for ``design`` with preset theme support."""
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize, layout="constrained")
    else:
        fig = ax.get_figure()
        ax.clear()

    components = set(components) if components is not None else None
    layers = set(layers) if layers is not None else None
    records = design.shapes.as_records()
    if components is not None:
        records = [r for r in records if r.component in components]
    if layers is not None:
        records = [r for r in records if r.layer in layers]

    # Resolve theme
    if theme is not None:
        theme_cfg = get_theme(theme)
    elif dark_mode is not None:
        theme_cfg = get_theme("cyber" if dark_mode else "paper")
    else:
        theme_cfg = get_theme("paper")

    styles = {key: value.to_dict() if hasattr(value, "to_dict") else dict(value) for key, value in theme_cfg.styles.items()}
    outline = None
    if chip_outline and hasattr(design, "main_chip"):
        cx, cy = design.chip_centre()
        w, h = design.chip_extent()
        outline = [
            (cx - w / 2, cy - h / 2),
            (cx + w / 2, cy - h / 2),
            (cx + w / 2, cy + h / 2),
            (cx - w / 2, cy + h / 2),
            (cx - w / 2, cy - h / 2),
        ]

    subtracts = [r.geometry for r in records if r.subtract and not r.geometry.is_empty]
    ground_records = [r for r in records if r.label == "ground" and not r.subtract and not r.geometry.is_empty]
    other_records = [r for r in records if r.label != "ground" and not r.subtract and not r.geometry.is_empty]

    draw_list: list[dict] = []
    if ground_records:
        merged_ground = union(*[r.geometry for r in ground_records])
        if subtracts:
            merged_ground = merged_ground.difference(union(*subtracts))
        if not merged_ground.is_empty:
            draw_list.append({"geometry": merged_ground, "label": "ground", "subtract": False})

    for r in other_records:
        draw_list.append(r.__dict__)

    draw_records(ax, draw_list, styles=styles, outline=True, chip_outline=outline)
    ax.set_aspect("equal", adjustable="box")
    ax.set_anchor("C")
    ax.autoscale_view()
    unit_label = getattr(design, "units", "um")

    # Apply Theme Aesthetics
    fig.patch.set_facecolor(theme_cfg.canvas_bg)
    ax.set_facecolor(theme_cfg.canvas_bg)
    ax.tick_params(colors=theme_cfg.text_color, labelsize=9)
    ax.xaxis.label.set_color(theme_cfg.text_color)
    ax.yaxis.label.set_color(theme_cfg.text_color)
    ax.set_xlabel(f"x [{unit_label}]", labelpad=6)
    ax.set_ylabel(f"y [{unit_label}]", labelpad=6)

    for spine in ax.spines.values():
        spine.set_color(theme_cfg.axis_color)
        spine.set_linewidth(1.0)

    if grid:
        ax.grid(True, color=theme_cfg.grid_color, linestyle="--", linewidth=0.8, alpha=0.85)
        ax.set_axisbelow(True)
    else:
        ax.grid(False)

    if title is not None:
        ax.set_title(title, pad=10, color=theme_cfg.text_color)

    if fig.get_layout_engine() is None:
        fig.tight_layout()
    return fig
