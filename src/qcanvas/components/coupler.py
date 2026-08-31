"""Coupler components for superconducting quantum circuits.

Includes:
    - ChargeTee: T-shaped capacitive XY drive line (for pad transmons)
    - ChargeClaw: Claw-shaped capacitive XY drive line (for cross transmons)
    - ChargeArc: Circular arc capacitive XY drive line (for circular transmons)
    - ReadTee: Readout resonator coupling tee (with origin at resonator outlet port)
"""

from __future__ import annotations

import math

from shapely.geometry import Polygon

from qcanvas.components.base import Component
from qcanvas.draw import arc, circle, rectangle, subtract, union
from qcanvas.utility import AttrDict, parse_dimension


class ChargeTee(Component):
    """T-shaped capacitive charge line (XY drive) coupler.

    Commonly used for capacitive coupling to pad-shaped transmons (SinglePad / DualPad).
    The geometric anchor/origin (pos_x, pos_y) is at the connection port to the
    transmission line, with the default port normal pointing UP (+y).

    Options:
        trace_width: Width of the feedline central trace at the port.
        trace_gap: Gap of the feedline at the port.
        lead_length: Length of the lead extending from the port toward the transmon.
        tee_width: Width of the T-head capacitive bar.
        tee_height: Height (thickness along y) of the T-head capacitive bar.
        tee_gap: Dielectric gap surrounding the T-head.
        tee_fillet: Corner rounding radius for the metal T-head.
        cutout_fillet: Corner rounding radius for the ground cutout around the T-head.
        ground_guard: Surrounding ground plane margin.
    """

    default_options = AttrDict(
        trace_width="10um",
        trace_gap="6um",
        lead_length="50um",
        tee_width="100um",
        tee_height="20um",
        tee_gap="15um",
        tee_fillet="0um",
        cutout_fillet="0um",
        ground_guard="30um",
    )

    def make(self) -> None:
        trace_w = parse_dimension(self.options.trace_width)
        trace_g = parse_dimension(self.options.trace_gap)
        lead_l = parse_dimension(self.options.lead_length)
        tee_w = parse_dimension(self.options.tee_width)
        tee_h = parse_dimension(self.options.tee_height)
        tee_g = parse_dimension(self.options.tee_gap)
        tee_fillet = parse_dimension(
            self.options.get("tee_fillet", self.options.get("fillet", 0.0))
        )
        cutout_fillet = parse_dimension(
            self.options.get("cutout_fillet", self.options.get("cutout_radius", 0.0))
        )
        guard = parse_dimension(self.options.get("ground_guard", self.default_options.ground_guard))

        # Metal trace: lead + tee bar
        # Lead extends from y = 0 down to y = -lead_l
        lead_metal = rectangle(trace_w, lead_l, 0.0, -lead_l / 2.0)
        # Tee head at y from -lead_l down to -lead_l - tee_h
        tee_metal = rectangle(
            tee_w, tee_h, 0.0, -lead_l - tee_h / 2.0, fillet=tee_fillet
        )
        metal = union(lead_metal, tee_metal)

        # Cutout: lead cutout (width trace_w + 2*trace_g) + tee cutout (tee_w + 2*tee_g, tee_h + 2*tee_g)
        # Top of lead cutout starts flush at y = 0
        lead_cutout = rectangle(trace_w + 2.0 * trace_g, lead_l, 0.0, -lead_l / 2.0)
        tee_cutout = rectangle(
            tee_w + 2.0 * tee_g,
            tee_h + 2.0 * tee_g,
            0.0,
            -lead_l - tee_h / 2.0,
            fillet=cutout_fillet,
        )
        cutout = union(lead_cutout, tee_cutout)

        if guard > 0.0:
            cutout_w = tee_w + 2.0 * tee_g
            cutout_h = lead_l + tee_h + tee_g
            cutout_cy = -cutout_h / 2.0
            ground_outer = rectangle(
                cutout_w + 2.0 * guard, cutout_h + 2.0 * guard, 0.0, cutout_cy
            )
            ground_ring = subtract(ground_outer, cutout)
            self.add_shape("ground", self.place(ground_ring))

        self.add_shape("cutout", self.place(cutout), subtract=True)
        self.add_shape("metal", self.place(metal))


