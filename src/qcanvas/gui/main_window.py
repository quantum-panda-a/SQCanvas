"""The QCanvas desktop CAD viewer and engineering design workspace."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from shapely.geometry import Point

from qcanvas.codegen import (
    ScriptLoadError,
    export_python_script,
    load_design_from_script,
)
from qcanvas.components.registry import ComponentMeta
from qcanvas.config import PRESET_THEMES, get_theme
from qcanvas.designs import PlanarDesign
from qcanvas.exporters.mpl import export_scene
from qcanvas.gui.canvas import MplCanvas
from qcanvas.gui.inspector import PropertyInspector
from qcanvas.gui.palette import ComponentPaletteWidget
from qcanvas.gui.theme import Palette, apply_dark_theme
from qcanvas.gui.watcher import ScriptWatcher

# Ordered list of preset themes for UI menus and dropdowns (clean names without serial numbers)
THEMES_CATALOG = [
    ("cyber", "Cyber Quantum (Default)"),
    ("nordic", "Nordic Amber (Science Gold)"),
    ("aurora", "Sycamore Aurora (Google Purple)"),
    ("paper", "Nature Clean Light (Publication)"),
    ("no002", "Prussian & Coral"),
    ("no005", "Morandi Sage & Rose"),
    ("no008", "Titanium & Gold"),
    ("no009", "Teal Lake & Crimson"),
    ("no013", "Indigo & Vermilion"),
]


class MainWindow(QMainWindow):
    """An interactive CAD engineering workspace for QCanvas superconducting designs."""

    def __init__(self, design: Any | None = None) -> None:
        super().__init__()
        self.design = design or PlanarDesign()
        self.active_theme: str = "cyber"
        self.setWindowTitle("QCanvas Viewer")
        self.resize(1360, 880)

        # Apply dark modern engineering design system
        apply_dark_theme(self)

        # Set window icon if available
        icon_path = Path(__file__).parent / "resources" / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._selected_component: str | None = None
        self._selection_just_changed: bool = False

        # Live Script Watcher & Path tracking
        self._active_script_path: Path | None = None
        self.watcher = ScriptWatcher(self)
        self.watcher.file_modified.connect(self._on_file_watcher_modified)

        # Build Main Viewport & Floating HUD
        self._build_viewport()

        # Build Docks (Must be built before menubar so dock toggle actions are ready)
        self._build_left_dock()
        self._build_right_dock()

        # Build Menu Bar
        self._build_menubar()

        # Build Status Bar
        self._setup_statusbar()

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
        self.fit_chip()

    # ---------------------------------------------------------------- Viewport & HUD
    def _build_viewport(self) -> None:
        """Create central viewport container with floating CAD HUD toolbar."""
        central_container = QWidget(self)
        central_layout = QVBoxLayout(central_container)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        # Top Floating CAD HUD Toolbar
        self.hud_toolbar = QWidget(central_container)
        self.hud_toolbar.setStyleSheet(
            f"background-color: {Palette.BG_SURFACE}; border-bottom: 1px solid {Palette.BORDER_SUBTLE}; padding: 3px 8px;"
        )
        hud_layout = QHBoxLayout(self.hud_toolbar)
        hud_layout.setContentsMargins(4, 2, 4, 2)
        hud_layout.setSpacing(6)

        # HUD Quick Action Buttons
        self.btn_hud_palette = QPushButton("🧩 Library")
        self.btn_hud_palette.setToolTip("Focus Component Library Tool Palette")
        self.btn_hud_palette.clicked.connect(self._toggle_or_raise_palette)

        self.btn_hud_fit = QPushButton("⤢ Fit (A)")
        self.btn_hud_fit.setToolTip("Fit viewport to selected component or entire layout [A]")
        self.btn_hud_fit.clicked.connect(self.fit_all)

        self.btn_hud_chip = QPushButton("⊡ Chip (Shift+A)")
        self.btn_hud_chip.setToolTip("Fit viewport to entire substrate chip die [Shift+A]")
        self.btn_hud_chip.clicked.connect(self.fit_chip)

        self.btn_hud_ruler = QPushButton("📏 Ruler (M)")
        self.btn_hud_ruler.setCheckable(True)
        self.btn_hud_ruler.setToolTip("Toggle interactive point-to-point distance measurement [M]")
        self.btn_hud_ruler.clicked.connect(self.toggle_ruler)

        self.btn_hud_labels = QPushButton("🏷 Labels (L)")
        self.btn_hud_labels.setCheckable(True)
        self.btn_hud_labels.setToolTip("Toggle component name annotations [L]")
        self.btn_hud_labels.clicked.connect(self.toggle_labels)

        self.btn_hud_rebuild = QPushButton("⟳ Rebuild (R)")
        self.btn_hud_rebuild.setToolTip("Rebuild layout and re-render [R]")
        self.btn_hud_rebuild.clicked.connect(self.rebuild)

        self.btn_hud_delete = QPushButton("🗑 Delete (Del)")
        self.btn_hud_delete.setToolTip("Delete selected component [Del / Backspace]")
        self.btn_hud_delete.clicked.connect(self.delete_selected_component)

        hud_layout.addWidget(self.btn_hud_palette)
        hud_layout.addWidget(self.btn_hud_fit)
        hud_layout.addWidget(self.btn_hud_chip)
        hud_layout.addWidget(self.btn_hud_ruler)
        hud_layout.addWidget(self.btn_hud_labels)
        hud_layout.addWidget(self.btn_hud_rebuild)
        hud_layout.addWidget(self.btn_hud_delete)
        hud_layout.addStretch(1)

        # Quick Export Button
        btn_quick_gds = QPushButton("💾 Export GDS…")
        btn_quick_gds.setStyleSheet(
            f"background-color: {Palette.ACCENT_TEAL}; color: #FFFFFF; font-weight: bold;"
        )
        btn_quick_gds.clicked.connect(self._export_gds)
        hud_layout.addWidget(btn_quick_gds)

        central_layout.addWidget(self.hud_toolbar)

        # Matplotlib CAD Canvas
        self.canvas = MplCanvas(self, width=7.0, height=6.0, dpi=100, theme=self.active_theme)
        central_layout.addWidget(self.canvas, 1)

        self.setCentralWidget(central_container)

    # ---------------------------------------------------------------- Menu Bar
    def _build_menubar(self) -> None:
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("&File")

        act_new = QAction("&New Blank Design", self)
        act_new.setShortcut(QKeySequence("Ctrl+N"))
        act_new.triggered.connect(self.new_design)
        file_menu.addAction(act_new)

        act_open = QAction("&Open Python Script…", self)
        act_open.setShortcut(QKeySequence("Ctrl+O"))
        act_open.triggered.connect(lambda: self.open_python_script())
        file_menu.addAction(act_open)

        act_save = QAction("&Save Python Script", self)
        act_save.setShortcut(QKeySequence("Ctrl+S"))
        act_save.triggered.connect(lambda: self.save_python_script())
        file_menu.addAction(act_save)

        act_save_as = QAction("Save Python Script &As…", self)
        act_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        act_save_as.triggered.connect(lambda: self.save_python_script(save_as=True))
        file_menu.addAction(act_save_as)

        file_menu.addSeparator()

        self.act_live_reload = QAction("⚡ &Live Reload on External Edit", self)
        self.act_live_reload.setCheckable(True)
        self.act_live_reload.setChecked(True)
        self.act_live_reload.toggled.connect(self._on_live_reload_toggled)
        file_menu.addAction(self.act_live_reload)

        # Examples Submenu
        examples_menu = file_menu.addMenu("Load &Examples")
        act_ex_transmon = QAction("Dual-Pad Transmon Pair", self)
        act_ex_transmon.triggered.connect(lambda: self.load_example_design("transmons"))
        examples_menu.addAction(act_ex_transmon)

        act_ex_xmon = QAction("Xmon & Readout Claw", self)
        act_ex_xmon.triggered.connect(lambda: self.load_example_design("xmon"))
        examples_menu.addAction(act_ex_xmon)

        file_menu.addSeparator()

        # Export Submenu
        export_menu = file_menu.addMenu("&Export")
        act_export_gds = QAction("Export &GDSII…", self)
        act_export_gds.setShortcut(QKeySequence("Ctrl+G"))
        act_export_gds.triggered.connect(self._export_gds)
        export_menu.addAction(act_export_gds)

        act_export_img = QAction("Export &Image…", self)
        act_export_img.setShortcut(QKeySequence("Ctrl+Shift+I"))
        act_export_img.triggered.connect(self._export_image)
        export_menu.addAction(act_export_img)

        file_menu.addSeparator()

        act_exit = QAction("E&xit", self)
        act_exit.setShortcut(QKeySequence("Ctrl+Q"))
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        # Edit Menu
        edit_menu = menubar.addMenu("&Edit")

        act_delete = QAction("&Delete Selected Component", self)
        act_delete.setShortcut(QKeySequence("Delete"))
        act_delete.triggered.connect(self.delete_selected_component)
        edit_menu.addAction(act_delete)

        act_rebuild = QAction("&Rebuild Design", self)
        act_rebuild.setShortcut(QKeySequence("R"))
        act_rebuild.triggered.connect(self.rebuild)
        edit_menu.addAction(act_rebuild)

        act_clear_sel = QAction("&Clear Selection", self)
        act_clear_sel.setShortcut(QKeySequence("Esc"))
        act_clear_sel.triggered.connect(self.clear_selection)
        edit_menu.addAction(act_clear_sel)

        # View Menu
        view_menu = menubar.addMenu("&View")

        act_toggle_palette = self.palette_dock.toggleViewAction()
        act_toggle_palette.setText("Component &Library Dock")
        view_menu.addAction(act_toggle_palette)

        act_toggle_hierarchy = self.left_dock.toggleViewAction()
        act_toggle_hierarchy.setText("Project &Hierarchy Dock")
        view_menu.addAction(act_toggle_hierarchy)

        act_toggle_inspector = self.right_dock.toggleViewAction()
        act_toggle_inspector.setText("Property &Inspector Dock")
        view_menu.addAction(act_toggle_inspector)

        view_menu.addSeparator()

        act_fit_all = QAction("&Fit All", self)
        act_fit_all.setShortcut(QKeySequence("A"))
        act_fit_all.triggered.connect(self.fit_all)
        view_menu.addAction(act_fit_all)

        act_fit_chip = QAction("Fit &Chip Die", self)
        act_fit_chip.setShortcut(QKeySequence("Shift+A"))
        act_fit_chip.triggered.connect(self.fit_chip)
        view_menu.addAction(act_fit_chip)

        view_menu.addSeparator()

        act_labels = QAction("Toggle &Labels", self)
        act_labels.setShortcut(QKeySequence("L"))
        act_labels.triggered.connect(self.toggle_labels)
        view_menu.addAction(act_labels)

        act_ruler = QAction("Measure &Ruler Tool", self)
        act_ruler.setShortcut(QKeySequence("M"))
        act_ruler.triggered.connect(self.toggle_ruler)
        view_menu.addAction(act_ruler)

        view_menu.addSeparator()

        # Theme Presets Submenu
        theme_menu = view_menu.addMenu("🎨 &Theme Preset")
        self.theme_action_group = QActionGroup(self)

        self.theme_actions: dict[str, QAction] = {}
        for key, name in THEMES_CATALOG:
            act = QAction(name, self)
            act.setCheckable(True)
            if key == self.active_theme:
                act.setChecked(True)
            act.triggered.connect(lambda _, k=key: self.set_theme_preset(k))
            self.theme_action_group.addAction(act)
            theme_menu.addAction(act)
            self.theme_actions[key] = act

        view_menu.addSeparator()

        act_toggle_scale = QAction("Show &Scale Bar", self)
        act_toggle_scale.setCheckable(True)
        act_toggle_scale.setChecked(True)
        act_toggle_scale.toggled.connect(lambda v: self.show_scale_bar.setChecked(v))
        view_menu.addAction(act_toggle_scale)

        act_toggle_crosshair = QAction("Show CAD &Crosshair", self)
        act_toggle_crosshair.setCheckable(True)
        act_toggle_crosshair.setChecked(True)
        act_toggle_crosshair.toggled.connect(self._on_crosshair_toggled)
        view_menu.addAction(act_toggle_crosshair)

        # Tools Menu
        tools_menu = menubar.addMenu("&Tools")
        act_tool_ruler = QAction("Distance &Ruler", self)
        act_tool_ruler.triggered.connect(self.toggle_ruler)
        tools_menu.addAction(act_tool_ruler)

        # Help Menu
        help_menu = menubar.addMenu("&Help")
        act_about = QAction("&About QCanvas", self)
        act_about.triggered.connect(self._show_about_dialog)
        help_menu.addAction(act_about)

    # ---------------------------------------------------------------- Left Docks
    def _build_left_dock(self) -> None:
        # 1. Component Library Palette Dock
        self.palette_dock = QDockWidget("Component Library", self)
        self.palette_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        self.palette = ComponentPaletteWidget(self)
        self.palette.component_selected.connect(self._on_palette_component_selected)
        self.palette.placement_cancelled.connect(self._on_placement_cancelled)
        self.palette.grid_snap_changed.connect(self._on_grid_snap_changed)
        self.palette_dock.setWidget(self.palette)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.palette_dock)

        # 2. Project Hierarchy Dock
        self.left_dock = QDockWidget("Project Hierarchy", self)
        self.left_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
        )

        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header Title
        lbl_comp_header = QLabel("Components")
        lbl_comp_header.setStyleSheet(
            f"font-weight: bold; color: {Palette.ACCENT_CYAN}; font-size: 11px; text-transform: uppercase;"
        )
        layout.addWidget(lbl_comp_header)

        # Search / Filter LineEdit
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search components...")
        self.search_input.textChanged.connect(self._filter_components)
        layout.addWidget(self.search_input)

        # Component Table / List
        self.component_table = QTableWidget(0, 2)
        self.component_table.setHorizontalHeaderLabels(["Name", "Type"])
        self.component_table.horizontalHeader().setStretchLastSection(True)
        self.component_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.component_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.component_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.component_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.component_table.verticalHeader().setVisible(False)
        self.component_table.setShowGrid(False)
        self.component_table.itemSelectionChanged.connect(self._on_component_table_selection_changed)
        self.component_table.itemClicked.connect(self._on_component_table_item_clicked)
        self.component_table.itemDoubleClicked.connect(self._on_component_table_double_clicked)
        self.component_list = self.component_table  # Backwards compatibility
        layout.addWidget(self.component_table, 1)

        # Layer & View Visibility Section
        lbl_layers_header = QLabel("Layers & Theme")
        lbl_layers_header.setStyleSheet(
            f"font-weight: bold; color: {Palette.ACCENT_CYAN}; font-size: 11px; text-transform: uppercase; margin-top: 4px;"
        )
        layout.addWidget(lbl_layers_header)

        # Theme Selector Dropdown
        theme_box = QHBoxLayout()
        lbl_theme = QLabel("Theme:")
        lbl_theme.setStyleSheet(f"color: {Palette.TEXT_SECONDARY};")
        self.theme_combo = QComboBox()
        for key, name in THEMES_CATALOG:
            self.theme_combo.addItem(name, key)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_combo_changed)
        theme_box.addWidget(lbl_theme)
        theme_box.addWidget(self.theme_combo, 1)
        layout.addLayout(theme_box)

        # Layer Filter
        layer_filter_box = QHBoxLayout()
        lbl_layer = QLabel("Layer Filter:")
        lbl_layer.setStyleSheet(f"color: {Palette.TEXT_SECONDARY};")
        self.layer_filter = QComboBox()
        self.layer_filter.currentIndexChanged.connect(lambda _: self._draw(preserve_view=True))
        layer_filter_box.addWidget(lbl_layer)
        layer_filter_box.addWidget(self.layer_filter, 1)
        layout.addLayout(layer_filter_box)

        # Checkbox Toggles
        toggles_box = QHBoxLayout()
        self.chip_outline = QCheckBox("Chip Outline")
        self.chip_outline.setChecked(True)
        self.chip_outline.toggled.connect(lambda _: self._draw(preserve_view=True))

        self.show_grid = QCheckBox("Grid")
        self.show_grid.setChecked(True)
        self.show_grid.toggled.connect(lambda _: self._draw(preserve_view=True))

        self.show_scale_bar = QCheckBox("Scale Bar")
        self.show_scale_bar.setChecked(True)
        self.show_scale_bar.toggled.connect(self._on_scale_bar_toggled)

        toggles_box.addWidget(self.chip_outline)
        toggles_box.addWidget(self.show_grid)
        toggles_box.addWidget(self.show_scale_bar)
        layout.addLayout(toggles_box)

        self.left_dock.setWidget(panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.left_dock)

        # Tabify Palette and Hierarchy docks on the left
        self.tabifyDockWidget(self.palette_dock, self.left_dock)
        self.palette_dock.raise_()

    def _on_theme_combo_changed(self, index: int) -> None:
        """Handle theme dropdown selection."""
        theme_key = self.theme_combo.currentData()
        if theme_key and theme_key != self.active_theme:
            self.set_theme_preset(theme_key)

    def set_theme_preset(self, theme_key: str) -> None:
        """Switch active theme preset, update UI controls, and re-render."""
        theme_cfg = get_theme(theme_key)
        self.active_theme = theme_cfg.key

        # Sync dropdown without triggering redundant event
        self.theme_combo.blockSignals(True)
        for i in range(self.theme_combo.count()):
            if self.theme_combo.itemData(i) == self.active_theme:
                self.theme_combo.setCurrentIndex(i)
                break
        self.theme_combo.blockSignals(False)

        # Sync menu bar action
        if self.active_theme in self.theme_actions:
            self.theme_actions[self.active_theme].setChecked(True)

        self.canvas.set_theme(self.active_theme)
        self._draw(preserve_view=True)
        self.status_dot.setText(f"🎨 {theme_cfg.name.split()[0]}")

    def _on_scale_bar_toggled(self, checked: bool) -> None:
        """Toggle physical scale bar overlay."""
        self.canvas.set_scale_bar_visible(checked)

    def _on_crosshair_toggled(self, checked: bool) -> None:
        """Toggle CAD crosshair cursor overlay."""
        self.canvas.crosshair_visible = checked
        if not checked:
            self.canvas._crosshair_h.set_visible(False)
            self.canvas._crosshair_v.set_visible(False)
            self.canvas.draw_idle()

    # ---------------------------------------------------------------- Right Dock
    def _build_right_dock(self) -> None:
        self.right_dock = QDockWidget("Property Inspector", self)
        self.right_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)

        self.inspector = PropertyInspector(self)
        self.inspector.component_changed.connect(self._on_component_property_changed)

        self.right_dock.setWidget(self.inspector)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.right_dock)

    # ---------------------------------------------------------------- Status Bar
    def _setup_statusbar(self) -> None:
        status_bar = QStatusBar(self)
        self.setStatusBar(status_bar)

        # Status Indicator Pill
        self.status_dot = QLabel("🟢 Ready")
        self.status_dot.setStyleSheet(
            f"background-color: {Palette.BG_CARD}; color: {Palette.TEXT_PRIMARY}; border-radius: 4px; padding: 2px 8px; font-weight: bold; font-size: 11px;"
        )

        # Coordinates Pill Badge
        self.coord_label = QLabel(" X: --  Y: -- ")
        self.coord_label.setStyleSheet(
            f"font-family: 'Consolas', 'Fira Code', monospace; font-weight: bold; background-color: {Palette.BG_CARD}; color: {Palette.ACCENT_CYAN}; border: 1px solid {Palette.BORDER_DEFAULT}; border-radius: 4px; padding: 2px 10px; margin: 0 4px;"
        )

        # Hint & Info Label
        self.hint_label = QLabel(
            " [Scroll] Zoom  ·  [Left Drag] Pan  ·  [Right Drag] Box Zoom  ·  [A] Fit  ·  [M] Ruler  ·  [R] Rebuild "
        )
        self.hint_label.setStyleSheet(f"color: {Palette.TEXT_MUTED}; padding: 2px 6px;")

        status_bar.addWidget(self.status_dot)
        status_bar.addWidget(self.coord_label)
        status_bar.addWidget(self.hint_label, 1)

    def _on_hover_coord(self, x: float | None, y: float | None) -> None:
        """Update status bar coordinate display."""
        if x is None or y is None:
            self.coord_label.setText(" X: --  Y: -- ")
        else:
            unit = getattr(self.design, "units", "um")
            self.coord_label.setText(f" X: {x:+.2f} {unit}   Y: {y:+.2f} {unit} ")

    # ---------------------------------------------------------------- Component Library & Placement
    def _toggle_or_raise_palette(self) -> None:
        """Show and focus the Component Library Palette dock."""
        if self.palette_dock.isHidden():
            self.palette_dock.show()
        self.palette_dock.raise_()

    def _on_palette_component_selected(self, meta: ComponentMeta) -> None:
        """Slot when user selects a component in the palette to place on canvas."""
        if self.canvas.ruler.active:
            self.toggle_ruler()
        snap_val = self.palette.get_current_grid_snap()
        self.canvas.placement.set_grid_snap(snap_val)
        self.canvas.placement.arm(meta)
        self.status_dot.setText(f"➕ Placing {meta.cls.__name__}")
        self.hint_label.setText(
            f"Placement Mode: [{meta.icon} {meta.display_name}] · Move cursor to position, [R] Rotate 90°, [Click] Place, [Esc] Cancel"
        )

    def _on_placement_cancelled(self) -> None:
        """Cancel active component placement mode."""
        self.canvas.placement.disarm()
        self.palette.set_active_component(None)
        self.status_dot.setText("🟢 Ready")
        self.hint_label.setText(
            " [Scroll] Zoom  ·  [Left Drag] Pan  ·  [Right Drag] Box Zoom  ·  [A] Fit  ·  [M] Ruler  ·  [R] Rebuild "
        )

    def _on_grid_snap_changed(self, snap_val: float) -> None:
        """Slot when grid snap setting is modified in palette."""
        self.canvas.placement.set_grid_snap(snap_val)
        unit = getattr(self.design, "units", "um")
        snap_str = f"{snap_val:.0f} {unit}" if snap_val > 0 else "Off"
        self.status_dot.setText(f"🧲 Snap: {snap_str}")

    # ---------------------------------------------------------------- Pick & Selection
    def _on_canvas_click_point(self, x: float, y: float) -> None:
        """Handle canvas click: if in placement mode, instantiate component; otherwise select."""
        if self.canvas.placement.is_active:
            new_comp = self.canvas.placement.handle_click(self.design, x, y)
            self.canvas.placement.disarm()
            self.palette.set_active_component(None)
            self.refresh(preserve_view=True)
            if new_comp:
                self.select_component(new_comp.name)
                self.status_dot.setText(f"✨ Placed {new_comp.name}")
                self.hint_label.setText(
                    f"Placed '{new_comp.name}' at ({x:+.1f}, {y:+.1f}) µm. Configure properties in Inspector on right."
                )
            return

        hit_name = self._find_component_at(x, y)
        if hit_name:
            if self._selected_component == hit_name:
                self.clear_selection()
            else:
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
                except Exception:  # noqa: BLE001
                    pass

        # 2. Proximity search (within click tolerance)
        min_dist = float("inf")
        closest_comp = None
        for r in records:
            if r.geometry and not r.geometry.is_empty:
                try:
                    dist = r.geometry.distance(pt)
                    if dist < min_dist:
                        min_dist = dist
                        closest_comp = r.component
                except Exception:  # noqa: BLE001
                    pass

        if min_dist <= 30.0:
            return closest_comp
        return None

    def select_component(self, name: str) -> None:
        """Select component by name, sync table selection, highlight on canvas, and inspect."""
        self._selected_component = name

        # Synchronize table selection without triggering recursive signals
        self.component_table.blockSignals(True)
        for row in range(self.component_table.rowCount()):
            item = self.component_table.item(row, 0)
            if item and item.text() == name:
                self.component_table.selectRow(row)
                break
        self.component_table.blockSignals(False)

        bounds = self._get_component_bounds(name)
        self.canvas.highlight_component(name, bounds)

        # Update Inspector
        comp = self.design.components.get(name) if hasattr(self.design, "components") else None
        self.inspector.set_component(comp)

        unit = getattr(self.design, "units", "um")
        if bounds:
            w = bounds[2] - bounds[0]
            h = bounds[3] - bounds[1]
            self.hint_label.setText(
                f"Selected: {name} ({w:.1f} × {h:.1f} {unit})  ·  [A] Frame  ·  [Esc] Clear"
            )

    def clear_selection(self) -> None:
        """Deselect all components and clear canvas highlight and inspector."""
        self._selected_component = None
        self.component_table.blockSignals(True)
        self.component_table.clearSelection()
        self.component_table.blockSignals(False)
        self.canvas.clear_highlight()
        self.inspector.set_component(None)
        self.hint_label.setText(
            " [Scroll] Zoom  ·  [Left Drag] Pan  ·  [Right Drag] Box Zoom  ·  [A] Fit  ·  [M] Ruler  ·  [R] Rebuild "
        )

    def _on_component_table_selection_changed(self) -> None:
        selected_rows = self.component_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            item = self.component_table.item(row, 0)
            if item:
                self.select_component(item.text())
                self._selection_just_changed = True
        else:
            self.clear_selection()
            self._selection_just_changed = True

    def _on_component_table_item_clicked(self, item) -> None:
        if self._selection_just_changed:
            self._selection_just_changed = False
        else:
            # Clicked on already selected item -> deselect
            self.clear_selection()

    def _on_component_table_double_clicked(self, item) -> None:
        row = item.row()
        name_item = self.component_table.item(row, 0)
        if name_item:
            name = name_item.text()
            bounds = self._get_component_bounds(name)
            if bounds:
                self.canvas.zoom_to_rect(bounds)

    def _filter_components(self, query: str) -> None:
        """Filter component list based on search text."""
        query = query.strip().lower()
        for row in range(self.component_table.rowCount()):
            item_name = self.component_table.item(row, 0)
            item_type = self.component_table.item(row, 1)
            name_text = item_name.text().lower() if item_name else ""
            type_text = item_type.text().lower() if item_type else ""
            match = query in name_text or query in type_text
            self.component_table.setRowHidden(row, not match)

    def _on_component_property_changed(self, name: str) -> None:
        """Callback when properties of a component are updated in Inspector."""
        self.refresh(preserve_view=True)
        self.status_dot.setText("🟢 Updated")

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
        self.status_dot.setText("⚙ Rebuilding...")
        self.design.rebuild()
        self.refresh(preserve_view=True)
        self.status_dot.setText("🟢 Ready")

    def toggle_labels(self) -> None:
        """Toggle component name labels on canvas."""
        bounds_map = self._get_all_component_bounds()
        is_visible = self.canvas.toggle_all_labels(bounds_map)
        self.btn_hud_labels.setChecked(is_visible)
        status = "shown" if is_visible else "hidden"
        self.hint_label.setText(f"Labels {status} ([L] toggle)")

    def toggle_ruler(self) -> None:
        """Toggle interactive CAD distance ruler tool."""
        active = self.canvas.ruler.toggle()
        self.btn_hud_ruler.setChecked(active)
        if active:
            self.status_dot.setText("📏 Measuring")
            self.hint_label.setText("Ruler Active: Click first point to start measurement  ·  [M] or [Esc] to exit")
        else:
            self.status_dot.setText("🟢 Ready")
            self.hint_label.setText(" [Scroll] Zoom  ·  [Left Drag] Pan  ·  [Right Drag] Box Zoom  ·  [A] Fit  ·  [M] Ruler ")

    def _on_canvas_shortcut(self, key: str) -> None:
        """Dispatch shortcuts from Canvas."""
        if key.startswith("ruler_status:"):
            status_msg = key.split("ruler_status:", 1)[1]
            self.hint_label.setText(status_msg)
            return

        k = key.lower()
        if key == "A":  # Shift + a
            self.fit_chip()
        elif k == "a":
            self.fit_all()
        elif k == "r":
            if self.canvas.placement.is_active:
                new_rot = self.canvas.placement.rotate_cw()
                self.hint_label.setText(
                    f"Placement Rotation: {new_rot:.0f}°  ·  [R] Rotate  ·  [Click] Place  ·  [Esc] Cancel"
                )
            else:
                self.rebuild()
        elif k == "l":
            self.toggle_labels()
        elif k == "m":
            self.toggle_ruler()
        elif key in ("escape", "Escape", "esc"):
            if self.canvas.placement.is_active:
                self._on_placement_cancelled()
            elif self.canvas.ruler.active:
                self.toggle_ruler()
            else:
                self.clear_selection()
        elif key in ("delete", "Delete", "backspace", "Backspace"):
            self.delete_selected_component()

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
            if self.canvas.placement.is_active:
                new_rot = self.canvas.placement.rotate_cw()
                self.hint_label.setText(
                    f"Placement Rotation: {new_rot:.0f}°  ·  [R] Rotate  ·  [Click] Place  ·  [Esc] Cancel"
                )
            else:
                self.rebuild()
            event.accept()
        elif key == Qt.Key.Key_L:
            self.toggle_labels()
            event.accept()
        elif key == Qt.Key.Key_M:
            self.toggle_ruler()
            event.accept()
        elif key == Qt.Key.Key_Escape:
            if self.canvas.placement.is_active:
                self._on_placement_cancelled()
            elif self.canvas.ruler.active:
                self.toggle_ruler()
            else:
                self.clear_selection()
            event.accept()
        elif key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.delete_selected_component()
            event.accept()
        else:
            super().keyPressEvent(event)

    def delete_selected_component(self) -> None:
        """Delete the currently selected component from the design."""
        if not self._selected_component:
            self.hint_label.setText("No component selected to delete.")
            return
        name = self._selected_component
        reply = QMessageBox.question(
            self,
            "Delete Component",
            f"Are you sure you want to delete component '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if hasattr(self.design, "remove_component"):
                try:
                    self.design.remove_component(name)
                except Exception as e:
                    QMessageBox.warning(self, "Delete Failed", f"Could not delete component: {e}")
                    return
            self.clear_selection()
            self.refresh(preserve_view=True)
            self.status_dot.setText("🗑️ Deleted")
            self.hint_label.setText(f"Removed component: '{name}'")

    def new_design(self) -> None:
        """Reset workspace to a blank planar design."""
        self.watcher.unwatch()
        self._active_script_path = None
        self._update_window_title()

        if hasattr(self.design, "remove_listener"):
            self.design.remove_listener(self._on_design_changed)
        self.design = PlanarDesign()
        self.design.add_listener(self._on_design_changed)
        self.clear_selection()
        self.refresh(preserve_view=False)
        self.fit_chip()
        self.status_dot.setText("📄 New Blank Design")
        self.hint_label.setText("Blank canvas ready. Select a component from the library on the left to begin.")

    def load_example_design(self, example_type: str = "transmons") -> None:
        """Load pre-built quantum layout example circuits."""
        self.watcher.unwatch()
        self._active_script_path = None
        self._update_window_title()

        if hasattr(self.design, "remove_listener"):
            self.design.remove_listener(self._on_design_changed)

        if example_type == "xmon":
            self.design = _xmon_example_design()
        else:
            self.design = _demo_design()

        self.design.add_listener(self._on_design_changed)
        self.clear_selection()
        self.refresh(preserve_view=False)
        self.fit_all()
        self.status_dot.setText("📦 Example Loaded")
        self.hint_label.setText(f"Loaded example layout: {example_type}")

    # ---------------------------------------------------------------- Python Script I/O & Live Reload
    def _update_window_title(self) -> None:
        """Update window title bar to show active script filename."""
        if self._active_script_path is not None:
            self.setWindowTitle(f"QCanvas Viewer — [{self._active_script_path.name}]")
        else:
            self.setWindowTitle("QCanvas Viewer")

    def _on_live_reload_toggled(self, enabled: bool) -> None:
        """Toggle active script live filesystem watcher."""
        self.watcher.set_enabled(enabled)
        if enabled and self._active_script_path:
            self.watcher.watch(self._active_script_path)
            self.status_dot.setText("⚡ Live Watch ON")
            self.hint_label.setText(f"Live reload active for: {self._active_script_path.name}")
        else:
            self.status_dot.setText("⏸ Live Watch OFF")
            self.hint_label.setText("Live reload paused.")

    def open_python_script(self, filepath: str | Path | None = None) -> None:
        """Open and execute a Python script to load its QCanvas Design."""
        if not filepath:
            filepath, _ = QFileDialog.getOpenFileName(
                self,
                "Open QCanvas Python Script",
                "",
                "Python Files (*.py);;All Files (*)",
            )
        if not filepath:
            return

        path = Path(filepath).resolve()
        try:
            new_design = load_design_from_script(path)
        except ScriptLoadError as err:
            self._show_script_error_dialog(err, is_hot_reload=False)
            return
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Open Script Failed", f"An unexpected error occurred while loading script:\n{e}")
            return

        if hasattr(self.design, "remove_listener"):
            self.design.remove_listener(self._on_design_changed)

        self._active_script_path = path
        self.design = new_design
        self.design.add_listener(self._on_design_changed)
        self.clear_selection()
        self.refresh(preserve_view=False)
        self.fit_chip()
        self._update_window_title()

        if self.act_live_reload.isChecked():
            self.watcher.watch(self._active_script_path)

        self.status_dot.setText(f"📂 {self._active_script_path.name}")
        self.hint_label.setText(f"Opened script: {self._active_script_path}  ·  ⚡ Live Watch Active")

    def save_python_script(self, filepath: str | Path | None = None, save_as: bool = False) -> None:
        """Export current design as a Python script and attach live reload watcher."""
        if save_as or self._active_script_path is None or filepath is not None:
            default_name = str(self._active_script_path) if self._active_script_path else "circuit_design.py"
            path_str = str(filepath) if filepath else None
            if not path_str:
                path_str, _ = QFileDialog.getSaveFileName(
                    self,
                    "Save QCanvas Python Script",
                    default_name,
                    "Python Files (*.py);;All Files (*)",
                )
            if not path_str:
                return
            self._active_script_path = Path(path_str).resolve()

        try:
            export_python_script(self.design, self._active_script_path)
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Save Script Failed", f"Could not save Python script:\n{e}")
            return

        self._update_window_title()
        if self.act_live_reload.isChecked():
            self.watcher.watch(self._active_script_path)

        self.status_dot.setText(f"💾 {self._active_script_path.name}")
        self.hint_label.setText(f"Saved design script to: {self._active_script_path}")

    def _on_file_watcher_modified(self, path: Path) -> None:
        """Slot triggered when active script is saved/modified externally."""
        if not self.act_live_reload.isChecked() or path != self._active_script_path:
            return

        try:
            reloaded_design = load_design_from_script(path)
        except ScriptLoadError as err:
            self.status_dot.setText("❌ Reload Error")
            self.hint_label.setText(f"Error on Line {err.line_number or '?'}: {err.message}")
            self._show_script_error_dialog(err, is_hot_reload=True)
            return
        except Exception as e:  # noqa: BLE001
            self.status_dot.setText("❌ Reload Error")
            self.hint_label.setText(f"Reload failed: {e}")
            return

        if hasattr(self.design, "remove_listener"):
            self.design.remove_listener(self._on_design_changed)

        self.design = reloaded_design
        self.design.add_listener(self._on_design_changed)

        # Preserve current view limits & highlight
        self.refresh(preserve_view=True)

        import datetime
        t_str = datetime.datetime.now().strftime("%H:%M:%S")
        self.status_dot.setText(f"⚡ Reloaded ({t_str})")
        self.hint_label.setText(f"Live updated from {path.name} at {t_str}")

    def _show_script_error_dialog(self, err: ScriptLoadError, is_hot_reload: bool = False) -> None:
        """Display structured diagnostic dialog when script execution fails."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Warning if is_hot_reload else QMessageBox.Icon.Critical)
        title = "Live Hot Reload Error" if is_hot_reload else "Failed to Load Script"
        msg_box.setWindowTitle(title)
        msg_box.setText(f"<h3>{err.error_type}: {err.message}</h3>")

        info_text = f"<b>File:</b> {err.filepath.name}<br>"
        if err.line_number is not None:
            info_text += f"<b>Line Number:</b> {err.line_number}<br>"
        if err.code_snippet:
            info_text += f"<br><b>Code Context:</b><pre style='background:#1E2330; padding:6px; color:#FF6B81;'>{err.code_snippet}</pre>"

        msg_box.setInformativeText(info_text)
        if err.traceback_str:
            msg_box.setDetailedText(err.traceback_str)

        msg_box.exec()

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
        """Render design onto canvas axes with active theme."""
        cur_xlim = None
        cur_ylim = None
        if preserve_view:
            try:
                cur_xlim = self.canvas.axes.get_xlim()
                cur_ylim = self.canvas.axes.get_ylim()
            except Exception:  # noqa: BLE001
                pass

        layer_text = self.layer_filter.currentText()
        layers = [int(layer_text)] if layer_text and layer_text != "All" else None

        export_scene(
            self.design,
            ax=self.canvas.axes,
            layers=layers,
            chip_outline=self.chip_outline.isChecked(),
            grid=self.show_grid.isChecked(),
            theme=self.active_theme,
            title=None,  # Clean frameless title
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
        path, _ = QFileDialog.getSaveFileName(self, "Export GDSII Layout", "qcanvas.gds", "GDS files (*.gds)")
        if path:
            self.design.export("gds", filepath=path)
            self.status_dot.setText("💾 GDS Exported")
            self.hint_label.setText(f"Exported GDSII to: {path}")

    def _export_image(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Image",
            f"qcanvas_layout_{self.active_theme}.png",
            "PNG (*.png);;SVG (*.svg);;PDF (*.pdf)",
        )
        if path:
            self.canvas.figure.savefig(path, dpi=300, facecolor=self.canvas.figure.get_facecolor(), bbox_inches="tight")
            self.status_dot.setText("📷 Image Saved")
            self.hint_label.setText(f"Saved layout image ({self.active_theme}) to: {path}")

    def _show_about_dialog(self) -> None:
        QMessageBox.about(
            self,
            "About QCanvas",
            "<h3>QCanvas CAD Studio</h3>"
            "<p>A modern, high-precision layout framework for superconducting quantum circuits.</p>"
            "<p><b>Version:</b> 0.1.0</p>",
        )

    def closeEvent(self, event) -> None:
        """Prompt confirmation dialog before closing the application."""
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        is_offscreen = app is not None and getattr(app, "platformName", lambda: "")() == "offscreen"

        if not is_offscreen and getattr(self, "_confirm_on_close", True):
            reply = QMessageBox.question(
                self,
                "Exit QCanvas Studio",
                "Are you sure you want to exit QCanvas CAD Studio?\n\nAny unsaved layout changes will be lost.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return

        self.watcher.unwatch()
        if hasattr(self.design, "remove_listener"):
            self.design.remove_listener(self._on_design_changed)
        self.canvas.interaction.disconnect()
        super().closeEvent(event)


def _demo_design():
    """Build a demo design with a pair of DualPadTransmon qubits."""
    from qcanvas.components import DualPadTransmon
    from qcanvas.designs import PlanarDesign

    design = PlanarDesign()
    DualPadTransmon(design, "Q1", options={"pos_x": "-2000um", "pos_y": "0.0um"})
    DualPadTransmon(design, "Q2", options={"pos_x": "2000um", "pos_y": "500um"})
    return design


def _xmon_example_design():
    """Build an example design featuring CrossTransmon (Xmon), ChargeClaw, and Launchpad."""
    from qcanvas.components import ChargeClaw, CrossTransmon, Launchpad
    from qcanvas.designs import PlanarDesign

    design = PlanarDesign()
    CrossTransmon(design, "Q1", options={"pos_x": "-1200um", "pos_y": "0.0um"})
    ChargeClaw(design, "claw_1", options={"pos_x": "-1200um", "pos_y": "600um", "orientation": "0"})
    Launchpad(design, "port_in", options={"pos_x": "-3200um", "pos_y": "1200um", "orientation": "0"})
    return design


__all__ = ["MainWindow"]
