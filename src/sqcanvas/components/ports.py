"""Port and termination components for CPW circuits.

Includes:
    - Launchpad: Wirebond launch pad transition to CPW transmission line
    - CPWOpen: Open-circuit CPW termination (dielectric gap to ground)
    - CPWShort: Short-circuit CPW termination (center conductor shorted to ground)
"""

from __future__ import annotations

from shapely.geometry import Polygon

from sqcanvas.components.base import Component
from sqcanvas.draw import buffer, rectangle, subtract
from sqcanvas.utility import AttrDict, parse_dimension


class Launchpad(Component):
    """Wirebond launch pad for signal input/output coupling.

    Provides a 50-ohm tapered transition from a wide wirebonding pad to
    an on-chip CPW transmission line. The geometric origin (pos_x, pos_y)
    is located at the CPW connection interface, with the default port normal
    pointing in the +x direction toward the chip interior.

    Options:
        trace_width: Conductor width of the CPW transmission line at the port.
        trace_gap: Dielectric gap of the CPW transmission line.
        lead_length: Length of the uniform CPW lead before the taper.
        taper_length: Length of the tapered section.
        pad_width: Width of the wirebond bonding pad.
        pad_length: Length of the wirebond bonding pad.
        pad_gap: Dielectric gap surrounding the wirebond pad.
        ground_guard: Surrounding ground plane margin.
    """

    default_options = AttrDict(
        trace_width="10um",
        trace_gap="6um",
        lead_length="30um",
        taper_length="120um",
        pad_width="150um",
        pad_length="200um",
        pad_gap="80um",
        ground_guard="30um",
    )

    def make(self) -> None:
        trace_w = parse_dimension(self.options.trace_width)
        trace_g = parse_dimension(self.options.trace_gap)
        lead_l = parse_dimension(self.options.lead_length)
        taper_l = parse_dimension(self.options.taper_length)
        pad_w = parse_dimension(self.options.pad_width)
        pad_l = parse_dimension(self.options.pad_length)
        pad_g = parse_dimension(self.options.pad_gap)
        guard = parse_dimension(self.options.get("ground_guard", self.default_options.ground_guard))

        tw_half = trace_w / 2.0
        pw_half = pad_w / 2.0

        # Metal Polygon:
        # Origin (0, 0) is at the port.
        # Lead extends from x = 0 to x = -lead_l
        # Taper extends from x = -lead_l to x = -(lead_l + taper_l)
        # Pad extends from x = -(lead_l + taper_l) to x = -(lead_l + taper_l + pad_l)
        x0 = 0.0
        x1 = -lead_l
        x2 = -(lead_l + taper_l)
        x3 = -(lead_l + taper_l + pad_l)

        metal_pts = [
            (x0, tw_half),
            (x1, tw_half),
            (x2, pw_half),
            (x3, pw_half),
            (x3, -pw_half),
            (x2, -pw_half),
            (x1, -tw_half),
            (x0, -tw_half),
        ]
        metal = Polygon(metal_pts)

        # Pocket Cutout Polygon:
        # Cutout surrounds lead by trace_g, taper by interpolated gap, and pad by pad_g
        # Extends behind the pad by pad_g at x = x3 - pad_g
        tg_half = tw_half + trace_g
        pg_half = pw_half + pad_g
        x3_back = x3 - pad_g

        cutout_pts = [
            (x0, tg_half),
            (x1, tg_half),
            (x2, pg_half),
            (x3_back, pg_half),
            (x3_back, -pg_half),
            (x2, -pg_half),
            (x1, -tg_half),
            (x0, -tg_half),
        ]
        cutout = Polygon(cutout_pts)

        if guard > 0.0:
            ground_outer = buffer(cutout, guard, join_style=2, cap_style=2)
            ground_ring = subtract(ground_outer, cutout)
            self.add_shape("ground", self.place(ground_ring))

        self.add_shape("cutout", self.place(cutout), subtract=True)
        self.add_shape("metal", self.place(metal))


class CPWOpen(Component):
    """CPW open-circuit termination (open to ground).

    Terminates a CPW transmission line into an open dielectric pocket of
    length ``termination_gap`` before the ground plane. Origin (0, 0) is at
    the port interface where the incoming line ends, with normal along +x.

    Options:
        width: Conductor width of the terminating CPW line.
        gap: Dielectric gap of the terminating CPW line.
        termination_gap: Length of the dielectric gap past the end of the central conductor.
        ground_guard: Surrounding ground plane margin.
    """

    default_options = AttrDict(
        width="10um",
        gap="6um",
        termination_gap="6um",
        ground_guard="30um",
    )

    def make(self) -> None:
        w = parse_dimension(self.options.width)
        g = parse_dimension(self.options.gap)
        term_g = parse_dimension(self.options.termination_gap)
        guard = parse_dimension(self.options.get("ground_guard", self.default_options.ground_guard))

        # Cutout box extending from x = 0 to x = term_g
        # Width is w + 2*g
        cutout = rectangle(term_g, w + 2.0 * g, term_g / 2.0, 0.0)

        if guard > 0.0:
            ground_outer = buffer(cutout, guard, join_style=2, cap_style=2)
            ground_ring = subtract(ground_outer, cutout)
            self.add_shape("ground", self.place(ground_ring))

        self.add_shape("cutout", self.place(cutout), subtract=True)


class CPWShort(Component):
    """CPW short-circuit termination (short to ground).

    Terminates a CPW transmission line directly into the ground plane,
    ending the dielectric cutout at the port boundary (0, 0).

    Options:
        width: Conductor width of the terminating CPW line.
        gap: Dielectric gap of the terminating CPW line.
        ground_guard: Surrounding ground plane margin.
    """

    default_options = AttrDict(
        width="10um",
        gap="6um",
        ground_guard="30um",
    )

    def make(self) -> None:
        w = parse_dimension(self.options.width)
        guard = parse_dimension(self.options.get("ground_guard", self.default_options.ground_guard))

        # Flush short termination: adds a flush metal junction marker / lead
        metal = rectangle(w / 2.0, w, -w / 4.0, 0.0)

        if guard > 0.0:
            ground_outer = rectangle(w / 2.0 + 2.0 * guard, w + 2.0 * guard, -w / 4.0, 0.0)
            ground_ring = subtract(ground_outer, metal)
            self.add_shape("ground", self.place(ground_ring))

        self.add_shape("metal", self.place(metal))


# Aliases
LaunchpadWirebond = Launchpad
launchpad = Launchpad
OpenToGround = CPWOpen
cpw_open = CPWOpen
ShortToGround = CPWShort
cpw_short = CPWShort
