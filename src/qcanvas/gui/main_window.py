"""The QCanvas desktop viewer window."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDockWidget,
    QLabel,
    QListWidget,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from qcanvas.gui.canvas import MplCanvas, NavigationToolbar
from qcanvas.viewer import view


class MainWindow(QMainWindow):
    """A minimal viewer: a list of components, a layer filter, and a canvas.

    This is intentionally a *display-only* window. It never edits geometry; it
    just re-exports the design through the matplotlib exporter.
    """

    def __init__(self, design: Any | None = None) -> None:
        super().__init__()
        self.design = design or _demo_design()
        self.setWindowTitle("QCanvas")
        self.resize(1100, 750)

        self.canvas = MplCanvas(self, width=7.0, height=6.0, dpi=100)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.addToolBar(self.toolbar)
        self.setCentralWidget(self.canvas)

        self._build_side_panel()
        if hasattr(self.design, "add_listener"):
            self.design.add_listener(self._on_design_changed)
        self.refresh()

    def _on_design_changed(self, _design: Any = None) -> None:
        """Slot invoked when the underlying design changes."""
        from PySide6.QtWidgets import QApplication

        self.refresh()
        app = QApplication.instance()
        if app is not None:
            app.processEvents()

    def closeEvent(self, event) -> None:
        """Clean up design listeners upon window closure."""
        if hasattr(self.design, "remove_listener"):
            self.design.remove_listener(self._on_design_changed)
        super().closeEvent(event)

    # ------------------------------------------------------------------ panels
    def _build_side_panel(self) -> None:
        dock = QDockWidget("Scene", self)
        dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)

        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.addWidget(QLabel("Components"))

        self.component_list = QListWidget()
        self.component_list.itemSelectionChanged.connect(self.refresh)
        layout.addWidget(self.component_list)

        layout.addWidget(QLabel("Layer filter"))
        self.layer_filter = QComboBox()
        layout.addWidget(self.layer_filter)

        self.chip_outline = QCheckBox("Chip outline")
        self.chip_outline.setChecked(True)
        self.chip_outline.toggled.connect(self.refresh)
        layout.addWidget(self.chip_outline)

        export_btn = QPushButton("Export GDS…")
        export_btn.clicked.connect(self._export_gds)
        layout.addWidget(export_btn)

        layout.addStretch(1)
        dock.setWidget(panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)

    # ------------------------------------------------------------------ actions
    def refresh(self) -> None:
        """Reload the component/layer lists and redraw the canvas."""
        selected = {item.text() for item in self.component_list.selectedItems()}
        names = self.design.shapes.components()
        self.component_list.blockSignals(True)
        self.component_list.clear()
        if not names:
            names = [c.name for c in self.design.get_components()]
        self.component_list.addItems(names)
        for idx in range(self.component_list.count()):
            if self.component_list.item(idx).text() in selected:
                self.component_list.item(idx).setSelected(True)
        self.component_list.blockSignals(False)

        layers = self.design.shapes.layers() or [1]
        self.layer_filter.blockSignals(True)
        self.layer_filter.clear()
        self.layer_filter.addItems([str(layer) for layer in layers])
        self.layer_filter.blockSignals(False)

        self._draw()

    def _draw(self) -> None:
        selected = [item.text() for item in self.component_list.selectedItems()]
        layer_text = self.layer_filter.currentText()
        layers = [int(layer_text)] if layer_text else None
        view(
            self.design,
            ax=self.canvas.axes,
            components=selected or None,
            layers=layers,
            chip_outline=self.chip_outline.isChecked(),
        )
        self.canvas.draw()

    def _export_gds(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getSaveFileName(self, "Export GDS", "qcanvas.gds", "GDS files (*.gds)")
        if path:
            self.design.export("gds", filepath=path)


def _demo_design():
    """Build a small demo design so the window opens with something on screen."""
    from qcanvas.components import TransmonPocket
    from qcanvas.designs import PlanarDesign

    design = PlanarDesign()
    TransmonPocket(design, "Q1", options={"pos_x": "-2000um", "pos_y": "0.0um"})
    TransmonPocket(design, "Q2", options={"pos_x": "2000um", "pos_y": "500um"})
    return design
