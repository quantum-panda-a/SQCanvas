"""Live filesystem watcher and hot-reload debouncer for SQCanvas GUI."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QFileSystemWatcher, QObject, QTimer, Signal

if TYPE_CHECKING:
    pass


class ScriptWatcher(QObject):
    """Watches a Python script on disk and emits a debounced signal when modified."""

    #: Emitted when the watched file is saved/modified on disk. Passes the file Path.
    file_modified = Signal(object)

    def __init__(self, parent: QObject | None = None, debounce_ms: int = 150) -> None:
        super().__init__(parent)
        self.debounce_ms = debounce_ms
        self._current_path: Path | None = None

        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._on_file_changed)

        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(self.debounce_ms)
        self._debounce_timer.timeout.connect(self._on_debounce_timeout)

        self.enabled: bool = True

    @property
    def is_watching(self) -> bool:
        return self._current_path is not None and self.enabled

    @property
    def active_path(self) -> Path | None:
        return self._current_path

    def watch(self, filepath: str | Path | None) -> None:
        """Set the active script to watch."""
        self.unwatch()

        if filepath is None:
            return

        path = Path(filepath).resolve()
        if not path.exists():
            return

        self._current_path = path
        self._watcher.addPath(str(path))

    def unwatch(self) -> None:
        """Stop watching current script file."""
        if self._current_path is not None:
            try:
                self._watcher.removePath(str(self._current_path))
            except Exception:
                pass
            self._current_path = None
        self._debounce_timer.stop()

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable change notifications."""
        self.enabled = enabled
        if not enabled:
            self._debounce_timer.stop()

    def _on_file_changed(self, path_str: str) -> None:
        """Handle raw Qt file change notification and trigger debouncing."""
        if not self.enabled or self._current_path is None:
            return

        # Re-add path in case the editor used atomic file replacement (write temp -> rename)
        if str(self._current_path) not in self._watcher.files():
            if self._current_path.exists():
                try:
                    self._watcher.addPath(str(self._current_path))
                except Exception:
                    pass

        self._debounce_timer.start(self.debounce_ms)

    def _on_debounce_timeout(self) -> None:
        """Emit debounced file modification signal."""
        if self.enabled and self._current_path is not None and self._current_path.exists():
            self.file_modified.emit(self._current_path)
