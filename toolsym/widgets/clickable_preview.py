"""Clickable thumbnail that opens an :class:`ImagePopup` on click."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent, QPixmap
from PySide6.QtWidgets import QLabel, QWidget

from toolsym.widgets.image_popup import ImagePopup

__all__ = ["ClickablePreview"]


class ClickablePreview(QLabel):
    """A QLabel that opens a full-resolution popup when clicked.

    Maintains a separate ``_full_pixmap`` so the displayed thumbnail can
    be scaled down without losing the high-resolution source.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumSize(160, 120)
        self.setStyleSheet(
            "QLabel { border: 1px solid #2a2a2a; background: #161616; }"
        )
        self._full_pixmap: QPixmap | None = None
        self._popup: ImagePopup | None = None

    def set_full_pixmap(self, pixmap: QPixmap | None) -> None:
        """Update both the thumbnail and the source pixmap."""
        self._full_pixmap = pixmap
        if pixmap is None or pixmap.isNull():
            self.clear()
            self.setText("(no preview)")
            return
        thumb = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.setPixmap(thumb)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802 — Qt naming
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._full_pixmap is not None
        ):
            self._popup = ImagePopup(self._full_pixmap, parent=self.window())
            self._popup.show()
        super().mousePressEvent(event)