class ChargeClaw(Component):
    """Claw-shaped capacitive charge line (XY drive) coupler.

    Commonly used for capacitive coupling to cross-shaped transmons (CrossTransmon / Xmon).
    The geometric anchor/origin (pos_x, pos_y) is at the connection port to the
    transmission line, with the default port normal pointing UP (+y).

    Options:
        trace_width: Width of the feedline central trace at the port.
        trace_gap: Gap of the feedline at the port.
        lead_length: Length of the lead extending from the port toward the transmon.
        claw_width: Inner spacing (gap/distance) between the two claw arms.
        claw_length: Length of the vertical prongs of the claw.
        claw_width_trace: Trace width of the claw base and prongs.
        claw_gap: Dielectric gap surrounding the claw.
        claw_fillet: Corner rounding radius for the metal claw (inner and outer corners).
        cutout_fillet: Corner rounding radius for the ground cutout.
        cutout_type: Cutout geometry mode (0: contour cutout around arms; 1: full pocket with area between arms etched out).
        ground_guard: Surrounding ground plane margin.
    """

    default_options = AttrDict(
        trace_width="10um",
        trace_gap="6um",
        lead_length="50um",
        claw_width="100um",
        claw_length="80um",
        claw_width_trace="10um",
        claw_gap="15um",
        claw_fillet="0um",
        cutout_fillet="0um",
        cutout_type=0,
        ground_guard="30um",
    )

    def make(self) -> None:
        trace_w = parse_dimension(self.options.trace_width)
        trace_g = parse_dimension(self.options.trace_gap)
        lead_l = parse_dimension(self.options.lead_length)
        w_inner = parse_dimension(self.options.claw_width)
        claw_l = parse_dimension(self.options.claw_length)
        w_trace = parse_dimension(self.options.claw_width_trace)
        claw_g = parse_dimension(self.options.claw_gap)
        claw_fillet = parse_dimension(
            self.options.get("claw_fillet", self.options.get("fillet", 0.0))
        )
        cutout_fillet = parse_dimension(
            self.options.get("cutout_fillet", self.options.get("cutout_radius", 0.0))
        )
        cutout_type = int(self.options.get("cutout_type", 0))
        guard = parse_dimension(self.options.get("ground_guard", self.default_options.ground_guard))

        w_out = w_inner + 2.0 * w_trace
        prong_x = (w_inner + w_trace) / 2.0
        prong_cy = -lead_l - w_trace - claw_l / 2.0

        # Lead from y = 0 to y = -lead_l
        lead_metal = rectangle(trace_w, lead_l, 0.0, -lead_l / 2.0)

        # U-shaped claw metal
        if claw_fillet <= 0.0:
            base_bar = rectangle(w_out, w_trace, 0.0, -lead_l - w_trace / 2.0)
            left_prong = rectangle(w_trace, claw_l, -prong_x, prong_cy)
            right_prong = rectangle(w_trace, claw_l, +prong_x, prong_cy)
            claw_metal = union(base_bar, left_prong, right_prong)
        else:
            r = min(claw_fillet, w_trace / 2.0, w_inner / 2.0, claw_l / 2.0)
            base_bar = rectangle(w_out, w_trace, 0.0, -lead_l - w_trace / 2.0, fillet=r)
            prong_h = claw_l + w_trace
            left_prong = rectangle(
                w_trace, prong_h, -prong_x, -lead_l - prong_h / 2.0, fillet=r
            )
            right_prong = rectangle(
                w_trace, prong_h, +prong_x, -lead_l - prong_h / 2.0, fillet=r
            )

            # Concave inner corner fillets where prongs meet base bar
            left_corner_box = rectangle(
                r, r, -w_inner / 2.0 + r / 2.0, -lead_l - w_trace - r / 2.0
            )
            left_corner_circ = circle(r, -w_inner / 2.0 + r, -lead_l - w_trace - r)
            left_inner_fillet = subtract(left_corner_box, left_corner_circ)

            right_corner_box = rectangle(
                r, r, w_inner / 2.0 - r / 2.0, -lead_l - w_trace - r / 2.0
            )
            right_corner_circ = circle(r, w_inner / 2.0 - r, -lead_l - w_trace - r)
            right_inner_fillet = subtract(right_corner_box, right_corner_circ)

            claw_metal = union(
                base_bar,
                left_prong,
                right_prong,
                left_inner_fillet,
                right_inner_fillet,
            )

        metal = union(lead_metal, claw_metal)

        # Cutout
        lead_cutout = rectangle(trace_w + 2.0 * trace_g, lead_l, 0.0, -lead_l / 2.0)

        if cutout_type == 0:
            base_cutout = rectangle(
                w_out + 2.0 * claw_g,
                w_trace + 2.0 * claw_g,
                0.0,
                -lead_l - w_trace / 2.0,
                fillet=cutout_fillet,
            )
            left_prong_cutout = rectangle(
                w_trace + 2.0 * claw_g,
                claw_l + claw_g,
                -prong_x,
                prong_cy - claw_g / 2.0,
                fillet=cutout_fillet,
            )
            right_prong_cutout = rectangle(
                w_trace + 2.0 * claw_g,
                claw_l + claw_g,
                +prong_x,
                prong_cy - claw_g / 2.0,
                fillet=cutout_fillet,
            )
            cutout = union(lead_cutout, base_cutout, left_prong_cutout, right_prong_cutout)
        else:
            # cutout_type == 1: the entire region between the two prongs is etched out,
            # extending upward by claw_g above the claw base and downward by claw_g below prongs
            pocket_w = w_out + 2.0 * claw_g
            pocket_h = w_trace + claw_l + 2.0 * claw_g
            pocket_cy = -lead_l - (w_trace + claw_l) / 2.0
            pocket_cutout = rectangle(
                pocket_w, pocket_h, 0.0, pocket_cy, fillet=cutout_fillet
            )
            cutout = union(lead_cutout, pocket_cutout)

        if guard > 0.0:
            cutout_w = w_out + 2.0 * claw_g
            cutout_h = lead_l + w_trace + claw_l + claw_g
            cutout_cy = -cutout_h / 2.0
            ground_outer = rectangle(
                cutout_w + 2.0 * guard, cutout_h + 2.0 * guard, 0.0, cutout_cy
            )
            ground_ring = subtract(ground_outer, cutout)
            self.add_shape("ground", self.place(ground_ring))

        self.add_shape("cutout", self.place(cutout), subtract=True)
        self.add_shape("metal", self.place(metal))


