"""Common parent class for TCM tabs."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

__all__ = ["BaseTab"]


class BaseTab(QWidget):
    """A tab that holds the current DATA root and exposes a setter.

    Subclasses should override :meth:`build` (called once from
    ``__init__``) instead of writing their own constructors.
    """

    title: str = ""

    def __init__(self, data_root: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data_root = data_root
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        self._layout = layout
        self.build()

    def data_root(self) -> Path:
        return self._data_root

    def set_data_root(self, path: Path) -> None:
        self._data_root = path
        self.on_data_root_changed(path)

    def build(self) -> None:
        """Override in subclasses to populate :attr:`_layout`."""
        placeholder = QLabel(f"{self.title or self.__class__.__name__} — TODO")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(placeholder)

    def on_data_root_changed(self, path: Path) -> None:
        """Override to react to DATA-root changes."""
