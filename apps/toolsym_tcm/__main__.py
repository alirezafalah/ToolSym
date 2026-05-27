"""Entry point for ``toolsym-tcm``."""

from __future__ import annotations

import sys

from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from toolsym import __version__
from toolsym.widgets import apply_dark_theme

from apps.toolsym_tcm.main_window import MainWindow


def _resolve_icon() -> QIcon | None:
    try:
        from importlib.resources import files

        path = files("toolsym").joinpath("resources/app_icon.ico")
        return QIcon(str(path))
    except (ModuleNotFoundError, FileNotFoundError):
        return None


def main(argv: list[str] | None = None) -> int:
    QCoreApplication.setOrganizationName("ToolSym")
    QCoreApplication.setApplicationName("ToolSym TCM")
    QCoreApplication.setApplicationVersion(__version__)

    app = QApplication(argv if argv is not None else sys.argv)
    apply_dark_theme(app)
    icon = _resolve_icon()
    if icon is not None:
        app.setWindowIcon(icon)

    window = MainWindow()
    window.show()
    return int(app.exec())


if __name__ == "__main__":
    raise SystemExit(main())
