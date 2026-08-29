"""The shape store — the single source of truth for a design's shapes."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from shapely.geometry.base import BaseGeometry


@dataclass
class ShapeRecord:
    """One shape, together with the metadata an exporter needs to draw it.

    Attributes:
        component: name of the component that produced the shape.
        label: a short, human-readable name (also used to pick a style).
        geometry: the shapely geometry being represented.
        layer: integer manufacturing layer index.
        subtract: if True, this shape is carved out of a ground plane.
        helper: if True, this shape is auxiliary (labels, refpoints) and is
            ignored for physical bounds/export by default.
        kind: ``"poly"`` or ``"path"``.
        width: for ``kind="path"``, the path width in micrometres.
        metadata: free-form dict for exporter-specific extras.
    """

    component: str
    label: str
    geometry: BaseGeometry
    layer: int = 1
    subtract: bool = False
    helper: bool = False
    kind: str = "poly"
    width: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ShapeStore:
    """An ordered collection of :class:`ShapeRecord` objects.

    The store is intentionally a plain in-memory container. It exposes a small
    query surface so exporters can iterate over exactly the shapes they care
    about, while never mutating component shapes.
    """

    def __init__(self) -> None:
        self._records: list[ShapeRecord] = []

    def add(self, record: ShapeRecord) -> ShapeRecord:
        self._records.append(record)
        return record

    def add_many(self, records: Iterator[ShapeRecord] | list[ShapeRecord]) -> None:
        self._records.extend(records)

    def clear(self) -> None:
        self._records.clear()

    def remove(self, *, component: str | None = None, label: str | None = None) -> int:
        """Drop records matching the given predicates; returns the count removed."""
        kept = []
        removed = 0
        for record in self._records:
            if component is not None and record.component == component:
                removed += 1
                continue
            if label is not None and record.label == label:
                removed += 1
                continue
            kept.append(record)
        self._records = kept
        return removed

    def __iter__(self) -> Iterator[ShapeRecord]:
        return iter(self._records)

    def __len__(self) -> int:
        return len(self._records)

    def is_empty(self) -> bool:
        return not self._records

    # ------------------------------------------------------------------ queries
    def filter(
        self,
        *,
        component: str | None = None,
        layer: int | None = None,
        subtract: bool | None = None,
        kind: str | None = None,
        helper: bool | None = None,
    ) -> list[ShapeRecord]:
        """Return records matching all provided predicates."""
        result = []
        for record in self._records:
            if component is not None and record.component != component:
                continue
            if layer is not None and record.layer != layer:
                continue
            if subtract is not None and record.subtract != subtract:
                continue
            if kind is not None and record.kind != kind:
                continue
            if helper is not None and record.helper != helper:
                continue
            result.append(record)
        return result

    def by_component(self, component: str) -> list[ShapeRecord]:
        return self.filter(component=component)

    def by_layer(self, layer: int) -> list[ShapeRecord]:
        return self.filter(layer=layer)

    def components(self) -> list[str]:
        """Return the distinct component names present in the store."""
        seen: list[str] = []
        for record in self._records:
            if record.component not in seen:
                seen.append(record.component)
        return seen

    def layers(self) -> list[int]:
        """Return the distinct physical (non-empty) layer indices."""
        seen: list[int] = []
        for record in self._records:
            if record.layer not in seen:
                seen.append(record.layer)
        return sorted(seen)

    def bounds(self) -> tuple[float, float, float, float]:
        """Return ``(min_x, min_y, max_x, max_y)`` over non-helper geometries."""
        boxes = [r.geometry.bounds for r in self._records if not r.helper and not r.geometry.is_empty]
        if not boxes:
            return (0.0, 0.0, 0.0, 0.0)
        return (
            min(b[0] for b in boxes),
            min(b[1] for b in boxes),
            max(b[2] for b in boxes),
            max(b[3] for b in boxes),
        )

    def as_records(self) -> list[ShapeRecord]:
        return list(self._records)

    def __repr__(self) -> str:
        return f"ShapeStore({len(self._records)} records)"
