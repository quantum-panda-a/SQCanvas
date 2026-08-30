"""Real-time property inspector widget for QCanvas components."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from qcanvas.gui.theme import Palette

if TYPE_CHECKING:
    from qcanvas.components.base import Component


class PropertyInspector(QWidget):
    """Inspector panel for live inspection and editing of component parameters."""

    component_changed = Signal(str)  # Emits component name when modified

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.current_component: Component | None = None
        self._input_fields: dict[str, QLineEdit] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(8)

        # Header Info Card
        self.header_card = QWidget()
        self.header_card.setStyleSheet(f"background-color: {Palette.BG_SURFACE}; border-radius: 6px; padding: 4px;")
        header_layout = QVBoxLayout(self.header_card)
        header_layout.setContentsMargins(8, 8, 8, 8)
        header_layout.setSpacing(2)

        self.lbl_title = QLabel("No Component Selected")
        self.lbl_title.setStyleSheet(f"font-weight: bold; font-size: 13px; color: {Palette.ACCENT_CYAN};")
        self.lbl_subtitle = QLabel("Select a component from tree or canvas")
        self.lbl_subtitle.setStyleSheet(f"color: {Palette.TEXT_MUTED}; font-size: 11px;")

        header_layout.addWidget(self.lbl_title)
        header_layout.addWidget(self.lbl_subtitle)
        main_layout.addWidget(self.header_card)

        # Scrollable form container
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background: transparent;")

        self.form_container = QWidget()
        self.form_container.setStyleSheet("background: transparent;")
        self.form_layout = QVBoxLayout(self.form_container)
        self.form_layout.setContentsMargins(0, 4, 0, 4)
        self.form_layout.setSpacing(10)

        self.scroll_area.setWidget(self.form_container)
        main_layout.addWidget(self.scroll_area, 1)

        # Bottom Action Buttons
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(6)

        self.btn_apply = QPushButton("Apply Changes")
        self.btn_apply.setObjectName("primaryButton")
        self.btn_apply.clicked.connect(self._on_apply_clicked)
        self.btn_apply.setEnabled(False)

        self.btn_reset = QPushButton("Reset")
        self.btn_reset.clicked.connect(self._on_reset_clicked)
        self.btn_reset.setEnabled(False)

        btn_bar.addWidget(self.btn_apply, 2)
        btn_bar.addWidget(self.btn_reset, 1)
        main_layout.addLayout(btn_bar)

    def set_component(self, comp: Component | None) -> None:
        """Inspect and display properties for the given component."""
        self.current_component = comp
        self._clear_form()

        if comp is None:
            self.lbl_title.setText("No Component Selected")
            self.lbl_subtitle.setText("Select a component to inspect parameters")
            self.btn_apply.setEnabled(False)
            self.btn_reset.setEnabled(False)
            return

        comp_type = type(comp).__name__
        self.lbl_title.setText(f"{comp.name}")
        self.lbl_subtitle.setText(f"Type: {comp_type}  ·  Layer: {comp.options.get('layer', 1)}")
        self.btn_apply.setEnabled(True)
        self.btn_reset.setEnabled(True)

        options: dict[str, Any] = getattr(comp, "options", {})

        def _fmt(v: Any) -> str:
            if isinstance(v, float) and v.is_integer():
                return str(int(v))
            return str(v)

        # Group 1: Transform / Placement
        transform_keys = ["pos_x", "pos_y", "orientation", "layer", "chip"]
        transform_opts = {k: _fmt(options[k]) for k in transform_keys if k in options}

        # Group 2: Geometry / Specific Options
        geometry_opts = {k: _fmt(v) for k, v in options.items() if k not in transform_keys}

        if transform_opts:
            self._add_group_section("Transform & Placement", transform_opts)

        if geometry_opts:
            self._add_group_section("Geometry Parameters", geometry_opts)

        self.form_layout.addStretch(1)

    def _clear_form(self) -> None:
        self._input_fields.clear()
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _add_group_section(self, title: str, options_dict: dict[str, str]) -> None:
        group = QGroupBox(title)
        layout = QFormLayout(group)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(6)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        for key, val in options_dict.items():
            lbl = QLabel(key)
            lbl.setStyleSheet(f"color: {Palette.TEXT_SECONDARY}; font-size: 11px; font-weight: 500;")
            edit = QLineEdit(val)
            edit.returnPressed.connect(self._on_apply_clicked)
            self._input_fields[key] = edit
            layout.addRow(lbl, edit)

        self.form_layout.addWidget(group)

    def _on_apply_clicked(self) -> None:
        if not self.current_component:
            return

        # Update options on the component
        for key, edit in self._input_fields.items():
            new_val = edit.text().strip()
            self.current_component.options[key] = new_val

        # Rebuild component geometry
        self.current_component.rebuild()
        self.component_changed.emit(self.current_component.name)

    def _on_reset_clicked(self) -> None:
        if self.current_component:
            self.set_component(self.current_component)


__all__ = ["PropertyInspector"]
