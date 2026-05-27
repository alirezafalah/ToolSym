"""ToolSym TCM main window."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from toolsym import __version__
from toolsym.widgets import DataRootPicker

from apps.toolsym_tcm.tabs.dataset_browser import DatasetBrowserTab
from apps.toolsym_tcm.tabs.image_to_signal import ImageToSignalTab
from apps.toolsym_tcm.tabs.symmetry import SymmetryTab
from apps.toolsym_tcm.tabs.visual_hull import VisualHullTab


class MainWindow(QMainWindow):
    """Analysis app shell.

    Each tab is a self-contained QWidget that pulls algorithms from
    ``toolsym.*``. The shell only wires up the DATA-root picker so all
    tabs see the same folder.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"ToolSym TCM — v{__version__}")
        self.resize(1280, 820)

        toolbar = QToolBar("Workspace")
        toolbar.setMovable(False)
        toolbar.setIconSize(toolbar.iconSize() * 0.85)
        self.addToolBar(toolbar)
        self._data_picker = DataRootPicker(self)
        toolbar.addWidget(self._data_picker)

        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.addTab(ImageToSignalTab(self._data_picker.current(), self), "Image to Signal")
        tabs.addTab(SymmetryTab(self._data_picker.current(), self), "Symmetry")
        tabs.addTab(VisualHullTab(self._data_picker.current(), self), "Visual Hull")
        tabs.addTab(DatasetBrowserTab(self._data_picker.current(), self), "Dataset Browser")

        # When the DATA root changes, push it to every tab.
        self._data_picker.changed.connect(
            lambda p: [tabs.widget(i).set_data_root(p) for i in range(tabs.count())]
        )

        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(tabs)
        self.setCentralWidget(wrapper)

        status = QStatusBar()
        status.addPermanentWidget(QLabel(f"v{__version__}"), 0)
        self.setStatusBar(status)
