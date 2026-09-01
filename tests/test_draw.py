import matplotlib.pyplot as plt
import pytest
from shapely.geometry import LineString, Point, Polygon

from sqcanvas.draw.basic import (
    _iter_func_geom_,
    arc,
    buffer,
    circle,
    flip_merge,
    is_rectangle,
    rectangle,
    rotate,
    scale,
    subtract,
    translate,
    union,
)
from sqcanvas.draw.mpl import draw_records, figure_spawn


def test_circle():
    c = circle(10.0, 5.0, 5.0)
    assert isinstance(c, Polygon)
    assert c.is_valid
    assert c.centroid.x == pytest.approx(5.0)
    assert c.centroid.y == pytest.approx(5.0)


def test_rectangle():
    rect = rectangle(2.0, 1.0, xoff=1.0, yoff=2.0)
    assert isinstance(rect, Polygon)
    minx, miny, maxx, maxy = rect.bounds
    assert minx == pytest.approx(0.0)
    assert maxx == pytest.approx(2.0)
    assert miny == pytest.approx(1.5)
    assert maxy == pytest.approx(2.5)
    assert is_rectangle(rect)


def test_rectangle_fillet():
    # Normal fillet
    rect = rectangle(100.0, 50.0, fillet=10.0)
    assert isinstance(rect, Polygon)
    assert rect.is_valid
    assert rect.bounds == pytest.approx((-50.0, -25.0, 50.0, 25.0))
    # A filleted rectangle has rounded corners and thus area < w * h
    assert rect.area < 100.0 * 50.0
    assert not is_rectangle(rect)
    assert len(rect.exterior.coords) > 5

    # Clamped fillet (fillet > min(w, h)/2)
    rect_clamped = rectangle(20.0, 20.0, fillet=50.0)
    assert rect_clamped.is_valid
    assert rect_clamped.bounds == pytest.approx((-10.0, -10.0, 10.0, 10.0))
    # Should approximate a circle of radius 10
    import math
    assert rect_clamped.area == pytest.approx(math.pi * 100.0, rel=1e-2)

    # Offset with fillet
    rect_off = rectangle(40.0, 20.0, xoff=10.0, yoff=5.0, fillet=5.0)
    assert rect_off.bounds == pytest.approx((-10.0, -5.0, 30.0, 15.0))


def test_arc_and_fillet():
    # Plain arc
    a0 = arc(100.0, 20.0, 0.0, 90.0)
    assert isinstance(a0, Polygon)
    assert a0.is_valid

    # Filleted arc
    a_fillet = arc(100.0, 20.0, 0.0, 90.0, fillet=4.0)
    assert isinstance(a_fillet, Polygon)
    assert a_fillet.is_valid
    assert a_fillet.area < a0.area

    # Semicircular round cap
    a_round = arc(100.0, 20.0, 0.0, 90.0, fillet=10.0)
    assert a_round.is_valid


def test_transforms():
    rect = rectangle(2.0, 2.0)
    moved = translate(rect, 3.0, 4.0)
    assert moved.bounds == pytest.approx((2.0, 3.0, 4.0, 5.0))

    scaled = scale(rect, 2.0, 3.0)
    assert scaled.bounds == pytest.approx((-2.0, -3.0, 2.0, 3.0))

    rotated = rotate(rect, 45.0)
    assert isinstance(rotated, Polygon)


def test_boolean_ops():
    r1 = rectangle(2.0, 2.0)
    r2 = rectangle(1.0, 1.0)
    diff = subtract(r1, r2)
    assert isinstance(diff, Polygon)
    assert diff.area == pytest.approx(3.0)

    u = union(r1, r2)
    assert u.area == pytest.approx(4.0)

    u2 = union([r1, r2])
    assert u2.area == pytest.approx(4.0)

    with pytest.raises(ValueError):
        union()


def test_buffer_and_flip_merge():
    pt = Point(0, 0)
    buf_round = buffer(pt, 1.0, cap_style=1)
    assert buf_round.area == pytest.approx(3.14159, abs=0.1)

    line = LineString([(0, 0), (2, 0)])
    buf_line = buffer(line, 0.5)
    assert buf_line.area > 0

    merged = flip_merge(line, xfact=-1, yfact=1)
    assert len(merged) == 4


def test_is_rectangle():
    rect = rectangle(4.0, 2.0)
    assert is_rectangle(rect)

    triangle = Polygon([(0, 0), (2, 0), (1, 1)])
    assert not is_rectangle(triangle)
    assert not is_rectangle(Point(0, 0))


def test_iter_func_geom():
    r1 = rectangle(1.0, 1.0)
    r2 = rectangle(2.0, 2.0)

    # Single
    res_single = _iter_func_geom_(translate, r1, x=1.0, y=0.0)
    assert res_single.bounds == pytest.approx((-0.5 + 1.0, -0.5, 0.5 + 1.0, 0.5))

    # Dict
    res_dict = _iter_func_geom_(translate, {"a": r1, "b": r2}, x=1.0, y=1.0)
    assert "a" in res_dict and "b" in res_dict

    # List
    res_list = _iter_func_geom_(translate, [r1, r2], x=1.0, y=1.0)
    assert len(res_list) == 2

    # Non-geometry fallback
    assert _iter_func_geom_(translate, 123, x=1.0) == 123


def test_draw_mpl_records():
    fig, ax = figure_spawn((6.0, 6.0))
    rect = rectangle(1.0, 1.0)
    inner = rectangle(0.5, 0.5)
    hollow_poly = subtract(rect, inner)
    line = LineString([(0, 0), (1, 1)])
    records = [
        {"geometry": rect, "label": "metal", "subtract": False},
        {"geometry": hollow_poly, "label": "ground", "subtract": False},
        {"geometry": rect, "label": "cutout", "subtract": True},
        {"geometry": line, "label": "wire", "subtract": False},
        {"geometry": None},
    ]
    draw_records(
        ax,
        records,
        styles={
            "metal": {"facecolor": "#000", "edgecolor": "#000"},
            "ground": {"facecolor": "0.25", "edgecolor": "0.1"},
        },
        chip_outline=[(-5, -5), (5, -5), (5, 5), (-5, 5), (-5, -5)],
    )
    plt.close(fig)
