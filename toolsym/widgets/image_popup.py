"""Full-resolution scroll-and-zoom image viewer.

Lifted from ``simulation_gui.py`` and generalised — both apps reuse it
for any "click thumbnail → see full image" interaction.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QWheelEvent
from PySide6.QtWidgets import QDialog, QLabel, QScrollArea, QVBoxLayout

__all__ = ["ImagePopup"]


class ImagePopup(QDialog):
    """Non-modal image viewer with mouse-wheel zoom (0.1× – 10×)."""

    MIN_ZOOM = 0.1
    MAX_ZOOM = 10.0
    ZOOM_STEP = 1.15

    def __init__(self, pixmap: QPixmap, title: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title or "Preview")
        self.setModal(False)
        self._zoom = 1.0
        self._pixmap = pixmap

        self._label = QLabel()
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setPixmap(pixmap)

        scroll = QScrollArea(self)
        scroll.setWidget(self._label)
        scroll.setWidgetResizable(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

        size = pixmap.size()
        self.resize(min(size.width(), 1200), min(size.height(), 900))

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802 — Qt naming
        notches = event.angleDelta().y() / 120
        factor = self.ZOOM_STEP**notches
        self._set_zoom(self._zoom * factor)
        event.accept()

    def _set_zoom(self, zoom: float) -> None:
        self._zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, zoom))
        size = self._pixmap.size() * self._zoom
        self._label.setPixmap(
            self._pixmap.scaled(
                size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self._label.adjustSize()
