"""Component catalog and discovery registry for QCanvas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from qcanvas.components.base import Component


@dataclass(frozen=True)
class ComponentMeta:
    """Metadata descriptor for a registered QCanvas component."""

    cls: Type[Component]
    category: str
    display_name: str
    icon: str
    description: str
    default_prefix: str


def _build_catalog() -> list[ComponentMeta]:
    from qcanvas.components.coupler import ChargeArc, ChargeClaw, ChargeTee, ReadTee
    from qcanvas.components.marker import AlignmentMarker, CasingMarker, Marker, PackagingMarker
    from qcanvas.components.ports import (
        CPWOpen,
        CPWShort,
        Launchpad,
        LaunchpadWirebond,
        OpenToGround,
        ShortToGround,
    )
    from qcanvas.components.qubits import (
        CircularTransmon,
        CrossTransmon,
        DualPadTransmon,
        SinglePadTransmon,
    )
    from qcanvas.components.text import Text

    return [
        # --- Qubits ---
        ComponentMeta(
            cls=DualPadTransmon,
            category="Qubits",
            display_name="Dual-Pad Transmon",
            icon="💠",
            description="Classic pocket transmon with dual capacitive rectangular pads.",
            default_prefix="Q",
        ),
        ComponentMeta(
            cls=SinglePadTransmon,
            category="Qubits",
            display_name="Single-Pad Transmon",
            icon="▫️",
            description="Single charge island transmon referencing ground.",
            default_prefix="Q",
        ),
        ComponentMeta(
            cls=CrossTransmon,
            category="Qubits",
            display_name="Cross Transmon (Xmon)",
            icon="➕",
            description="Cross-shaped 4-arm planar transmon qubit.",
            default_prefix="Q",
        ),
        ComponentMeta(
            cls=CircularTransmon,
            category="Qubits",
            display_name="Circular Transmon",
            icon="⚪",
            description="Concentric circular electrode transmon.",
            default_prefix="Q",
        ),
        # --- Couplers ---
        ComponentMeta(
            cls=ChargeClaw,
            category="Couplers",
            display_name="Charge Claw",
            icon="🦀",
            description="Capacitive claw coupler for qubit readout and bus coupling.",
            default_prefix="claw_",
        ),
        ComponentMeta(
            cls=ChargeTee,
            category="Couplers",
            display_name="Charge Tee",
            icon="┬",
            description="T-shaped capacitive coupling pad.",
            default_prefix="tee_",
        ),
        ComponentMeta(
            cls=ChargeArc,
            category="Couplers",
            display_name="Charge Arc",
            icon="⌒",
            description="Curved capacitive coupling electrode segment.",
            default_prefix="arc_",
        ),
        ComponentMeta(
            cls=ReadTee,
            category="Couplers",
            display_name="Readout Tee",
            icon="⊤",
            description="Readout resonator feedline tee coupling segment.",
            default_prefix="readout_",
        ),
        # --- Ports & Pads ---
        ComponentMeta(
            cls=Launchpad,
            category="Ports & Pads",
            display_name="Launchpad (RF Port)",
            icon="🔌",
            description="High-frequency coplanar wirebond launch pad.",
            default_prefix="port_",
        ),
        ComponentMeta(
            cls=LaunchpadWirebond,
            category="Ports & Pads",
            display_name="Launchpad Wirebond",
            icon="🏷️",
            description="Standard wirebond pad for microwave I/O connection.",
            default_prefix="pad_",
        ),
        ComponentMeta(
            cls=CPWOpen,
            category="Ports & Pads",
            display_name="CPW Open End",
            icon="⭕",
            description="Open-circuit termination for CPW transmission line.",
            default_prefix="open_",
        ),
        ComponentMeta(
            cls=CPWShort,
            category="Ports & Pads",
            display_name="CPW Short End",
            icon="⬛",
            description="Short-circuit termination to ground plane.",
            default_prefix="short_",
        ),
        ComponentMeta(
            cls=OpenToGround,
            category="Ports & Pads",
            display_name="Open to Ground",
            icon="🔲",
            description="Open cutout boundary to ground plane.",
            default_prefix="open_gnd_",
        ),
        ComponentMeta(
            cls=ShortToGround,
            category="Ports & Pads",
            display_name="Short to Ground",
            icon="▪️",
            description="Direct connection to ground plane.",
            default_prefix="short_gnd_",
        ),
        # --- Markers ---
        ComponentMeta(
            cls=AlignmentMarker,
            category="Markers",
            display_name="Alignment Marker",
            icon="🎯",
            description="Optical and e-beam lithography cross-alignment marker.",
            default_prefix="mark_",
        ),
        ComponentMeta(
            cls=PackagingMarker,
            category="Markers",
            display_name="Packaging Marker",
            icon="📐",
            description="Dicing and chip edge alignment marker.",
            default_prefix="pack_",
        ),
        ComponentMeta(
            cls=CasingMarker,
            category="Markers",
            display_name="Casing Marker",
            icon="⏹️",
            description="Outer shield / casing frame marker.",
            default_prefix="case_",
        ),
        # --- Text ---
        ComponentMeta(
            cls=Text,
            category="Text & Labels",
            display_name="Text Annotation",
            icon="🔤",
            description="GDS lithography text label and logo lettering.",
            default_prefix="text_",
        ),
    ]


COMPONENT_CATALOG: list[ComponentMeta] = _build_catalog()


def get_component_catalog() -> list[ComponentMeta]:
    """Return the list of all registered component descriptors."""
    return list(COMPONENT_CATALOG)


def get_component_meta(name_or_cls: str | Type[Component]) -> ComponentMeta | None:
    """Find component metadata by class name, display name, or class object."""
    if isinstance(name_or_cls, str):
        target = name_or_cls.lower().strip()
        for meta in COMPONENT_CATALOG:
            if (
                meta.cls.__name__.lower() == target
                or meta.display_name.lower() == target
            ):
                return meta
    else:
        for meta in COMPONENT_CATALOG:
            if meta.cls is name_or_cls:
                return meta
    return None
