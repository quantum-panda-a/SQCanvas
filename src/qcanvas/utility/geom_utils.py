"""Geometry utilities shared by the drawing layer."""

from __future__ import annotations

import math
from collections.abc import Iterator, Sequence

import numpy as np
from shapely.geometry.base import BaseGeometry


class Vector:
    """A lightweight 2D vector used for placements and orientations.

    Coordinates are in design units (micrometres). The class offers the small
    set of affine helpers that component builders need (magnitude, direction,
    rotation, scaling, addition) while staying numpy-free at call sites.
    """

    def __init__(self, x: float = 0.0, y: float = 0.0) -> None:
        self.x = float(x)
        self.y = float(y)

    @classmethod
    def from_points(cls, start: Sequence[float], end: Sequence[float]) -> Vector:
        """Build a vector that points from ``start`` to ``end``."""
        return cls(end[0] - start[0], end[1] - start[1])

    @property
    def magnitude(self) -> float:
        return math.hypot(self.x, self.y)

    @property
    def angle(self) -> float:
        """Return the direction in degrees (0 is +X, counter-clockwise positive)."""
        return math.degrees(math.atan2(self.y, self.x))

    def normalised(self) -> Vector:
        length = self.magnitude
        if length == 0.0:
            raise ValueError("Cannot normalise a zero-length vector.")
        return Vector(self.x / length, self.y / length)

    def rotated(self, degrees: float) -> Vector:
        rad = math.radians(degrees)
        cos, sin = math.cos(rad), math.sin(rad)
        return Vector(self.x * cos - self.y * sin, self.x * sin + self.y * cos)

    def scaled(self, factor: float) -> Vector:
        return Vector(self.x * factor, self.y * factor)

    def __add__(self, other: Vector) -> Vector:
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector) -> Vector:
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, factor: float) -> Vector:
        return self.scaled(factor)

    def __truediv__(self, factor: float) -> Vector:
        return Vector(self.x / factor, self.y / factor)

    def __iter__(self) -> Iterator[float]:
        yield self.x
        yield self.y

    def __repr__(self) -> str:
        return f"Vector({self.x:g}, {self.y:g})"


def get_poly_pts(geometry: BaseGeometry) -> np.ndarray:
    """Return the exterior coordinates of a polygon as an Nx2 ndarray."""
    if geometry.is_empty:
        return np.empty((0, 2))
    coords = list(geometry.exterior.coords)
    return np.asarray(coords, dtype=float)


def round_coordinate_sequence(
    coords: Sequence[Sequence[float]], decimals: int = 1
) -> list[tuple[float, float]]:
    """Round an iterable of ``(x, y)`` coordinates to ``decimals`` places."""
    return [(round(float(x), decimals), round(float(y), decimals)) for x, y in coords]
