"""The base design container."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from typing import TYPE_CHECKING, Any

from qcanvas.config import CHIP_DEFAULTS, DEFAULT_EXPORTER, DESIGN_DEFAULTS
from qcanvas.exporters import Exporter
from qcanvas.shapes import ShapeRecord, ShapeStore
from qcanvas.utility import AttrDict

if TYPE_CHECKING:
    from qcanvas.components import Component


class Design:
    """Top-level container that owns everything about a layout.

    A design holds:
      * the named :class:`~qcanvas.components.Component` instances,
      * a :class:`~qcanvas.shapes.ShapeStore` that accumulates their shapes,
      * chip metadata (size, material) and design variables,
      * access to the pluggable :class:`~qcanvas.exporters.Exporter` registry.

    The store is the single read source for exporters; components only ever
    *add* to it. This is what keeps shape authoring and exporting decoupled.
    """

    def __init__(
        self,
        metadata: dict[str, Any] | None = None,
        overwrite_enabled: bool = False,
    ) -> None:
        self.name = "Design"
        self.units = DESIGN_DEFAULTS.units
        self.variables = AttrDict(DESIGN_DEFAULTS.variables)
        self.chips = AttrDict(deepcopy(CHIP_DEFAULTS.to_dict()))

        self.components: dict[str, Component] = {}
        self._shapes = ShapeStore()
        self.overwrite_enabled = overwrite_enabled
        self._metadata = AttrDict(design_name=self.name, notes="")
        self._exporter_cache: dict[str, Exporter] = {}
        self._change_listeners: list[Callable[[Design], None]] = []
        if metadata:
            self._metadata.update(metadata)

    # ------------------------------------------------------- change listeners
    def add_listener(self, listener: Callable[[Design], None]) -> None:
        """Register a callback to be invoked whenever the design changes."""
        if listener not in self._change_listeners:
            self._change_listeners.append(listener)

    def remove_listener(self, listener: Callable[[Design], None]) -> None:
        """Unregister a previously added change callback."""
        if listener in self._change_listeners:
            self._change_listeners.remove(listener)

    def notify_changed(self) -> None:
        """Notify all registered listeners that the design content has updated."""
        for listener in list(self._change_listeners):
            try:
                listener(self)
            except Exception:
                pass

    def open_gui(self) -> Any:
        """Launch the desktop GUI viewer for this design non-blockingly."""
        from qcanvas.gui import launch

        return launch(self)

    # ------------------------------------------------------- component registry
    def register_component(self, component: Component) -> None:
        """Record a newly built component on this design."""
        name = component.name
        if name in self.components:
            if not self.overwrite_enabled:
                raise ValueError(f"Component '{name}' already exists on design '{self.name}'.")
            self.remove_shapes(component=name)
        self.components[name] = component

    def remove_component(self, name: str) -> None:
        """Remove a component by name from the design's registry."""
        if name not in self.components:
            raise KeyError(f"No component named '{name}' on design '{self.name}'.")
        self.remove_shapes(component=name)
        del self.components[name]
        self.notify_changed()

    def remove_shapes(self, *, component: str | None = None, label: str | None = None) -> int:
        """Drop shapes from the store (optionally scoped to a component/label)."""
        return self._shapes.remove(component=component, label=label)

    def get_components(self) -> list[Component]:
        return list(self.components.values())

    def rebuild_component(self, name: str) -> None:
        """Rebuild the shapes of one component in place."""
        if name not in self.components:
            raise KeyError(f"No component named '{name}' on design '{self.name}'.")
        self.components[name].rebuild()

    def rebuild(self) -> None:
        """Regenerate every component's shapes from scratch."""
        self._shapes.clear()
        for component in self.components.values():
            component.make()
        self.notify_changed()

    # ------------------------------------------------------- shapes access
    @property
    def shapes(self) -> ShapeStore:
        return self._shapes

    def add_shape(
        self,
        component: str,
        label: str,
        geometry: Any,
        *,
        layer: int = 1,
        subtract: bool = False,
        helper: bool = False,
        kind: str = "poly",
        width: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ShapeRecord:
        """Add a shape to the design's shape store (called by components)."""
        record = ShapeRecord(
            component=component,
            label=label,
            geometry=geometry,
            layer=int(layer),
            subtract=subtract,
            helper=helper,
            kind=kind,
            width=width,
            metadata=metadata or {},
        )
        return self._shapes.add(record)

    # ------------------------------------------------------- exporting
    def exporter(self, name: str | None = None) -> Exporter:
        """Return a (cached) exporter instance by registered name."""
        name = name or DEFAULT_EXPORTER
        if name not in Exporter.registry:
            raise KeyError(f"Exporter '{name}' is not registered. Available: {list(Exporter.registry)}")
        if name not in self._exporter_cache:
            self._exporter_cache[name] = Exporter.registry[name]()
        return self._exporter_cache[name]

    def export(self, name: str | None = None, **options: Any) -> Any:
        """Export this design to a concrete artifact using an exporter."""
        return self.exporter(name).export(self, **options)
