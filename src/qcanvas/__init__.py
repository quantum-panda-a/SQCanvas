"""QCanvas — a plugin-driven layout engine for superconducting quantum chips.

Public surface:

    qcanvas.view(design)      -> export a design as a matplotlib figure
    qcanvas.designs.Design    -> base design container
    qcanvas.designs.PlanarDesign -> single-chip planar layout
    qcanvas.components.Component, TransmonPocket
    qcanvas.exporters.Exporter, MatplotlibExporter, GdsExporter

The GUI (``qcanvas.gui``) is installed by default but is *not* imported here so
the package stays cheap to import in headless / CI contexts.
"""

from qcanvas import components, designs, draw, exporters, shapes, utility
from qcanvas.components import Component, TransmonPocket
from qcanvas.designs import Design, PlanarDesign
from qcanvas.exporters import Exporter, GdsExporter, MatplotlibExporter
from qcanvas.viewer import display, view

__version__ = "0.1.0"

__all__ = [
    "Component",
    "Design",
    "Exporter",
    "GdsExporter",
    "MatplotlibExporter",
    "PlanarDesign",
    "TransmonPocket",
    "components",
    "designs",
    "display",
    "draw",
    "exporters",
    "shapes",
    "utility",
    "view",
]
