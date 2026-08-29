import matplotlib.pyplot as plt
import pytest
from shapely.geometry import LineString, Point, Polygon

from qcanvas.draw.basic import (
    _iter_func_geom_,
    buffer,
    flip_merge,
    is_rectangle,
    rectangle,
    rotate,
    scale,
    subtract,
    translate,
    union,
)
from qcanvas.draw.mpl import draw_records, figure_spawn


def test_rectangle():
    rect = rectangle(2.0, 1.0, xoff=1.0, yoff=2.0)
    assert isinstance(rect, Polygon)
    minx, miny, maxx, maxy = rect.bounds
    assert minx == pytest.approx(0.0)
    assert maxx == pytest.approx(2.0)
    assert miny == pytest.approx(1.5)
    assert maxy == pytest.approx(2.5)
    assert is_rectangle(rect)


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
        {"geometry": rect, "label": "pocket", "subtract": True},
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
