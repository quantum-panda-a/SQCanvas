"""Transmon components: DualPadTransmon, SinglePadTransmon, and CrossTransmon."""

from __future__ import annotations

from qcanvas.components.base import Component
from qcanvas.draw import rectangle, subtract, union
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


class SinglePadTransmon(Component):
    """A single-pad transmon component drawn in a ground plane cutout.

    A single charge island sits inside a cutout pocket carved out of the ground
    plane, with a Josephson junction in the bottom gap connecting the pad to ground.
    The component placement center (pos_x, pos_y) is at the center of the metal pad.

    Options:
        pad_width: Width (x-axis) of the charge island pad.
        pad_height: Height (y-axis) of the charge island pad.
        inductor_width: Width of the junction bridge in the bottom gap.
        gap_top: Distance from the top of the pad to the top cutout edge.
        gap_down: Distance from the bottom of the pad to the bottom cutout edge.
        gap_left: Distance from the left edge of the pad to the left cutout edge.
        gap_right: Distance from the right edge of the pad to the right cutout edge.
        pad_fillet: Corner rounding radius for the charge island pad.
        cutout_fillet: Corner rounding radius for the ground cutout.
        ground_guard: Surrounding ground plane margin.
    """

    default_options = AttrDict(
        pad_width="650um",
        pad_height="120um",
        inductor_width="20um",
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

        # Single metal pad centered at (0, 0)
        pad = rectangle(pad_w, pad_h, 0.0, 0.0, fillet=pad_fillet)

        # Cutout dimensions and center offset determined by directional gaps
        cutout_w = pad_w + gap_left + gap_right
        cutout_h = pad_h + gap_top + gap_down
        cutout_cx = (gap_right - gap_left) / 2.0
        cutout_cy = (gap_top - gap_down) / 2.0

        cutout = rectangle(cutout_w, cutout_h, cutout_cx, cutout_cy, fillet=cutout_fillet)

        if guard > 0.0:
            ground_outer = rectangle(
                cutout_w + 2.0 * guard, cutout_h + 2.0 * guard, cutout_cx, cutout_cy
            )
            ground_ring = subtract(ground_outer, cutout)
            self.add_shape("ground", self.place(ground_ring))

        self.add_shape("cutout", self.place(cutout), subtract=True)
        self.add_shape("metal", self.place(pad))

        # Junction placed in the bottom gap between pad and ground
        bridge_y = -pad_h / 2.0 - gap_down / 2.0
        bridge = rectangle(inductor_w, gap_down, 0.0, bridge_y)
        self.add_shape("junction", self.place(bridge))


class CrossTransmon(Component):
    """A cross-shaped (Xmon / Crossmon) transmon component.

    Four cross arms intersect at the geometric center (pos_x, pos_y), enclosed
    by a cross-shaped pocket carved out of the ground plane. A Josephson junction
    bridges the bottom (south) gap between the south arm and the ground plane.

    Options:
        cross_width: Width of each cross arm.
        cross_length: Length of each cross arm from the center.
        cross_gap: Gap between the cross arms and the ground cutout.
        inductor_width: Width of the junction bridge in the south gap.
        cross_fillet: Corner rounding radius for the cross arms.
        cutout_fillet: Corner rounding radius for the ground cutout pocket.
        ground_guard: Surrounding ground plane margin.
    """

    default_options = AttrDict(
        cross_width="30um",
        cross_length="200um",
        cross_gap="35um",
        inductor_width="20um",
        cross_fillet="0um",
        cutout_fillet="0um",
        ground_guard="30um",
    )

    def make(self) -> None:
        cross_w = parse_dimension(self.options.cross_width)
        cross_l = parse_dimension(self.options.cross_length)
        cross_gap = parse_dimension(self.options.cross_gap)
        inductor_w = parse_dimension(self.options.get("inductor_width", self.default_options.inductor_width))
        guard = parse_dimension(self.options.get("ground_guard", 0.0))

        cross_fillet = parse_dimension(
            self.options.get("cross_fillet", self.options.get("fillet", 0.0))
        )
        cutout_fillet = parse_dimension(
            self.options.get("cutout_fillet", self.options.get("cutout_radius", 0.0))
        )

        # Cross metal shape: horizontal and vertical arms intersecting at (0, 0)
        h_bar = rectangle(2.0 * cross_l, cross_w, 0.0, 0.0, fillet=cross_fillet)
        v_bar = rectangle(cross_w, 2.0 * cross_l, 0.0, 0.0, fillet=cross_fillet)
        cross = union(h_bar, v_bar)

        # Cross cutout (pocket) shape
        h_cutout = rectangle(
            2.0 * (cross_l + cross_gap), cross_w + 2.0 * cross_gap, 0.0, 0.0, fillet=cutout_fillet
        )
        v_cutout = rectangle(
            cross_w + 2.0 * cross_gap, 2.0 * (cross_l + cross_gap), 0.0, 0.0, fillet=cutout_fillet
        )
        cutout = union(h_cutout, v_cutout)

        if guard > 0.0:
            outer_dim = 2.0 * (cross_l + cross_gap + guard)
            ground_outer = rectangle(outer_dim, outer_dim, 0.0, 0.0)
            ground_ring = subtract(ground_outer, cutout)
            self.add_shape("ground", self.place(ground_ring))

        self.add_shape("cutout", self.place(cutout), subtract=True)
        self.add_shape("metal", self.place(cross))

        # Junction placed in the south gap
        bridge_y = -cross_l - cross_gap / 2.0
        bridge = rectangle(inductor_w, cross_gap, 0.0, bridge_y)
        self.add_shape("junction", self.place(bridge))


