"""Reusable progress dialog with abort + log."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

__all__ = ["ProgressDialog"]


class ProgressDialog(QDialog):
    """Modal-but-cancellable progress dialog.

    Workers should connect to :attr:`aborted` and poll it periodically.
    Use :meth:`set_progress` and :meth:`log` to push updates.
    """

    aborted = Signal()

    def __init__(self, title: str = "Working…", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(420)

        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)

        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumBlockCount(2000)
        self._log.setStyleSheet(
            "QPlainTextEdit { background: #000; color: #6ec06e; font-family: Consolas, monospace; }"
        )
        self._log.setMinimumHeight(140)

        self._abort_btn = QPushButton("Abort")
        self._abort_btn.clicked.connect(self._on_abort)

        layout = QVBoxLayout(self)
        layout.addWidget(self._bar)
        layout.addWidget(self._log)
        layout.addWidget(self._abort_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def set_progress(self, fraction: float, message: str | None = None) -> None:
        self._bar.setValue(int(round(max(0.0, min(1.0, fraction)) * 100)))
        if message:
            self.log(message)

    def log(self, line: str) -> None:
        self._log.appendPlainText(line)

    def _on_abort(self) -> None:
        self._abort_btn.setEnabled(False)
        self._abort_btn.setText("Aborting…")
        self.aborted.emit()

    def finish(self, message: str = "Done.") -> None:
        self.set_progress(1.0, message)
        self._abort_btn.setText("Close")
        self._abort_btn.setEnabled(True)
        try:
            self._abort_btn.clicked.disconnect()
        except RuntimeError:
            pass
        self._abort_btn.clicked.connect(self.accept)
