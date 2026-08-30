"""Theme and design system definitions for QCanvas GUI.

Provides a unified, high-contrast dark EDA palette, typography, and Qt StyleSheets (QSS).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication, QWidget


# -----------------------------------------------------------------------------
# Color Palette Constants
# -----------------------------------------------------------------------------
class Palette:
    # Canvas & Viewport
    CANVAS_BG = "#12151C"
    CANVAS_GRID = "#1E2330"
    CANVAS_AXIS = "#2A3142"

    # Surfaces & Windows
    BG_DARKEST = "#0E1017"
    BG_MAIN = "#161922"
    BG_SURFACE = "#1D212D"
    BG_CARD = "#242A38"
    BG_HOVER = "#2D3446"
    BG_ACTIVE = "#384157"

    # Borders & Dividers
    BORDER_SUBTLE = "#262C3C"
    BORDER_DEFAULT = "#323B50"
    BORDER_FOCUS = "#00D2D3"

    # Text & Typography
    TEXT_PRIMARY = "#F1F5F9"
    TEXT_SECONDARY = "#94A3B8"
    TEXT_MUTED = "#64748B"
    TEXT_DISABLED = "#475569"

    # Brand & Quantum Accents
    ACCENT_CYAN = "#00D2D3"
    ACCENT_TEAL = "#00ADB5"
    ACCENT_BLUE = "#0984E3"
    ACCENT_PURPLE = "#6C5CE7"
    ACCENT_RUBY = "#FF4757"
    ACCENT_AMBER = "#FFA502"
    ACCENT_GREEN = "#2ED573"

    # Quantum Component Colors
    CHIP_SUBSTRATE = "#12151C"
    METAL_BASE = "#00ADB5"
    JUNCTION_RUBY = "#FF4757"
    CUTOUT_VOID = "#12151C"
    GROUND_PLANE = "#2A354D"
    SELECTION_BOX = "#00D2D3"
    CROSSHAIR = "#00D2D3"


# -----------------------------------------------------------------------------
# Master Qt Style Sheet (QSS)
# -----------------------------------------------------------------------------
DARK_THEME_QSS = f"""
/* Global Reset & Base Fonts */
QWidget {{
    background-color: {Palette.BG_MAIN};
    color: {Palette.TEXT_PRIMARY};
    font-family: "Segoe UI", "Inter", "PingFang SC", "Microsoft YaHei", -apple-system, sans-serif;
    font-size: 12px;
    selection-background-color: {Palette.ACCENT_TEAL};
    selection-color: #FFFFFF;
}}

/* Main Window */
QMainWindow {{
    background-color: {Palette.BG_MAIN};
}}

QMainWindow::separator {{
    background: {Palette.BORDER_SUBTLE};
    width: 2px;
    height: 2px;
}}

/* Menu Bar & Menus */
QMenuBar {{
    background-color: {Palette.BG_MAIN};
    color: {Palette.TEXT_PRIMARY};
    border-bottom: 1px solid {Palette.BORDER_SUBTLE};
    padding: 2px 6px;
}}

QMenuBar::item {{
    background: transparent;
    padding: 4px 10px;
    border-radius: 4px;
}}

QMenuBar::item:selected {{
    background-color: {Palette.BG_HOVER};
    color: {Palette.ACCENT_CYAN};
}}

QMenu {{
    background-color: {Palette.BG_SURFACE};
    color: {Palette.TEXT_PRIMARY};
    border: 1px solid {Palette.BORDER_DEFAULT};
    border-radius: 6px;
    padding: 4px;
}}

QMenu::item {{
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {Palette.BG_ACTIVE};
    color: {Palette.ACCENT_CYAN};
}}

QMenu::separator {{
    height: 1px;
    background: {Palette.BORDER_SUBTLE};
    margin: 4px 6px;
}}

/* Dock Widgets */
QDockWidget {{
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
    border: 1px solid {Palette.BORDER_SUBTLE};
    font-weight: bold;
    color: {Palette.TEXT_SECONDARY};
}}

QDockWidget::title {{
    background-color: {Palette.BG_SURFACE};
    padding: 6px 10px;
    border-bottom: 1px solid {Palette.BORDER_SUBTLE};
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

/* Push Buttons & Tool Buttons */
QPushButton {{
    background-color: {Palette.BG_CARD};
    color: {Palette.TEXT_PRIMARY};
    border: 1px solid {Palette.BORDER_DEFAULT};
    border-radius: 4px;
    padding: 5px 12px;
    font-weight: 500;
    min-height: 18px;
}}

QPushButton:hover {{
    background-color: {Palette.BG_HOVER};
    border-color: {Palette.ACCENT_TEAL};
    color: #FFFFFF;
}}

QPushButton:pressed {{
    background-color: {Palette.BG_ACTIVE};
    border-color: {Palette.ACCENT_CYAN};
}}

QPushButton:disabled {{
    background-color: {Palette.BG_SURFACE};
    color: {Palette.TEXT_DISABLED};
    border-color: {Palette.BORDER_SUBTLE};
}}

QPushButton#primaryButton {{
    background-color: {Palette.ACCENT_TEAL};
    color: #FFFFFF;
    border: 1px solid {Palette.ACCENT_CYAN};
    font-weight: bold;
}}

QPushButton#primaryButton:hover {{
    background-color: {Palette.ACCENT_CYAN};
    color: #0E1017;
}}

QToolButton {{
    background-color: {Palette.BG_CARD};
    color: {Palette.TEXT_PRIMARY};
    border: 1px solid {Palette.BORDER_SUBTLE};
    border-radius: 4px;
    padding: 4px 8px;
}}

