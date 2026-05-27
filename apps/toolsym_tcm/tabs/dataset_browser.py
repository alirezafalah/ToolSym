"""Dataset Browser tab — successor to ``tool_profile_viz``.

Shows the per-tool folder structure under the DATA root and lets the
user click through individual frames. Currently a minimal placeholder;
full feature port (waveform overlay, multi-tool comparison) is tracked
in MIGRATION.md.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QDir, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileSystemModel,
    QHBoxLayout,
    QListWidget,
    QSplitter,
    QTreeView,
)

from toolsym.widgets import ClickablePreview

from apps.toolsym_tcm.tabs._base import BaseTab


class DatasetBrowserTab(BaseTab):
    title = "Dataset Browser"

    def build(self) -> None:
        self._model = QFileSystemModel()
        self._model.setFilter(QDir.Filter.Dirs | QDir.Filter.NoDotAndDotDot | QDir.Filter.Files)
        self._model.setRootPath(str(self.data_root()))

        self._tree = QTreeView()
        self._tree.setModel(self._model)
        self._tree.setRootIndex(self._model.index(str(self.data_root())))
        self._tree.setColumnHidden(1, True)
        self._tree.setColumnHidden(2, True)
        self._tree.setColumnHidden(3, True)
        self._tree.clicked.connect(self._on_clicked)

        self._frames = QListWidget()
        self._frames.itemClicked.connect(self._on_frame_clicked)

        self._preview = ClickablePreview()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._tree)
        splitter.addWidget(self._frames)
        splitter.addWidget(self._preview)
        splitter.setSizes([260, 220, 600])
        wrapper = QHBoxLayout()
        wrapper.addWidget(splitter)
        self._layout.addLayout(wrapper)

    def on_data_root_changed(self, path: Path) -> None:
        self._model.setRootPath(str(path))
        self._tree.setRootIndex(self._model.index(str(path)))

    def _on_clicked(self, index) -> None:  # noqa: ANN001 — Qt model index
        path = Path(self._model.filePath(index))
        self._frames.clear()
        if path.is_dir():
            from toolsym.io.masks import iter_mask_paths

            try:
                for p in iter_mask_paths(path):
                    self._frames.addItem(p.name)
                self._frames.setProperty("folder", str(path))
            except FileNotFoundError:
                pass

    def _on_frame_clicked(self, item) -> None:  # noqa: ANN001 — QListWidgetItem
        folder = Path(self._frames.property("folder") or "")
        if not folder.is_dir():
            return
        path = folder / item.text()
        pix = QPixmap(str(path))
        if not pix.isNull():
            self._preview.set_full_pixmap(pix)
