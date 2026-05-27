"""ToolSym Sim main window."""

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

from apps.toolsym_sim.tabs.augment import AugmentTab
from apps.toolsym_sim.tabs.noise import NoiseTab
from apps.toolsym_sim.tabs.render import RenderTab
from apps.toolsym_sim.tabs.voxelize import VoxelizeTab


class MainWindow(QMainWindow):
    """Simulation app shell.

    Tabs share the same DATA root via :class:`DataRootPicker`.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"ToolSym Sim — v{__version__}")
        self.resize(1280, 820)

        toolbar = QToolBar("Workspace")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        self._data_picker = DataRootPicker(self)
        toolbar.addWidget(self._data_picker)

        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.addTab(RenderTab(self._data_picker.current(), self), "Render")
        tabs.addTab(NoiseTab(self._data_picker.current(), self), "Noise")
        tabs.addTab(AugmentTab(self._data_picker.current(), self), "Augment")
        tabs.addTab(VoxelizeTab(self._data_picker.current(), self), "Voxelize")

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
