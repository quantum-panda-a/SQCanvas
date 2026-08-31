"""QCanvas — a plugin-driven layout engine for superconducting quantum chips.

Public surface:

    qcanvas.view(design)      -> export a design as a matplotlib figure
    qcanvas.designs.Design    -> base design container
    qcanvas.designs.PlanarDesign -> single-chip planar layout
    qcanvas.components.Component, DualPadTransmon
    qcanvas.exporters.Exporter, MatplotlibExporter, GdsExporter

The GUI (``qcanvas.gui``) is installed by default but is *not* imported here so
the package stays cheap to import in headless / CI contexts.
"""

import logging

# Mute matplotlib's internal verbose loggers in interactive/notebook sessions
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("matplotlib.axes._base").setLevel(logging.WARNING)

from qcanvas.codegen import (
    ScriptLoadError,
    export_python_script,
    generate_python_script,
    load_design_from_script,
)
from qcanvas.components import (
    AlignmentMarker,
    CPWOpen,
    CPWShort,
    ChargeArc,
    ChargeClaw,
    ChargeTee,
    CircularTransmon,
    Component,
    CrossTransmon,
    DualPadTransmon,
    Launchpad,
    PackagingMarker,
    ReadTee,
    SinglePadTransmon,
    Text,
)
from qcanvas.designs import Design, PlanarDesign
from qcanvas.exporters import Exporter, GdsExporter, MatplotlibExporter
from qcanvas.viewer import display, view

to_python = generate_python_script
load_script = load_design_from_script

__version__ = "0.1.0"

__all__ = [
    "AlignmentMarker",
    "CPWOpen",
    "CPWShort",
    "ChargeArc",
    "ChargeClaw",
    "ChargeTee",
    "CircularTransmon",
    "Component",
    "CrossTransmon",
    "Design",
    "DualPadTransmon",
    "Exporter",
    "GdsExporter",
    "Launchpad",
    "MatplotlibExporter",
    "PackagingMarker",
    "PlanarDesign",
    "ReadTee",
    "SinglePadTransmon",
    "Text",
    "display",
    "draw",
    "export_python_script",
    "exporters",
    "generate_python_script",
    "load_design_from_script",
    "load_script",
    "shapes",
    "to_python",
    "utility",
    "view",
]
