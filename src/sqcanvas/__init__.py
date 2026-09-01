"""SQCanvas — Superconducting Qubit Chip Analysis, Netlist, Visualization, and Automation Suite.

Public surface:

    sqcanvas.view(design)      -> export a design as a matplotlib figure
    sqcanvas.designs.Design    -> base design container
    sqcanvas.designs.PlanarDesign -> single-chip planar layout
    sqcanvas.components.Component, DualPadTransmon
    sqcanvas.exporters.Exporter, MatplotlibExporter, GdsExporter

The GUI (``sqcanvas.gui``) is installed by default but is *not* imported here so
the package stays cheap to import in headless / CI contexts.
"""

import logging

# Mute matplotlib's internal verbose loggers in interactive/notebook sessions
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("matplotlib.axes._base").setLevel(logging.WARNING)

from sqcanvas.codegen import (
    ScriptLoadError,
    export_python_script,
    generate_python_script,
    load_design_from_script,
)
from sqcanvas.components import (
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
from sqcanvas.designs import Design, PlanarDesign
from sqcanvas.exporters import Exporter, GdsExporter, MatplotlibExporter
from sqcanvas.viewer import display, view

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
