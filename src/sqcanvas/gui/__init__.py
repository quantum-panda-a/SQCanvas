"""The SQCanvas desktop viewer (ships with the default install)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import matplotlib

# Mute matplotlib's internal verbose loggers in interactive sessions
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("matplotlib.axes._base").setLevel(logging.WARNING)

# Must be set before any matplotlib pyplot / backend import under Qt.
matplotlib.use("QtAgg")

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication

from sqcanvas.gui.main_window import MainWindow


def _is_in_ipython() -> bool:
    """Return True if executing inside an interactive IPython/Jupyter kernel."""
    try:
        from IPython import get_ipython

        return get_ipython() is not None
    except Exception:
        return False


def _enable_ipython_gui() -> None:
    """Hook Qt event processing into the active IPython/Jupyter loop if available."""
    try:
        from IPython import get_ipython

        ip = get_ipython()
        if ip is not None:
            for gui_backend in ("qt6", "qt"):
                try:
                    ip.enable_gui(gui_backend)
                    break
                except Exception:
                    pass
    except Exception:
        pass


def launch(design=None) -> MainWindow | None:
    """Create and show a :class:`MainWindow` for ``design`` non-blockingly.

    In interactive environments like Jupyter / IPython, this hooks the Qt event
    loop so cell execution continues immediately while the GUI stays open as a live dashboard.
    """
    import os

    if os.environ.get("SQCANVAS_HEADLESS_LOAD") == "1":
        return None

    _enable_ipython_gui()
    from pathlib import Path
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    icon_path = Path(__file__).parent / "resources" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow(design=design)
    window.show()
    return window


def run(design=None) -> None:
    """Launch the viewer and enter the Qt event loop.

    If run inside an interactive IPython/Jupyter session, this automatically delegates
    to non-blocking mode (:func:`launch`) to avoid freezing the notebook kernel.
    In standard standalone Python scripts, it blocks until the window is closed.
    """
    import os

    if os.environ.get("SQCANVAS_HEADLESS_LOAD") == "1":
        return
    _enable_ipython_gui()
    from pathlib import Path
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    icon_path = Path(__file__).parent / "resources" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow(design=design)
    window.show()

    if not _is_in_ipython():
        app.exec()


logger = logging.getLogger(__name__)

IPC_SERVER_NAME = "sqcanvas_cad_single_instance_ipc"


def _configure_high_dpi() -> None:
    """Enable crisp High-DPI rendering on Windows (125%/150%) and macOS Retina displays."""
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QGuiApplication

        if hasattr(Qt, "HighDpiScaleFactorRoundingPolicy"):
            QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
                Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
            )
    except Exception:  # noqa: BLE001, S110
        pass


def _try_send_to_existing_instance(filepath: str | None = None, theme: str | None = None) -> bool:
    """Attempt to forward an open request to an already running SQCanvas GUI instance via IPC."""
    import json
    import os

    if os.environ.get("SQCANVAS_HEADLESS_LOAD") == "1":
        return False

    try:
        from PySide6.QtNetwork import QLocalSocket
        from PySide6.QtWidgets import QApplication

        # Ensure minimal QApplication exists for event handling if not initialized
        _app = QApplication.instance() or QApplication([])
        socket = QLocalSocket()
        socket.connectToServer(IPC_SERVER_NAME)
        if not socket.waitForConnected(300):
            return False

        payload = json.dumps({"file": filepath, "theme": theme}).encode("utf-8")
        socket.write(payload)
        socket.flush()
        socket.waitForBytesWritten(500)
        socket.disconnectFromServer()
        return True
    except Exception:  # noqa: BLE001, S110
        return False


def _setup_ipc_server(window: MainWindow, app: QApplication) -> Any:
    """Set up local socket server to listen for new files opened from terminal."""
    import json

    from PySide6.QtNetwork import QLocalServer

    server = QLocalServer(app)
    # Clean up any stale socket from past abnormal exits
    server.removeServer(IPC_SERVER_NAME)
    if not server.listen(IPC_SERVER_NAME):
        logger.debug("Could not start IPC server: %s", server.errorString())
        return None

    def _on_new_connection() -> None:
        client_socket = server.nextPendingConnection()
        if not client_socket:
            return

        def _on_ready_read() -> None:
            try:
                data = bytes(client_socket.readAll()).decode("utf-8")
                if data:
                    payload = json.loads(data)
                    window.handle_external_open_request(
                        filepath=payload.get("file"),
                        theme=payload.get("theme"),
                    )
            except Exception as err:  # noqa: BLE001
                logger.debug("Failed to parse IPC message: %s", err)
            finally:
                client_socket.disconnectFromServer()

        client_socket.readyRead.connect(_on_ready_read)

    server.newConnection.connect(_on_new_connection)
    return server


def run_gui_with_ipc(
    file: str | None = None,
    theme: str | None = None,
    new_instance: bool = False,
    design: Any | None = None,
) -> None:
    """Launch the SQCanvas GUI workspace with single-instance IPC awareness and High-DPI support."""
    import os
    from pathlib import Path

    if os.environ.get("SQCANVAS_HEADLESS_LOAD") == "1":
        return

    # If single-instance is enabled and another instance is running, delegate and exit cleanly
    if not new_instance and design is None:
        resolved_file = str(Path(file).resolve()) if file else None
        if _try_send_to_existing_instance(filepath=resolved_file, theme=theme):
            target_desc = f" and opened {Path(file).name}" if file else ""
            print(f"Activated existing SQCanvas CAD window{target_desc}.")
            return

    _configure_high_dpi()
    _enable_ipython_gui()
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    icon_path = Path(__file__).parent / "resources" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow(design=design)
    if theme:
        try:
            window.set_theme_preset(theme)
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to apply theme '%s': %s", theme, e)

    if file:
        file_path = Path(file)
        if file_path.exists():
            window.open_python_script(file_path)
        else:
            logger.error("Specified script file does not exist: %s", file)

    # Attach IPC Server to primary window so future invocations join as tabs
    ipc_server = _setup_ipc_server(window, app)
    # Prevent garbage collection of ipc_server
    window._ipc_server = ipc_server

    window.show()

    if not _is_in_ipython():
        app.exec()


def main(argv: list[str] | None = None) -> None:
    """CLI entry point delegating to sqcanvas.cli."""
    from sqcanvas.cli import main as cli_main

    cli_main(argv)


__all__ = ["MainWindow", "launch", "main", "run", "run_gui_with_ipc"]