class ChargeArc(Component):
    """Circular arc capacitive charge line (XY drive) coupler.

    Commonly used for capacitive coupling to circular transmons (CircularTransmon).
    The geometric anchor/origin (pos_x, pos_y) is at the connection port to the
    transmission line, with the default port normal pointing UP (+y).

    Options:
        trace_width: Width of the feedline central trace at the port.
        trace_gap: Gap of the feedline at the port.
        lead_length: Length of the straight lead extending from the port to the arc.
        arc_radius: Center-line radius of the coupling arc.
        arc_width: Radial thickness of the arc electrode.
        arc_angle: Total angular span (degrees) of the arc.
        arc_gap: Dielectric gap surrounding the arc (radially and at both ends).
        arc_fillet: Corner rounding radius for the metal arc electrode.
        cutout_fillet: Corner rounding radius for the ground cutout.
        ground_guard: Surrounding ground plane margin.
    """

    default_options = AttrDict(
        trace_width="10um",
        trace_gap="6um",
        lead_length="50um",
        arc_radius="180um",
        arc_width="10um",
        arc_angle="90",
        arc_gap="15um",
        arc_fillet="0um",
        cutout_fillet="0um",
        ground_guard="30um",
    )

    def make(self) -> None:
        trace_w = parse_dimension(self.options.trace_width)
        trace_g = parse_dimension(self.options.trace_gap)
        lead_l = parse_dimension(self.options.lead_length)
        arc_r = parse_dimension(self.options.arc_radius)
        arc_w = parse_dimension(self.options.arc_width)
        arc_deg = float(self.options.arc_angle)
        arc_g = parse_dimension(self.options.arc_gap)
        arc_fillet = parse_dimension(
            self.options.get("arc_fillet", self.options.get("fillet", 0.0))
        )
        cutout_fillet = parse_dimension(
            self.options.get("cutout_fillet", self.options.get("cutout_radius", 0.0))
        )
        guard = parse_dimension(self.options.get("ground_guard", self.default_options.ground_guard))

        # Center of curvature for the arc is at (0, -lead_l - arc_r)
        # so that the top of the arc (at 90 deg) is at (0, -lead_l), touching the lead
        center_y = -lead_l - arc_r

        # Lead from y = 0 to y = -lead_l
        lead_metal = rectangle(trace_w, lead_l, 0.0, -lead_l / 2.0)

        # Arc from (90 - arc_deg/2) to (90 + arc_deg/2)
        start_angle = 90.0 - arc_deg / 2.0
        end_angle = 90.0 + arc_deg / 2.0
        arc_metal = arc(
            arc_r,
            arc_w,
            start_angle,
            end_angle,
            0.0,
            center_y,
            fillet=arc_fillet,
        )

        metal = union(lead_metal, arc_metal)

        # Cutouts: lead cutout + arc cutout with radial & angular arc_gap extension
        lead_cutout = rectangle(trace_w + 2.0 * trace_g, lead_l, 0.0, -lead_l / 2.0)
        d_theta = math.degrees(arc_g / max(1e-6, arc_r))
        cutout_start_angle = start_angle - d_theta
        cutout_end_angle = end_angle + d_theta
        cutout_width = arc_w + 2.0 * arc_g
        arc_cutout = arc(
            arc_r,
            cutout_width,
            cutout_start_angle,
            cutout_end_angle,
            0.0,
            center_y,
            fillet=cutout_fillet,
        )
        cutout = union(lead_cutout, arc_cutout)

        if guard > 0.0:
            min_x, min_y, max_x, max_y = cutout.bounds
            cutout_w = max_x - min_x
            cutout_h = max_y - min_y
            cutout_cx = (min_x + max_x) / 2.0
            cutout_cy = (min_y + max_y) / 2.0
            ground_outer = rectangle(
                cutout_w + 2.0 * guard,
                cutout_h + 2.0 * guard,
                cutout_cx,
                cutout_cy,
            )
            ground_ring = subtract(ground_outer, cutout)
            self.add_shape("ground", self.place(ground_ring))

        self.add_shape("cutout", self.place(cutout), subtract=True)
        self.add_shape("metal", self.place(metal))


