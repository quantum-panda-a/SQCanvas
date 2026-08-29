"""A reference transmon component: a dual-pad transmon with two charge islands in a ground plane cutout."""

from __future__ import annotations

from qcanvas.components.base import Component
from qcanvas.draw import rectangle, subtract
from qcanvas.utility import AttrDict, parse_dimension


class DualPadTransmon(Component):
    """A transmon component drawn in a ground plane cutout.

    Two charge islands sit either side of a small junction gap, enclosed by a
    cutout carved out of (subtracted from) the ground plane.

    Options:
        pad_gap: Distance between the two charge islands.
        inductor_width: Width of the junction bridge between the pads.
        pad_width: Width (x-axis) of each charge island pad.
        pad_height: Height (y-axis) of each charge island pad.
        gap_top: Distance from the top of the upper pad to the top cutout edge.
        gap_down: Distance from the bottom of the lower pad to the bottom cutout edge.
        gap_left: Distance from the left edge of the pads to the left cutout edge.
        gap_right: Distance from the right edge of the pads to the right cutout edge.
        pad_fillet: Corner rounding radius for the charge island pads.
        cutout_fillet: Corner rounding radius for the ground cutout.
        ground_guard: Surrounding ground plane margin.
    """

    default_options = AttrDict(
        pad_gap="30um",
        inductor_width="20um",
        pad_width="455um",
        pad_height="90um",
        gap_top="35um",
        gap_down="35um",
        gap_left="35um",
        gap_right="35um",
        pad_fillet="0um",
        cutout_fillet="0um",
        ground_guard="30um",
    )

    def make(self) -> None:
        pad_w = parse_dimension(self.options.pad_width)
        pad_h = parse_dimension(self.options.pad_height)
        gap = parse_dimension(self.options.pad_gap)
        inductor_w = parse_dimension(self.options.inductor_width)
        guard = parse_dimension(self.options.get("ground_guard", 0.0))

        pad_fillet = parse_dimension(
            self.options.get("pad_fillet", self.options.get("pad_radius", 0.0))
        )
        cutout_fillet = parse_dimension(
            self.options.get("cutout_fillet", self.options.get("cutout_radius", 0.0))
        )

        # Resolve directional gaps
        gap_top = parse_dimension(self.options.get("gap_top", self.default_options.gap_top))
        gap_down = parse_dimension(self.options.get("gap_down", self.default_options.gap_down))
        gap_left = parse_dimension(self.options.get("gap_left", self.default_options.gap_left))
        gap_right = parse_dimension(self.options.get("gap_right", self.default_options.gap_right))

        island_y = gap / 2.0 + pad_h / 2.0
        top_island = rectangle(pad_w, pad_h, 0.0, +island_y, fillet=pad_fillet)
        bottom_island = rectangle(pad_w, pad_h, 0.0, -island_y, fillet=pad_fillet)

        # Cutout dimensions and center offset determined by directional gaps
        cutout_w = pad_w + gap_left + gap_right
        cutout_h = 2.0 * pad_h + gap + gap_top + gap_down
        cutout_cx = (gap_right - gap_left) / 2.0
        cutout_cy = (gap_top - gap_down) / 2.0

        # Cutout carved out of the surrounding ground plane.
        cutout = rectangle(cutout_w, cutout_h, cutout_cx, cutout_cy, fillet=cutout_fillet)

        if guard > 0.0:
            ground_outer = rectangle(
                cutout_w + 2.0 * guard, cutout_h + 2.0 * guard, cutout_cx, cutout_cy
            )
            ground_ring = subtract(ground_outer, cutout)
            self.add_shape("ground", self.place(ground_ring))

        self.add_shape("cutout", self.place(cutout), subtract=True)
        self.add_shape("metal", self.place(top_island))
        self.add_shape("metal", self.place(bottom_island))

        # A small bar bridging the gap (kept simple, purely for layout).
        bridge = rectangle(inductor_w, gap)
        self.add_shape("junction", self.place(bridge))
