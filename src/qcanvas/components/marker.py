"""Alignment and packaging marker components for quantum chips.

Includes:
    - PackagingMarker: Multi-style alignment and packaging casing marker (cross, cross_box, circle_cross, corner_l, square)
    - AlignmentMarker: Optical/photolithography alignment mark
"""

from __future__ import annotations

from qcanvas.components.base import Component
from qcanvas.draw import buffer, circle, rectangle, subtract, union
from qcanvas.utility import AttrDict, parse_dimension


class PackagingMarker(Component):
    """Alignment and casing marker for chip packaging and assembly.

    Used to accurately align the chip inside the sample box/casing (套壳),
    as well as for dicing saw alignment, wirebond referencing, and optical inspection.

    Supported marker types:
        - 'cross_box': Central crosshair inside an outer square box frame
        - 'cross': Precision crosshair marker
        - 'circle_cross': Concentric circular ring with central crosshair
        - 'corner_l': L-shaped corner bracket for chip corner alignment
        - 'square': Centered square target

    Options:
        marker_type: Marker geometry type ('cross_box', 'cross', 'circle_cross', 'corner_l', 'square').
        size: Overall outer bounding size.
        cross_width: Line width / thickness of the crosshair.
        cross_length: Total arm length of the central crosshair.
        box_size: Outer square frame size for 'cross_box'.
        box_line_width: Line width of the outer square frame.
        subtract: If True, etch the marker out of the ground plane.
        ground_guard: Surrounding ground plane margin when subtracted.
    """

    default_options = AttrDict(
        marker_type="cross_box",
        size="200um",
        cross_width="20um",
        cross_length="140um",
        box_size="200um",
        box_line_width="10um",
        subtract=False,
        ground_guard="30um",
    )

    def make(self) -> None:
        marker_type = str(self.options.get("marker_type", "cross_box")).lower()
        size = parse_dimension(self.options.size)
        cross_w = parse_dimension(self.options.cross_width)
        cross_l = parse_dimension(self.options.get("cross_length", size * 0.7))
        box_size = parse_dimension(self.options.get("box_size", size))
        box_lw = parse_dimension(self.options.get("box_line_width", cross_w / 2.0))
        is_subtract = bool(self.options.get("subtract", False))
        guard = parse_dimension(self.options.get("ground_guard", self.default_options.ground_guard))

        # 1. Central cross shape
        h_bar = rectangle(cross_l, cross_w, 0.0, 0.0)
        v_bar = rectangle(cross_w, cross_l, 0.0, 0.0)
        cross_geom = union(h_bar, v_bar)

        if marker_type == "cross":
            geom = cross_geom

        elif marker_type == "cross_box":
            # Outer box frame = outer box minus inner box
            outer_box = rectangle(box_size, box_size, 0.0, 0.0)
            inner_box = rectangle(box_size - 2.0 * box_lw, box_size - 2.0 * box_lw, 0.0, 0.0)
            box_frame = subtract(outer_box, inner_box)
            geom = union(cross_geom, box_frame)

        elif marker_type == "circle_cross":
            # Concentric ring + cross
            ring_outer_r = size / 2.0
            ring_inner_r = max(0.0, ring_outer_r - box_lw)
            outer_c = circle(ring_outer_r, 0.0, 0.0)
            inner_c = circle(ring_inner_r, 0.0, 0.0)
            ring_geom = subtract(outer_c, inner_c)
            geom = union(cross_geom, ring_geom)

        elif marker_type == "corner_l":
            # L-bracket placed in positive quadrant, centered around origin
            l_h = rectangle(size, cross_w, size / 2.0, cross_w / 2.0)
            l_v = rectangle(cross_w, size, cross_w / 2.0, size / 2.0)
            geom = union(l_h, l_v)

        elif marker_type == "square":
            geom = rectangle(size, size, 0.0, 0.0)

        else:
            geom = cross_geom

        if is_subtract and guard > 0.0:
            ground_outer = buffer(geom, guard, join_style=2, cap_style=2)
            ground_ring = subtract(ground_outer, geom)
            self.add_shape("ground", self.place(ground_ring))

        placed_geom = self.place(geom)
        label = "cutout" if is_subtract else "metal"
        self.add_shape(label, placed_geom, subtract=is_subtract)


# Aliases
AlignmentMarker = PackagingMarker
CasingMarker = PackagingMarker
Marker = PackagingMarker
packaging_marker = PackagingMarker