QToolButton:hover {{
    background-color: {Palette.BG_HOVER};
    border-color: {Palette.ACCENT_TEAL};
    color: #FFFFFF;
}}

QToolButton:checked {{
    background-color: {Palette.BG_ACTIVE};
    border-color: {Palette.ACCENT_CYAN};
    color: {Palette.ACCENT_CYAN};
}}

/* Line Edits & Spin Boxes */
QLineEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {Palette.BG_SURFACE};
    color: {Palette.TEXT_PRIMARY};
    border: 1px solid {Palette.BORDER_DEFAULT};
    border-radius: 4px;
    padding: 4px 8px;
    selection-background-color: {Palette.ACCENT_TEAL};
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {Palette.ACCENT_CYAN};
    background-color: {Palette.BG_CARD};
}}

/* Combo Box */
QComboBox {{
    background-color: {Palette.BG_CARD};
    color: {Palette.TEXT_PRIMARY};
    border: 1px solid {Palette.BORDER_DEFAULT};
    border-radius: 4px;
    padding: 4px 10px;
    min-height: 20px;
}}

QComboBox:hover {{
    border-color: {Palette.ACCENT_TEAL};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox QAbstractItemView {{
    background-color: {Palette.BG_SURFACE};
    border: 1px solid {Palette.BORDER_DEFAULT};
    selection-background-color: {Palette.BG_ACTIVE};
    selection-color: {Palette.ACCENT_CYAN};
    border-radius: 4px;
    padding: 2px;
}}

/* Check Box */
QCheckBox {{
    color: {Palette.TEXT_PRIMARY};
    spacing: 6px;
}}

QCheckBox::indicator {{
    width: 15px;
    height: 15px;
    border-radius: 3px;
    border: 1px solid {Palette.BORDER_DEFAULT};
    background-color: {Palette.BG_SURFACE};
}}

QCheckBox::indicator:hover {{
    border-color: {Palette.ACCENT_TEAL};
}}

QCheckBox::indicator:checked {{
    background-color: {Palette.ACCENT_TEAL};
    border-color: {Palette.ACCENT_CYAN};
}}

/* Tree & Table Views */
QTreeWidget, QTableWidget, QListView {{
    background-color: {Palette.BG_SURFACE};
    color: {Palette.TEXT_PRIMARY};
    border: 1px solid {Palette.BORDER_SUBTLE};
    border-radius: 4px;
    outline: none;
    gridline-color: {Palette.BORDER_SUBTLE};
}}

QTreeWidget::item, QTableWidget::item {{
    padding: 4px 6px;
    border-radius: 2px;
}}

QTreeWidget::item:hover, QTableWidget::item:hover {{
    background-color: {Palette.BG_HOVER};
}}

QTreeWidget::item:selected, QTableWidget::item:selected {{
    background-color: {Palette.BG_ACTIVE};
    color: {Palette.ACCENT_CYAN};
}}

QHeaderView::section {{
    background-color: {Palette.BG_MAIN};
    color: {Palette.TEXT_SECONDARY};
    padding: 4px 8px;
    border: none;
    border-bottom: 1px solid {Palette.BORDER_SUBTLE};
    border-right: 1px solid {Palette.BORDER_SUBTLE};
    font-weight: 600;
    font-size: 11px;
}}

/* Tab Widget */
QTabWidget::pane {{
    border: 1px solid {Palette.BORDER_SUBTLE};
    background-color: {Palette.BG_SURFACE};
    border-radius: 4px;
}}

QTabBar::tab {{
    background-color: {Palette.BG_MAIN};
    color: {Palette.TEXT_SECONDARY};
    padding: 6px 12px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}}

QTabBar::tab:hover {{
    background-color: {Palette.BG_HOVER};
    color: {Palette.TEXT_PRIMARY};
}}

QTabBar::tab:selected {{
    background-color: {Palette.BG_SURFACE};
    color: {Palette.ACCENT_CYAN};
    border-bottom: 2px solid {Palette.ACCENT_CYAN};
}}

/* Scrollbars */
QScrollBar:vertical {{
    background: {Palette.BG_SURFACE};
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: {Palette.BORDER_DEFAULT};
    min-height: 20px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: {Palette.ACCENT_TEAL};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: {Palette.BG_SURFACE};
    height: 8px;
    margin: 0px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal {{
    background: {Palette.BORDER_DEFAULT};
    min-width: 20px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {Palette.ACCENT_TEAL};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* Status Bar */
QStatusBar {{
    background-color: {Palette.BG_SURFACE};
    color: {Palette.TEXT_SECONDARY};
    border-top: 1px solid {Palette.BORDER_SUBTLE};
    min-height: 26px;
}}

QStatusBar::item {{
    border: none;
}}

/* Group Box */
QGroupBox {{
    font-weight: bold;
    border: 1px solid {Palette.BORDER_SUBTLE};
    border-radius: 6px;
    margin-top: 8px;
    padding-top: 10px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 8px;
    padding: 0 4px;
    color: {Palette.TEXT_SECONDARY};
    font-size: 11px;
    text-transform: uppercase;
}}
"""


def apply_dark_theme(target: QApplication | QWidget) -> None:
    """Apply the QCanvas dark engineering theme to an application or root widget."""
    target.setStyleSheet(DARK_THEME_QSS)


__all__ = ["DARK_THEME_QSS", "Palette", "apply_dark_theme"]
