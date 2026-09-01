import math

import pytest
from shapely.geometry import Polygon

from sqcanvas.utility.attr_dict import AttrDict
from sqcanvas.utility.exceptions import DimensionError, ExportError, SQCanvasError
from sqcanvas.utility.geom_utils import Vector, get_poly_pts, round_coordinate_sequence
from sqcanvas.utility.parsing import get_path, is_true, parse_value, set_path, walk_options
from sqcanvas.utility.units import format_dimension, parse_dimension


def test_attr_dict_nested_and_attributes():
    cfg = AttrDict(chip={"size": {"size_x": 9.0, "size_y": 6.0}}, elements=[{"name": "a"}])
    assert cfg.chip.size.size_x == 9.0
    assert cfg.chip.size.size_y == 6.0
    assert cfg["chip"]["size"]["size_x"] == 9.0
    assert cfg.elements[0].name == "a"

    cfg.chip.size.size_z = 0.5
    assert cfg["chip"]["size"]["size_z"] == 0.5

    del cfg.chip.size.size_z
    assert "size_z" not in cfg.chip.size
    with pytest.raises(AttributeError):
        _ = cfg.chip.size.size_z

    with pytest.raises(AttributeError):
        _ = cfg.non_existent

    with pytest.raises(AttributeError):
        del cfg.non_existent


def test_attr_dict_update_and_to_dict():
    cfg = AttrDict(a=1, b={"c": 2})
    cfg.update({"b": {"d": 3}, "e": 4})
    assert cfg.b.c == 2
    assert cfg.b.d == 3
    assert cfg.e == 4

    plain = cfg.to_dict()
    assert isinstance(plain, dict)
    assert not isinstance(plain["b"], AttrDict)
    assert plain == {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}
    assert "AttrDict" in repr(cfg)

    with pytest.raises(TypeError):
        cfg.update("not_a_mapping")


def test_units_parse_dimension():
    assert parse_dimension(10) == 10.0
    assert parse_dimension(12.5) == 12.5
    assert parse_dimension("10um") == pytest.approx(10.0)
    assert parse_dimension("1000nm") == pytest.approx(1.0)
    assert parse_dimension("1 mm") == pytest.approx(1000.0)
    assert parse_dimension("2 cm") == pytest.approx(20000.0)
    assert parse_dimension("1 m") == pytest.approx(1000000.0)
    assert parse_dimension("5micron") == pytest.approx(5.0)
    assert parse_dimension("5microns") == pytest.approx(5.0)
    assert parse_dimension("5\u03bcm") == pytest.approx(5.0)
    assert parse_dimension(["10um", "20um"]) == pytest.approx(10.0)

    with pytest.raises(DimensionError):
        parse_dimension(True)

    with pytest.raises(DimensionError):
        parse_dimension("invalid_dim")

    with pytest.raises(DimensionError):
        parse_dimension("10lightyears")

    with pytest.raises(DimensionError):
        parse_dimension({})


def test_units_format_dimension():
    assert format_dimension(10.0, "um") == "10um"
    assert format_dimension(1000.0, "mm") == "1mm"
    assert format_dimension(10.0) == "10um"
    with pytest.raises(DimensionError):
        format_dimension(1.0, "invalid_unit")


def test_parsing_helpers():
    assert is_true(True)
    assert is_true("True")
    assert is_true("1")
    assert is_true("yes")
    assert not is_true(False)
    assert not is_true("0")
    assert not is_true("no")

    assert parse_value("10um") == pytest.approx(10.0)
    assert parse_value("not_a_dim") == "not_a_dim"
    assert parse_value(123) == 123
    assert parse_value("") == ""

    options = {
        "pad_w": "455um",
        "pad_h": "90um",
        "count": 4,
        "nested": {"gap": "30um"},
        "list_vals": ["10um", "20um", {"sub_gap": "5um"}],
    }
    walked = walk_options(options)
    assert walked.pad_w == pytest.approx(455.0)
    assert walked.pad_h == pytest.approx(90.0)
    assert walked.count == 4
    assert walked.nested.gap == pytest.approx(30.0)
    assert walked.list_vals[0] == pytest.approx(10.0)
    assert walked.list_vals[2].sub_gap == pytest.approx(5.0)

    target = AttrDict()
    set_path(target, "chip.size.size_x", 10.0)
    assert target.chip.size.size_x == 10.0
    assert get_path(target, "chip.size.size_x") == 10.0
    assert get_path(target, "chip.size.non_existent", default=-1) == -1


def test_geom_utils_vector():
    v1 = Vector(3.0, 4.0)
    assert v1.magnitude == pytest.approx(5.0)
    assert v1.angle == pytest.approx(math.degrees(math.atan2(4.0, 3.0)))

    norm = v1.normalised()
    assert norm.magnitude == pytest.approx(1.0)
    assert norm.x == pytest.approx(0.6)
    assert norm.y == pytest.approx(0.8)

    with pytest.raises(ValueError):
        Vector(0.0, 0.0).normalised()

    v_from_pts = Vector.from_points([1.0, 2.0], [4.0, 6.0])
    assert v_from_pts.x == 3.0
    assert v_from_pts.y == 4.0

    rotated = Vector(1.0, 0.0).rotated(90)
    assert rotated.x == pytest.approx(0.0, abs=1e-9)
    assert rotated.y == pytest.approx(1.0)

    scaled = v1.scaled(2.0)
    assert scaled.x == 6.0 and scaled.y == 8.0

    v2 = Vector(1.0, 2.0)
    assert (v1 + v2).x == 4.0 and (v1 + v2).y == 6.0
    assert (v1 - v2).x == 2.0 and (v1 - v2).y == 2.0
    assert (v1 * 2).x == 6.0 and (v1 * 2).y == 8.0
    assert (v1 / 2).x == 1.5 and (v1 / 2).y == 2.0

    coords = list(v1)
    assert coords == [3.0, 4.0]
    assert "Vector" in repr(v1)


def test_geom_utils_poly_coords():
    poly = Polygon([(0, 0), (2, 0), (2, 3), (0, 3)])
    pts = get_poly_pts(poly)
    assert pts.shape == (5, 2)

    empty_poly = Polygon()
    empty_pts = get_poly_pts(empty_poly)
    assert empty_pts.shape == (0, 2)

    rounded = round_coordinate_sequence([(1.23456, 2.34567)], decimals=2)
    assert rounded == [(1.23, 2.35)]


def test_exceptions_hierarchy():
    assert issubclass(DimensionError, (SQCanvasError, ValueError))
    assert issubclass(ExportError, (SQCanvasError, RuntimeError))
