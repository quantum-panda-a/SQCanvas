"""The QCanvas desktop viewer window with CAD interaction."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QHeaderView,
    QLabel,
    QMainWindow,
    QPushButton,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from shapely.geometry import Point

from qcanvas.gui.canvas import MplCanvas
from qcanvas.viewer import view


class MainWindow(QMainWindow):
    """An interactive CAD viewer for QCanvas designs."""

    def __init__(self, design: Any | None = None) -> None:
        super().__init__()
        self.design = design or _demo_design()
        self.setWindowTitle("QCanvas Viewer")
        self.resize(1150, 780)

        # Set window icon if available
        icon_path = Path(__file__).parent / "resources" / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._selected_component: str | None = None

        # Canvas with embedded CAD interaction
        self.canvas = MplCanvas(self, width=7.0, height=6.0, dpi=100)
        self.setCentralWidget(self.canvas)

        # Setup Status Bar
        self._setup_statusbar()

        # Side Dock
        self._build_side_panel()

        # Hook canvas interaction callbacks
        self.canvas.set_interaction_callbacks(
            on_hover=self._on_hover_coord,
            on_click_point=self._on_canvas_click_point,
            on_autoscale=self.fit_all,
            on_shortcut=self._on_canvas_shortcut,
        )

        if hasattr(self.design, "add_listener"):
            self.design.add_listener(self._on_design_changed)

        self.refresh(preserve_view=False)

    # ---------------------------------------------------------------- Status Bar
    def _setup_statusbar(self) -> None:
        status_bar = QStatusBar(self)
        self.setStatusBar(status_bar)

        self.coord_label = QLabel(" X: --  Y: -- ")
        self.coord_label.setStyleSheet("font-family: monospace; font-weight: bold; color: #264653; padding: 2px 8px;")

        self.hint_label = QLabel(" [Scroll] Zoom  ·  [Left Drag] Pan  ·  [Right Drag] Box Zoom  ·  [A] Fit  ·  [R] Rebuild ")
        self.hint_label.setStyleSheet("color: #555555; padding: 2px 4px;")

        status_bar.addWidget(self.coord_label)
        status_bar.addWidget(self.hint_label, 1)

    def _on_hover_coord(self, x: float | None, y: float | None) -> None:
        """Update status bar coordinate display."""
        if x is None or y is None:
            self.coord_label.setText(" X: --  Y: -- ")
        else:
            unit = getattr(self.design, "units", "um")
            self.coord_label.setText(f" X: {x:+.2f} {unit}   Y: {y:+.2f} {unit} ")

    # ---------------------------------------------------------------- Side Panel
    def _build_side_panel(self) -> None:
        dock = QDockWidget(self)
        # Hide the redundant 'Scene' title bar completely
        dock.setTitleBarWidget(QWidget())
        dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)

        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(QLabel("Components"))

        # Two-column table: Name | Type
        self.component_table = QTableWidget(0, 2)
        self.component_table.setHorizontalHeaderLabels(["Name", "Type"])
        self.component_table.horizontalHeader().setStretchLastSection(True)
        self.component_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.component_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.component_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.component_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.component_table.verticalHeader().setVisible(False)
        self.component_table.setShowGrid(False)
        self.component_table.setStyleSheet("QTableWidget { border: 1px solid #e0e0e0; border-radius: 4px; }")
        self.component_table.itemSelectionChanged.connect(self._on_component_table_selection_changed)
        self.component_table.itemDoubleClicked.connect(self._on_component_table_double_clicked)
        self.component_list = self.component_table  # Alias for backward compatibility
        layout.addWidget(self.component_table)

        layout.addWidget(QLabel("Layer filter"))
        self.layer_filter = QComboBox()
        self.layer_filter.currentIndexChanged.connect(lambda _: self._draw(preserve_view=True))
        layout.addWidget(self.layer_filter)

        self.chip_outline = QCheckBox("Chip outline")
        self.chip_outline.setChecked(True)
        self.chip_outline.toggled.connect(lambda _: self._draw(preserve_view=True))
        layout.addWidget(self.chip_outline)

        self.show_grid = QCheckBox("Grid")
        self.show_grid.setChecked(True)
        self.show_grid.toggled.connect(lambda _: self._draw(preserve_view=True))
        layout.addWidget(self.show_grid)

        btn_fit = QPushButton("Fit View (A)")
        btn_fit.clicked.connect(self.fit_all)
        layout.addWidget(btn_fit)

        btn_rebuild = QPushButton("Rebuild Design (R)")
        btn_rebuild.clicked.connect(self.rebuild)
        layout.addWidget(btn_rebuild)

        export_btn = QPushButton("Export GDS…")
        export_btn.clicked.connect(self._export_gds)
        layout.addWidget(export_btn)

        layout.addStretch(1)
        dock.setWidget(panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)

    # ---------------------------------------------------------------- Pick & Selection
    def _on_canvas_click_point(self, x: float, y: float) -> None:
        """Find and select component at canvas click point."""
        hit_name = self._find_component_at(x, y)
        if hit_name:
            self.select_component(hit_name)
        else:
            self.clear_selection()

    def _find_component_at(self, x: float, y: float) -> str | None:
        """Find the component name under the coordinate point (x, y)."""
        pt = Point(x, y)
        records = self.design.shapes.as_records()

        # 1. Exact geometric containment
        for r in reversed(records):
            if r.geometry and not r.geometry.is_empty:
                try:
                    if r.geometry.contains(pt):
                        return r.component
                except Exception:
                    pass

        # 2. Proximity search (e.g. clicked near boundary or line)
        min_dist = float("inf")
        closest_comp = None
        for r in records:
            if r.geometry and not r.geometry.is_empty:
                try:
                    dist = r.geometry.distance(pt)
                    if dist < min_dist:
                        min_dist = dist
                        closest_comp = r.component
                except Exception:
                    pass

        # If within a reasonable click tolerance (e.g. 30 um)
        if min_dist <= 30.0:
            return closest_comp
        return None

    def select_component(self, name: str) -> None:
        """Select component by name, sync table selection and highlight on canvas."""
        self._selected_component = name

        # Synchronize table widget selection without triggering recursive signals
        self.component_table.blockSignals(True)
        for row in range(self.component_table.rowCount()):
            item = self.component_table.item(row, 0)
            if item and item.text() == name:
                self.component_table.selectRow(row)
                break
        self.component_table.blockSignals(False)

        bounds = self._get_component_bounds(name)
        self.canvas.highlight_component(name, bounds)

        unit = getattr(self.design, "units", "um")
        if bounds:
            w = bounds[2] - bounds[0]
            h = bounds[3] - bounds[1]
            self.hint_label.setText(
                f"Selected: {name} ({w:.1f} × {h:.1f} {unit})  ·  [A] Frame  ·  [Esc] Clear"
            )

    def clear_selection(self) -> None:
        """Deselect all components and clear canvas highlight."""
        self._selected_component = None
        self.component_table.blockSignals(True)
        self.component_table.clearSelection()
        self.component_table.blockSignals(False)
        self.canvas.clear_highlight()
        self.hint_label.setText(
            " [Scroll] Zoom  ·  [Left Drag] Pan  ·  [Right Drag] Box Zoom  ·  [A] Fit  ·  [R] Rebuild "
        )

    def _on_component_table_selection_changed(self) -> None:
        selected_rows = self.component_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            item = self.component_table.item(row, 0)
            if item:
                self.select_component(item.text())
        else:
            self.clear_selection()

    def _on_component_table_double_clicked(self, item) -> None:
        row = item.row()
        name_item = self.component_table.item(row, 0)
        if name_item:
            name = name_item.text()
            bounds = self._get_component_bounds(name)
            if bounds:
                self.canvas.zoom_to_rect(bounds)

    # ---------------------------------------------------------------- Bounds Helpers
    def _get_component_bounds(self, name: str) -> tuple[float, float, float, float] | None:
        records = self.design.shapes.by_component(name)
        boxes = [r.geometry.bounds for r in records if r.geometry and not r.geometry.is_empty]
        if not boxes:
            return None
        return (
            min(b[0] for b in boxes),
            min(b[1] for b in boxes),
            max(b[2] for b in boxes),
            max(b[3] for b in boxes),
        )

    def _get_all_component_bounds(self) -> dict[str, tuple[float, float, float, float]]:
        result = {}
        for name in self.design.shapes.components():
            b = self._get_component_bounds(name)
            if b is not None:
                result[name] = b
        return result

    # ---------------------------------------------------------------- Shortcuts & Actions
    def fit_all(self) -> None:
        """Fit view to selected component, all components, or chip."""
        if self._selected_component:
            b = self._get_component_bounds(self._selected_component)
            if b:
                self.canvas.zoom_to_rect(b)
                return

        bounds = self.design.shapes.bounds()
        if bounds != (0.0, 0.0, 0.0, 0.0):
            self.canvas.zoom_to_rect(bounds)

    def fit_chip(self) -> None:
        """Fit view to entire chip die outline."""
        if hasattr(self.design, "main_chip"):
            cx, cy = self.design.chip_centre()
            w, h = self.design.chip_extent()
            chip_bounds = (cx - w / 2.0, cy - h / 2.0, cx + w / 2.0, cy + h / 2.0)
            self.canvas.zoom_to_rect(chip_bounds)
        else:
            self.fit_all()

    def rebuild(self) -> None:
        """Rebuild design from scratch and refresh the view."""
        self.design.rebuild()
        self.refresh(preserve_view=True)

    def toggle_labels(self) -> None:
        """Toggle component name labels on canvas."""
        bounds_map = self._get_all_component_bounds()
        is_visible = self.canvas.toggle_all_labels(bounds_map)
        status = "shown" if is_visible else "hidden"
        self.hint_label.setText(f"Labels {status} ([L] toggle)")

    def _on_canvas_shortcut(self, key: str) -> None:
        """Dispatch shortcuts from Matplotlib CanvasInteraction."""
        k = key.lower()
        if key == "A":  # Shift + a
            self.fit_chip()
        elif k == "a":
            self.fit_all()
        elif k == "r":
            self.rebuild()
        elif k == "l":
            self.toggle_labels()
        elif key in ("escape", "Escape", "esc"):
            self.clear_selection()

    def keyPressEvent(self, event) -> None:
        """Qt-level keyboard shortcuts."""
        key = event.key()
        modifiers = event.modifiers()

        if key == Qt.Key.Key_A:
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                self.fit_chip()
            else:
                self.fit_all()
            event.accept()
        elif key == Qt.Key.Key_R:
            self.rebuild()
            event.accept()
        elif key == Qt.Key.Key_L:
            self.toggle_labels()
            event.accept()
        elif key == Qt.Key.Key_Escape:
            self.clear_selection()
            event.accept()
        else:
            super().keyPressEvent(event)

    # ---------------------------------------------------------------- Drawing & Refresh
    def _on_design_changed(self, _design: Any = None) -> None:
        """Slot invoked when underlying design updates."""
        from PySide6.QtWidgets import QApplication

        self.refresh(preserve_view=True)
        app = QApplication.instance()
        if app is not None:
            app.processEvents()

    def refresh(self, preserve_view: bool = True) -> None:
        """Reload components and redraw canvas."""
        names = self.design.shapes.components()
        if not names:
            names = [c.name for c in self.design.get_components()]

        self.component_table.blockSignals(True)
        self.component_table.setRowCount(len(names))
        selected_row = -1
        for row, name in enumerate(names):
            comp = self.design.components.get(name) if hasattr(self.design, "components") else None
            comp_type = type(comp).__name__ if comp is not None else "Component"

            item_name = QTableWidgetItem(name)
            item_type = QTableWidgetItem(comp_type)

            self.component_table.setItem(row, 0, item_name)
            self.component_table.setItem(row, 1, item_type)

            if self._selected_component and name == self._selected_component:
                selected_row = row

        if selected_row >= 0:
            self.component_table.selectRow(selected_row)
        else:
            self.component_table.clearSelection()
        self.component_table.blockSignals(False)

        layers = self.design.shapes.layers() or [1]
        current_layer = self.layer_filter.currentText()
        self.layer_filter.blockSignals(True)
        self.layer_filter.clear()
        self.layer_filter.addItem("All")
        for layer in layers:
            self.layer_filter.addItem(str(layer))
        if current_layer and current_layer in [str(l) for l in layers]:
            self.layer_filter.setCurrentText(current_layer)
        self.layer_filter.blockSignals(False)

        self._draw(preserve_view=preserve_view)

    def _draw(self, preserve_view: bool = False) -> None:
        """Render design onto canvas axes."""
        cur_xlim = None
        cur_ylim = None
        if preserve_view:
            try:
                cur_xlim = self.canvas.axes.get_xlim()
                cur_ylim = self.canvas.axes.get_ylim()
            except Exception:
                pass

        layer_text = self.layer_filter.currentText()
        layers = [int(layer_text)] if layer_text and layer_text != "All" else None

        view(
            self.design,
            ax=self.canvas.axes,
            layers=layers,
            chip_outline=self.chip_outline.isChecked(),
            grid=self.show_grid.isChecked(),
        )

        self.canvas.refresh_interaction_axes()

        # Restore view limits if requested
        if preserve_view and cur_xlim is not None and cur_ylim is not None and cur_xlim != (0.0, 1.0):
            self.canvas.axes.set_xlim(cur_xlim)
            self.canvas.axes.set_ylim(cur_ylim)

        # Restore component highlight if active
        if self._selected_component:
            bounds = self._get_component_bounds(self._selected_component)
            self.canvas.highlight_component(self._selected_component, bounds)

        self.canvas.draw()

    def _export_gds(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export GDS", "qcanvas.gds", "GDS files (*.gds)")
        if path:
            self.design.export("gds", filepath=path)

    def closeEvent(self, event) -> None:
        """Clean up listeners and disconnect interaction handlers."""
        if hasattr(self.design, "remove_listener"):
            self.design.remove_listener(self._on_design_changed)
        self.canvas.interaction.disconnect()
        super().closeEvent(event)


def _demo_design():
    """Build a demo design so the window opens with content."""
    from qcanvas.components import DualPadTransmon
    from qcanvas.designs import PlanarDesign

    design = PlanarDesign()
    DualPadTransmon(design, "Q1", options={"pos_x": "-2000um", "pos_y": "0.0um"})
    DualPadTransmon(design, "Q2", options={"pos_x": "2000um", "pos_y": "500um"})
    return design
