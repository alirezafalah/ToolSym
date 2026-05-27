"""Entry point for ``toolsym-sim``."""

from __future__ import annotations

import sys

from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from toolsym import __version__
from toolsym.widgets import apply_dark_theme

from apps.toolsym_sim.main_window import MainWindow


def _resolve_icon() -> QIcon | None:
    from importlib.resources import files

    try:
        anchor = files("toolsym").joinpath("resources")
        png = anchor.joinpath("app_icon.png")
        ico = anchor.joinpath("app_icon.ico")
        icon = QIcon()
        if png.is_file():
            icon.addFile(str(png))
        if ico.is_file():
            icon.addFile(str(ico))
        return icon if not icon.isNull() else None
    except (ModuleNotFoundError, FileNotFoundError):
        return None


def main(argv: list[str] | None = None) -> int:
    QCoreApplication.setOrganizationName("ToolSym")
    QCoreApplication.setApplicationName("ToolSym Sim")
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
