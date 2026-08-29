"""Runtime configuration and design defaults for QCanvas."""

from __future__ import annotations

from qcanvas.utility.attr_dict import AttrDict

# The exporter used when none is explicitly requested (e.g. ``qcanvas.view``).
DEFAULT_EXPORTER = "mpl"

# Design-wide default variables (referenced by component options).
DESIGN_DEFAULTS = AttrDict(
    units="um",
    variables=AttrDict(
        cpw_width="10um",
        cpw_gap="6um",
    ),
)

# Default chip metadata: a single planar die centred at the origin.
CHIP_DEFAULTS = AttrDict(
    main=AttrDict(
        material="Si",
        size=AttrDict(center_x=0.0, center_y=0.0, size_x=9000.0, size_y=6000.0),
        z=AttrDict(thickness="300um"),
    )
)

# Palette keys are matched against a shape record's ``label`` (see the mpl
# exporter). Unknown labels fall back to the neutral "default" entry.
DISPLAY_STYLES = AttrDict(
    default=AttrDict(facecolor="0.15", edgecolor="0.0"),
    metal=AttrDict(facecolor="0.15", edgecolor="0.0"),
    junction=AttrDict(facecolor="#d62728", edgecolor="#8b0000"),
    pocket=AttrDict(facecolor="none", edgecolor="0.5"),
    ground=AttrDict(facecolor="0.25", edgecolor="0.1"),
)
