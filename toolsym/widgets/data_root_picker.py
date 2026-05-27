"""Widget for picking and persisting the DATA root folder."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)

from toolsym.config import data_root

__all__ = ["DataRootPicker"]


class DataRootPicker(QWidget):
    """Inline widget + persistence for the DATA root.

    Emits :attr:`changed` whenever the user picks a new folder. The
    value is also written to :class:`QSettings` (key
    ``toolsym/data_root``) so subsequent runs of either app reuse it.
    """

    changed = Signal(Path)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = QSettings("ToolSym", "ToolSym")
        initial = self._settings.value("toolsym/data_root", "", type=str)
        self._path = Path(initial) if initial else data_root()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("DATA:"))
        self._edit = QLineEdit(str(self._path))
        self._edit.editingFinished.connect(self._on_edit)
        layout.addWidget(self._edit, 1)
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._on_browse)
        layout.addWidget(browse)

    def current(self) -> Path:
        return self._path

    def _on_browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Pick the DATA folder", str(self._path)
        )
        if folder:
            self._set(Path(folder))

    def _on_edit(self) -> None:
        text = self._edit.text().strip()
        if text:
            self._set(Path(text))

    def _set(self, path: Path) -> None:
        self._path = data_root(path)
        self._edit.setText(str(self._path))
        self._settings.setValue("toolsym/data_root", str(self._path))
        self.changed.emit(self._path)
