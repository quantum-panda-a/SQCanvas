"""Notebook-friendly inline display helpers."""

from __future__ import annotations

from sqcanvas.viewer.view import view


def display(design, *, figsize: tuple[float, float] = (8.0, 8.0), **options) -> None:
    """Export a design and show it inline in a Jupyter-style front end.

    Falls back to ``matplotlib.pyplot.show`` when no inline backend is active.
    """
    import matplotlib.pyplot as plt

    fig = view(design, figsize=figsize, **options)
    try:
        from IPython.display import display as ipy_display

        ipy_display(fig)
    except Exception:  # noqa: BLE001
        plt.show(block=False)
    return fig
