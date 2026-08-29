"""A reference transmon component: a pocket transmon with two charge islands."""

from __future__ import annotations

from qcanvas.components.base import Component
from qcanvas.draw import rectangle, subtract
from qcanvas.utility import AttrDict, parse_dimension


class TransmonPocket(Component):
    """A pocket transmon drawn in a ground plane.

    Two rectangular charge islands sit either side of a small junction gap,
    enclosed by a pocket that is carved out of (subtracted from) the ground
    plane. An optional ``ground_guard`` specifies the surrounding ground plane margin.
    """

    default_options = AttrDict(
        pad_gap="30um",
        inductor_width="20um",
        pad_width="455um",
        pad_height="90um",
        pocket_width="650um",
        pocket_height="650um",
        ground_guard="10um",
    )

    def make(self) -> None:
        pad_w = parse_dimension(self.options.pad_width)
        pad_h = parse_dimension(self.options.pad_height)
        gap = parse_dimension(self.options.pad_gap)
        pocket_w = parse_dimension(self.options.pocket_width)
        pocket_h = parse_dimension(self.options.pocket_height)
        inductor_w = parse_dimension(self.options.inductor_width)
        guard = parse_dimension(self.options.get("ground_guard", 0.0))

        island_y = gap / 2.0 + pad_h / 2.0
        top_island = rectangle(pad_w, pad_h, 0.0, +island_y)
        bottom_island = rectangle(pad_w, pad_h, 0.0, -island_y)

        # Pocket carved out of the surrounding ground plane.
        pocket = rectangle(pocket_w, pocket_h)

        if guard > 0.0:
            ground_outer = rectangle(pocket_w + 2.0 * guard, pocket_h + 2.0 * guard)
            ground_ring = subtract(ground_outer, pocket)
            self.add_shape("ground", self.place(ground_ring))

        self.add_shape("pocket", self.place(pocket), subtract=True)
        self.add_shape("metal", self.place(top_island))
        self.add_shape("metal", self.place(bottom_island))

        # A small bar bridging the gap (kept simple, purely for layout).
        bridge = rectangle(inductor_w, gap)
        self.add_shape("junction", self.place(bridge))
