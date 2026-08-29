import pytest
from matplotlib.figure import Figure

from qcanvas.gui.interaction import CanvasInteraction


def test_compute_zoom_range():
    # Zoom in at center 0.0 with factor 2.0
    # Current range: [-100, 100], span = 200 -> new span = 100 -> [-50, 50]
    new_min, new_max = CanvasInteraction._compute_zoom_range(-100.0, 100.0, 0.0, 2.0)
    assert pytest.approx(new_min) == -50.0
    assert pytest.approx(new_max) == 50.0

    # Zoom in offset at 50.0 (offset ratio 0.75)
    # New span = 100 -> min = 50 - 0.75*100 = -25, max = 50 + 0.25*100 = 75
    new_min, new_max = CanvasInteraction._compute_zoom_range(-100.0, 100.0, 50.0, 2.0)
    assert pytest.approx(new_min) == -25.0
    assert pytest.approx(new_max) == 75.0


def test_interaction_callbacks():
    fig = Figure()
    ax = fig.add_subplot(111)
    ax.set_xlim(-100.0, 100.0)
    ax.set_ylim(-100.0, 100.0)

    hovered = []
    clicked = []
    shortcuts = []
    autoscaled = []

    interaction = CanvasInteraction(
        fig,
        ax,
        on_hover=lambda x, y: hovered.append((x, y)),
        on_click_point=lambda x, y: clicked.append((x, y)),
        on_shortcut=lambda k: shortcuts.append(k),
        on_autoscale=lambda: autoscaled.append(True),
    )

    # Hover coordinate callback
    class MockEvent:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    # Hover outside
    interaction._on_motion(MockEvent(inaxes=None, xdata=None, ydata=None, button=None))
    assert hovered[-1] == (None, None)

    # Hover inside
    interaction._on_motion(MockEvent(inaxes=ax, xdata=12.5, ydata=-45.0, button=None))
    assert hovered[-1] == (12.5, -45.0)

    # Single click
    interaction._on_press(MockEvent(inaxes=ax, button=1, x=100, y=100, xdata=10.0, ydata=20.0, dblclick=False))
    interaction._on_release(MockEvent(inaxes=ax, button=1, x=100, y=100, xdata=10.0, ydata=20.0))
    assert clicked[-1] == (10.0, 20.0)

    # Double click autoscale
    interaction._on_press(MockEvent(inaxes=ax, button=1, x=100, y=100, xdata=10.0, ydata=20.0, dblclick=True))
    assert len(autoscaled) == 1

    # Shortcuts
    interaction._on_key_press(MockEvent(key="a"))
    assert shortcuts[-1] == "a"

    interaction.disconnect()
    assert len(interaction._cids) == 0
