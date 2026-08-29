"""Headless exporting entry point."""

from __future__ import annotations

from collections.abc import Iterable

from matplotlib.axes import Axes
from matplotlib.figure import Figure


def view(
    design,
    ax: Axes | None = None,
    *,
    figsize: tuple[float, float] = (8.0, 8.0),
    components: Iterable[str] | None = None,
    layers: Iterable[int] | None = None,
    chip_outline: bool = True,
    title: str | None = None,
) -> Figure:
    """Export ``design`` to a matplotlib figure.

    Use this from scripts, notebooks, or anywhere Qt is unavailable. It returns
    the figure so callers can save it, embed it in subplots, or show it inline.
    """
    return design.export(
        "mpl",
        ax=ax,
        figsize=figsize,
        components=components,
        layers=layers,
        chip_outline=chip_outline,
        title=title,
    )
