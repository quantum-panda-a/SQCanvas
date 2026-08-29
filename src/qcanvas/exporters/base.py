"""The pluggable exporter base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar


class Exporter(ABC):
    """Base class for all exporters of a :class:`~qcanvas.designs.Design`.

    An exporter reads a design's *shape store* and produces a concrete
    artifact: a figure, a GDS file, or anything else. Subclasses set a unique
    ``name`` and implement :meth:`export`. Registration is automatic.

    Exporters are side-effect-free on the design: they may read, never mutate.
    """

    registry: ClassVar[dict[str, type[Exporter]]] = {}
    name: ClassVar[str] = "base"

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if getattr(cls, "name", None):
            Exporter.registry[cls.name] = cls

    @classmethod
    def for_name(cls, name: str) -> type[Exporter]:
        """Look up a registered exporter class by name."""
        try:
            return cls.registry[name]
        except KeyError as exc:
            raise KeyError(f"Exporter '{name}' not registered. Available: {sorted(cls.registry)}") from exc

    @classmethod
    def names(cls) -> list[str]:
        return sorted(cls.registry)

    @abstractmethod
    def export(self, design: Any, **options: Any) -> Any:
        """Export ``design`` to an artifact, honoring ``options``."""

    def __repr__(self) -> str:
        return f"<{type(self).__name__} name={type(self).name!r}>"
