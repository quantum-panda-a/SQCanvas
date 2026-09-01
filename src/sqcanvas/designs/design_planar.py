"""A single-chip, planar (coplanar-waveguide) layout design."""

from __future__ import annotations

from sqcanvas.designs.design_base import Design


class PlanarDesign(Design):
    """The default layout: one planar die with coplanar geometries.

    Use this for qubits, resonators, launch pads, and routes drawn on a single
    metal/dielectric stack. It adds a small amount of convenience on top of
    :class:`Design` (a named chip + helper accessors) while keeping the
    shape/exporting split intact.
    """

    def __init__(self, metadata: dict | None = None, overwrite_enabled: bool = False) -> None:
        super().__init__(metadata=metadata, overwrite_enabled=overwrite_enabled)
        self.name = "PlanarDesign"

    @property
    def main_chip(self):
        """The default single chip definition."""
        return self.chips.main

    def chip_centre(self) -> tuple[float, float]:
        """Return the ``(x, y)`` centre of the main chip."""
        size = self.chips.main.size
        return (float(size.center_x), float(size.center_y))

    def chip_extent(self) -> tuple[float, float]:
        """Return the ``(width, height)`` of the main chip."""
        size = self.chips.main.size
        return (float(size.size_x), float(size.size_y))
