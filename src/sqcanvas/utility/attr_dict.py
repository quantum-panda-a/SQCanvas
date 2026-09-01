"""A dict that also exposes its keys as attributes, recursively."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class AttrDict(dict):
    """A ``dict`` whose nested values can be read and written as attributes.

    ``AttrDict`` exists so that deeply nested configuration (chip metadata,
    component options, exporter options) can be authored with dotted access::

        cfg = AttrDict(chip=AttrDict(size={"size_x": 9}))
        cfg.chip.size.size_x  # -> 9

    It is deliberately a ``dict`` subclass, so it round-trips through JSON and
    standard dict tooling without special handling.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__()
        if args:
            other = args[0] if isinstance(args[0], Mapping) else dict(args[0])
            self.update(other)
        if kwargs:
            self.update(kwargs)

    @staticmethod
    def _wrap(value: Any) -> Any:
        if isinstance(value, AttrDict):
            return value
        if isinstance(value, Mapping):
            return AttrDict(value)
        if isinstance(value, list):
            return [AttrDict._wrap(item) for item in value]
        if isinstance(value, tuple):
            return tuple(AttrDict._wrap(item) for item in value)
        return value

    def __getattr__(self, key: str) -> Any:
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = AttrDict._wrap(value)

    def __delattr__(self, key: str) -> None:
        try:
            del self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc

    def __setitem__(self, key: str, value: Any) -> None:
        super().__setitem__(key, AttrDict._wrap(value))

    def update(self, *args: Any, **kwargs: Any) -> None:  # type: ignore[override]
        """Deep-merge mappings into this one (nested dict values merge)."""
        for other in args:
            if not isinstance(other, Mapping):
                raise TypeError(f"update() must be given a mapping, not {type(other)!r}")
            for key, value in other.items():
                if isinstance(value, Mapping) and isinstance(self.get(key), Mapping):
                    if not isinstance(self[key], AttrDict):
                        self[key] = AttrDict(self[key])
                    self[key].update(value)
                else:
                    self[key] = AttrDict._wrap(value)
        for key, value in kwargs.items():
            if isinstance(value, Mapping) and isinstance(self.get(key), Mapping):
                if not isinstance(self[key], AttrDict):
                    self[key] = AttrDict(self[key])
                self[key].update(value)
            else:
                self[key] = AttrDict._wrap(value)

    def to_dict(self) -> dict[str, Any]:
        """Return a plain ``dict`` copy with nested values unwrapped."""
        return {
            key: (value.to_dict() if isinstance(value, AttrDict) else value)
            for key, value in self.items()
        }

    def __repr__(self) -> str:
        return f"AttrDict({dict.__repr__(self)})"