class ReadTee(Component):
    """Readout resonator coupling tee.

    Comprises a primary through CPW feedline (bus) and a secondary CPW stub
    that capacitively couples to the bus and leads to the readout resonator.
    The geometric anchor/origin (pos_x, pos_y) is defined at the outlet port
    connecting to the readout resonator, with default normal facing DOWN (-y).

    The secondary stub and horizontal coupling section form a smooth 90-degree
    CPW bend with a specified turning radius (`turn_radius`), with the right end
    of the coupling line shorted directly to ground.

    Options:
        prime_width: Central conductor width of the primary feedline.
        prime_gap: Ground dielectric gap of the primary feedline.
        prime_length: Length of the primary through feedline.
        second_width: Central conductor width of the secondary stub.
        second_gap: Ground dielectric gap of the secondary stub.
        coupling_length: Length of the parallel coupling section.
        coupling_space: Ground plane spacing between primary and secondary lines.
        down_length: Length of the stub extending down to the resonator port (0, 0).
        turn_radius: Turning radius of the 90-degree CPW bend (default "20um").
        ground_guard: Surrounding ground plane margin.
    """

    default_options = AttrDict(
        prime_width="10um",
        prime_gap="6um",
        prime_length="300um",
        second_width="10um",
        second_gap="6um",
        coupling_length="150um",
        coupling_space="4um",
        down_length="50um",
        turn_radius="20um",
        ground_guard="30um",
    )

    def make(self) -> None:
        prime_w = parse_dimension(self.options.prime_width)
        prime_g = parse_dimension(self.options.prime_gap)
        prime_l = parse_dimension(self.options.prime_length)
        second_w = parse_dimension(self.options.second_width)
        second_g = parse_dimension(self.options.second_gap)
        coup_l = parse_dimension(self.options.coupling_length)
        coup_space = parse_dimension(self.options.coupling_space)
        down_l = parse_dimension(self.options.down_length)
        turn_r = parse_dimension(
            self.options.get(
                "turn_radius",
                self.options.get("bend_radius", self.options.get("radius", "20um")),
            )
        )
        guard = parse_dimension(self.options.get("ground_guard", self.default_options.ground_guard))

        # (0, 0) is the secondary port connecting to the readout resonator.
        # Secondary line forms a smooth 90-degree CPW bend from (0, 0) -> (0, down_l) -> (coup_l, down_l).
        w2 = second_w / 2.0
        wg = w2 + second_g

        if turn_r <= 0.0:
            # Secondary L-bend central conductor (shorted to ground at x = coup_l):
            sec_metal_pts = [
                (-w2, 0.0),
                (-w2, down_l + w2),
                (coup_l, down_l + w2),
                (coup_l, down_l - w2),
                (w2, down_l - w2),
                (w2, 0.0),
            ]
            second_metal = Polygon(sec_metal_pts)

            # Secondary L-bend dielectric cutout (ends flush at x = coup_l for short termination):
            sec_cutout_pts = [
                (-wg, 0.0),
                (-wg, down_l + wg),
                (coup_l, down_l + wg),
                (coup_l, down_l - wg),
                (wg, down_l - wg),
                (wg, 0.0),
            ]
            second_cutout = Polygon(sec_cutout_pts)
        else:
            r = min(turn_r, down_l, coup_l)
            arc_cx = r
            arc_cy = down_l - r

            # Metal: vertical lead, 90-deg circular bend, horizontal coupling arm
            metal_parts = []
            if down_l > r:
                metal_parts.append(rectangle(second_w, down_l - r, 0.0, (down_l - r) / 2.0))
            metal_parts.append(arc(r, second_w, 90.0, 180.0, arc_cx, arc_cy))
            if coup_l > r:
                metal_parts.append(rectangle(coup_l - r, second_w, (coup_l + r) / 2.0, down_l))
            second_metal = union(*metal_parts)

            # Cutout: vertical cutout, 90-deg circular cutout, horizontal cutout (ends flush at coup_l)
            cutout_parts = []
            if down_l > r:
                cutout_parts.append(
                    rectangle(second_w + 2.0 * second_g, down_l - r, 0.0, (down_l - r) / 2.0)
                )
            cutout_parts.append(arc(r, second_w + 2.0 * second_g, 90.0, 180.0, arc_cx, arc_cy))
            if coup_l > r:
                cutout_parts.append(
                    rectangle(
                        coup_l - r,
                        second_w + 2.0 * second_g,
                        (coup_l + r) / 2.0,
                        down_l,
                    )
                )
            second_cutout = union(*cutout_parts)

        # Primary bus CPW sits parallel above the secondary coupling arm:
        prime_cy = down_l + wg + coup_space + prime_g + prime_w / 2.0
        prime_cx = coup_l / 2.0
        prime_metal = rectangle(prime_l, prime_w, prime_cx, prime_cy)
        prime_cutout = rectangle(prime_l, prime_w + 2.0 * prime_g, prime_cx, prime_cy)

        metal = union(second_metal, prime_metal)
        cutout = union(second_cutout, prime_cutout)

        if guard > 0.0:
            min_x, min_y, max_x, max_y = cutout.bounds
            cutout_w = max_x - min_x
            cutout_h = max_y - min_y
            cutout_cx = (min_x + max_x) / 2.0
            cutout_cy = (min_y + max_y) / 2.0
            ground_outer = rectangle(
                cutout_w + 2.0 * guard,
                cutout_h + 2.0 * guard,
                cutout_cx,
                cutout_cy,
            )
            ground_ring = subtract(ground_outer, cutout)
            self.add_shape("ground", self.place(ground_ring))

        self.add_shape("cutout", self.place(cutout), subtract=True)
        self.add_shape("metal", self.place(metal))


# Aliases for lowercase naming conventions
charge_tee = ChargeTee
charge_claw = ChargeClaw
charge_arc = ChargeArc
read_tee = ReadTee
