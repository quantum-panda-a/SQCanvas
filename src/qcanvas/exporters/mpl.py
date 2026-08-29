"""A matplotlib exporter — produces a :class:`matplotlib.figure.Figure`."""

from __future__ import annotations

from collections.abc import Iterable

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from qcanvas.config import DISPLAY_STYLES
from qcanvas.draw import union
from qcanvas.draw.mpl import draw_records
from qcanvas.exporters.base import Exporter


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
) -> Figure:
    """Build a matplotlib scene for ``design`` and return its figure."""
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

    styles = {key: value.to_dict() if hasattr(value, "to_dict") else dict(value) for key, value in DISPLAY_STYLES.items()}
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
    subtract_records = [r for r in records if r.subtract and not r.geometry.is_empty]

    draw_list: list[dict] = []
    if ground_records:
        merged_ground = union(*[r.geometry for r in ground_records])
        if subtracts:
            merged_ground = merged_ground.difference(union(*subtracts))
        if not merged_ground.is_empty:
            draw_list.append({"geometry": merged_ground, "label": "ground", "subtract": False})

    for r in subtract_records:
        draw_list.append(r.__dict__)

    for r in other_records:
        draw_list.append(r.__dict__)

    draw_records(ax, draw_list, styles=styles, outline=True, chip_outline=outline)
    ax.set_aspect("equal", adjustable="box")
    ax.set_anchor("C")
    ax.autoscale_view()
    unit_label = getattr(design, "units", "um")
    ax.set_xlabel(f"x [{unit_label}]", labelpad=6)
    ax.set_ylabel(f"y [{unit_label}]", labelpad=6)
    if grid:
        ax.grid(True, color="#dcdcdc", linestyle="--", linewidth=0.6, alpha=0.75)
        ax.set_axisbelow(True)
    else:
        ax.grid(False)
    if title:
        ax.set_title(title, pad=10)
    else:
        ax.set_title(f"{design.name} — {len(records)} shapes", pad=10)
    if fig.get_layout_engine() is None:
        fig.tight_layout()
    return fig
