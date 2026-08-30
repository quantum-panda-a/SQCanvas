"""Base class for drawable, parameterized components."""

from __future__ import annotations

from typing import Any

from qcanvas.draw import rotate, translate
from qcanvas.utility import AttrDict, parse_dimension, walk_options


class Component:
    """The unit of shape authoring.

    A component declares a set of default options (dimensions as strings,
    positions, layer), and implements :meth:`make` to turn those options into
    shapes that it registers on its parent design via :meth:`add_shape`.

    Components never draw themselves; they only produce shapes. An exporter
    later consumes those shapes from the design's store.
    """

    #: Defaults merged under any options passed at construction time.
    default_options = AttrDict(
        pos_x="0.0um",
        pos_y="0.0um",
        orientation="0",
        chip="main",
        layer="1",
    )

    def __init__(self, design: Any, name: str, options: dict[str, Any] | None = None) -> None:
        self.design = design
        self.name = name
        self.options = self._merge_options(options or {})
        self.design.register_component(self)
        self.make()
        if hasattr(self.design, "notify_changed"):
            self.design.notify_changed()

    # -------------------------------------------------------------- options
    def _merge_options(self, supplied: dict[str, Any]) -> AttrDict:
        merged = AttrDict(Component.default_options)
        merged.update(self.default_options)
        merged.update(supplied)
        return walk_options(merged)

    def __getitem__(self, key: str) -> Any:
        return self.options[key]

    # ------------------------------------------------------------ shapes
    def make(self) -> None:
        """Generate this component's shapes.

        Subclasses implement this and call :meth:`add_shape` for each shape.
        """
        raise NotImplementedError("Component subclasses must implement make().")

    def rebuild(self) -> None:
        """Drop this component's shapes from the store, then regenerate them."""
        self.design.remove_shapes(component=self.name)
        self.make()
        if hasattr(self.design, "notify_changed"):
            self.design.notify_changed()

    def add_shape(
        self,
        label: str,
        geometry: Any,
        *,
        layer: int | None = None,
        subtract: bool = False,
        helper: bool = False,
        kind: str = "poly",
        width: float | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Register a shape on the parent design, tagged with this component's name."""
        layer = int(float(self.options.layer)) if layer is None else layer
        return self.design.add_shape(
            component=self.name,
            label=label,
            geometry=geometry,
            layer=layer,
            subtract=subtract,
            helper=helper,
            kind=kind,
            width=width,
            metadata=metadata,
        )

    # ------------------------------------------------------------ transforms
    @property
    def origin(self) -> tuple[float, float]:
        """Component placement in design units (micrometres)."""
        return (parse_dimension(self.options.pos_x), parse_dimension(self.options.pos_y))

    @property
    def rotation(self) -> float:
        return float(self.options.orientation)

    def place(self, geometry: Any) -> Any:
        """Apply this component's position and orientation to a local shape."""
        x, y = self.origin
        return translate(rotate(geometry, self.rotation, origin=(0.0, 0.0)), x=x, y=y)

    @property
    def chip(self) -> str:
        return str(self.options.chip)

    @property
    def layer(self) -> int:
        return int(float(self.options.layer))

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name!r})"
