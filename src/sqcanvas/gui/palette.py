"""Component Palette Dock Widget for browsing, filtering, and selecting components in SQCanvas."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from sqcanvas.components.registry import COMPONENT_CATALOG, ComponentMeta
from sqcanvas.gui.theme import Palette

if TYPE_CHECKING:
    pass


class ComponentPaletteWidget(QWidget):
    """Component library tool palette for interactive circuit design."""

    #: Signal emitted when user selects a component to place. Passes ComponentMeta.
    component_selected = Signal(object)

    #: Signal emitted when user clicks Cancel placement.
    placement_cancelled = Signal()

    #: Signal emitted when grid snap setting changes (in micrometres).
    grid_snap_changed = Signal(float)

    GRID_SNAP_PRESETS = [
        ("Off (Free)", 0.0),
        ("10 µm", 10.0),
        ("25 µm", 25.0),
        ("50 µm (Default)", 50.0),
        ("100 µm", 100.0),
        ("250 µm", 250.0),
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.active_meta: ComponentMeta | None = None
        self._meta_map: dict[str, ComponentMeta] = {}

        self._build_ui()
        self._populate_components()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 1. Header Title
        lbl_header = QLabel("Component Library")
        lbl_header.setStyleSheet(
            f"font-weight: bold; color: {Palette.ACCENT_CYAN}; font-size: 11px; text-transform: uppercase;"
        )
        layout.addWidget(lbl_header)

        # 2. Search / Filter input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search library...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._filter_catalog)
        layout.addWidget(self.search_input)

        # 3. Grid Snapping Row
        snap_box = QHBoxLayout()
        lbl_snap = QLabel("Snap:")
        lbl_snap.setStyleSheet(f"color: {Palette.TEXT_SECONDARY}; font-size: 11px;")
        self.combo_snap = QComboBox()
        for label, val in self.GRID_SNAP_PRESETS:
            self.combo_snap.addItem(label, val)
        # Default to 50 um
        self.combo_snap.setCurrentIndex(3)
        self.combo_snap.currentIndexChanged.connect(self._on_snap_changed)
        snap_box.addWidget(lbl_snap)
        snap_box.addWidget(self.combo_snap, 1)
        layout.addLayout(snap_box)

        # 4. Component Category Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(14)
        self.tree.setAnimated(True)
        self.tree.setStyleSheet(
            f"""
            QTreeWidget {{
                background-color: {Palette.BG_CARD};
                border: 1px solid {Palette.BORDER_SUBTLE};
                border-radius: 4px;
                padding: 4px;
            }}
            QTreeWidget::item {{
                padding: 5px 6px;
                border-radius: 3px;
                margin: 1px 0;
            }}
            QTreeWidget::item:hover {{
                background-color: {Palette.BG_HOVER};
            }}
            QTreeWidget::item:selected {{
                background-color: {Palette.BG_ACTIVE};
                border: 1px solid {Palette.ACCENT_CYAN};
            }}
            """
        )
        self.tree.itemClicked.connect(self._on_tree_item_clicked)
        self.tree.itemDoubleClicked.connect(self._on_tree_item_double_clicked)
        layout.addWidget(self.tree, 1)

        # 5. Armed Component Banner / Cancel Button
        self.banner_frame = QFrame()
        self.banner_frame.setStyleSheet(
            f"background-color: {Palette.BG_SURFACE}; border: 1px solid {Palette.BORDER_DEFAULT}; border-radius: 4px; padding: 4px;"
        )
        banner_layout = QHBoxLayout(self.banner_frame)
        banner_layout.setContentsMargins(4, 2, 4, 2)
        banner_layout.setSpacing(6)

        self.lbl_armed_status = QLabel("Click a component to place")
        self.lbl_armed_status.setStyleSheet(
            f"color: {Palette.TEXT_MUTED}; font-size: 11px;"
        )
        self.btn_cancel_placement = QPushButton("✕ Cancel")
        self.btn_cancel_placement.setToolTip("Cancel placement mode [Esc]")
        self.btn_cancel_placement.setVisible(False)
        self.btn_cancel_placement.setStyleSheet(
            f"background-color: {Palette.BG_HOVER}; color: {Palette.ACCENT_RUBY}; border: 1px solid {Palette.BORDER_DEFAULT}; padding: 2px 8px; font-size: 11px;"
        )
        self.btn_cancel_placement.clicked.connect(self._on_cancel_clicked)

        banner_layout.addWidget(self.lbl_armed_status, 1)
        banner_layout.addWidget(self.btn_cancel_placement)
        layout.addWidget(self.banner_frame)

    def _populate_components(self) -> None:
        """Populate tree widget grouped by category."""
        self.tree.clear()
        self._meta_map.clear()

        # Group components by category
        categories: dict[str, list[ComponentMeta]] = {}
        for meta in COMPONENT_CATALOG:
            categories.setdefault(meta.category, []).append(meta)

        header_font = QFont()
        header_font.setBold(True)

        for cat_name, items in categories.items():
            cat_item = QTreeWidgetItem(self.tree)
            cat_item.setText(0, f"📁 {cat_name} ({len(items)})")
            cat_item.setFont(0, header_font)
            cat_item.setForeground(0, QColor(Palette.ACCENT_CYAN))
            cat_item.setFlags(cat_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)

            for meta in items:
                child = QTreeWidgetItem(cat_item)
                child.setText(0, f"{meta.icon}  {meta.display_name}")
                child.setToolTip(0, f"<b>{meta.display_name}</b><br>{meta.description}<br><i>Click to place on canvas (Prefix: {meta.default_prefix})</i>")
                # Store class name in data
                key = meta.cls.__name__
                child.setData(0, Qt.ItemDataRole.UserRole, key)
                self._meta_map[key] = meta

            cat_item.setExpanded(True)

    def _filter_catalog(self, text: str) -> None:
        """Dynamically filter categories and items according to search query."""
        query = text.strip().lower()
        for i in range(self.tree.topLevelItemCount()):
            cat_item = self.tree.topLevelItem(i)
            cat_match_count = 0
            for j in range(cat_item.childCount()):
                child = cat_item.child(j)
                key = child.data(0, Qt.ItemDataRole.UserRole)
                meta = self._meta_map.get(key)
                if meta is None:
                    continue
                match = (
                    query in meta.display_name.lower()
                    or query in meta.description.lower()
                    or query in meta.category.lower()
                    or query in meta.cls.__name__.lower()
                )
                child.setHidden(not match)
                if match:
                    cat_match_count += 1

            cat_item.setHidden(cat_match_count == 0)
            if query and cat_match_count > 0:
                cat_item.setExpanded(True)

    def _on_snap_changed(self, index: int) -> None:
        snap_val = float(self.combo_snap.currentData())
        self.grid_snap_changed.emit(snap_val)

    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        key = item.data(0, Qt.ItemDataRole.UserRole)
        if not key or key not in self._meta_map:
            return
        meta = self._meta_map[key]
        self.set_active_component(meta)
        self.component_selected.emit(meta)

    def _on_tree_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        self._on_tree_item_clicked(item, column)

    def _on_cancel_clicked(self) -> None:
        self.set_active_component(None)
        self.placement_cancelled.emit()

    def set_active_component(self, meta: ComponentMeta | None) -> None:
        """Update active armed component in UI."""
        self.active_meta = meta
        if meta is not None:
            self.lbl_armed_status.setText(f"Armed: {meta.icon} {meta.display_name}")
            self.lbl_armed_status.setStyleSheet(
                f"color: {Palette.ACCENT_AMBER}; font-weight: bold; font-size: 11px;"
            )
            self.btn_cancel_placement.setVisible(True)
        else:
            self.lbl_armed_status.setText("Click a component to place")
            self.lbl_armed_status.setStyleSheet(
                f"color: {Palette.TEXT_MUTED}; font-size: 11px;"
            )
            self.btn_cancel_placement.setVisible(False)
            self.tree.clearSelection()

    def get_current_grid_snap(self) -> float:
        """Return the currently selected grid snap value in micrometres."""
        return float(self.combo_snap.currentData() or 50.0)
