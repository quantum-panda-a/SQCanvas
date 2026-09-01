"""Text layout component for chip labels, markers, and annotations."""

from __future__ import annotations

import gdstk
import shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union

from sqcanvas.components.base import Component
from sqcanvas.draw import buffer, subtract, translate
from sqcanvas.utility import AttrDict, parse_dimension


class Text(Component):
    """Text shape component rendered on the chip.

    Renders a text string into vector polygons using GDSII typography fonts.
    Can be placed as positive metal or subtracted as a ground cutout pocket.

    Options:
        text: Text string to render.
        size: Font height / size.
        subtract: If True, subtract the text geometry from the ground plane.
        align_x: Horizontal alignment ('left', 'center', 'right').
        align_y: Vertical alignment ('bottom', 'center', 'top').
        vertical: If True, orient text vertically.
        ground_guard: Surrounding ground plane margin when subtracted.
    """

    default_options = AttrDict(
        text="SQCanvas",
        size="100um",
        subtract=False,
        align_x="center",
        align_y="center",
        vertical=False,
        ground_guard="30um",
    )

    def make(self) -> None:
        text_str = str(self.options.text)
        if not text_str:
            return

        size = parse_dimension(self.options.size)
        is_subtract = bool(self.options.get("subtract", False))
        align_x = str(self.options.get("align_x", "center")).lower()
        align_y = str(self.options.get("align_y", "center")).lower()
        vertical = bool(self.options.get("vertical", False))
        guard = parse_dimension(self.options.get("ground_guard", self.default_options.ground_guard))

        raw_polys = gdstk.text(text_str, size, position=(0.0, 0.0), vertical=vertical)
        if not raw_polys:
            return

        shapely_polys = [shapely.make_valid(Polygon(p.points)) for p in raw_polys]
        geom = unary_union(shapely_polys)

        min_x, min_y, max_x, max_y = geom.bounds

        # Calculate alignment offsets
        dx = 0.0
        if align_x == "center":
            dx = -(min_x + max_x) / 2.0
        elif align_x == "left":
            dx = -min_x
        elif align_x == "right":
            dx = -max_x

        dy = 0.0
        if align_y == "center":
            dy = -(min_y + max_y) / 2.0
        elif align_y == "bottom":
            dy = -min_y
        elif align_y == "top":
            dy = -max_y

        aligned_geom = translate(geom, dx, dy)

        if is_subtract and guard > 0.0:
            ground_outer = buffer(aligned_geom, guard, join_style=2, cap_style=2)
            ground_ring = subtract(ground_outer, aligned_geom)
            self.add_shape("ground", self.place(ground_ring))

        placed_geom = self.place(aligned_geom)
        label = "cutout" if is_subtract else "metal"
        self.add_shape(label, placed_geom, subtract=is_subtract)


# Alias
text = Text

