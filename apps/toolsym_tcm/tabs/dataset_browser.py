"""Dataset Browser tab.

Three-pane explorer for the DATA root:

* Left   — filesystem tree.
* Middle — preview pane that switches based on what you click:
            - image file → high-res preview (click to popup-zoom)
            - CSV file   → first 2000 rows in a table
            - folder of masks → list of frames
* Right  — selected-frame preview when browsing a mask folder.
"""

from __future__ import annotations

import csv
from pathlib import Path

from PySide6.QtCore import QDir, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileSystemModel,
    QHeaderView,
    QLabel,
    QListWidget,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from toolsym.widgets import ClickablePreview

from apps.toolsym_tcm.tabs._base import BaseTab

IMAGE_EXTS = {".png", ".tif", ".tiff", ".bmp", ".jpg", ".jpeg"}


class DatasetBrowserTab(BaseTab):
    title = "Dataset Browser"

    def build(self) -> None:
        self._model = QFileSystemModel()
        self._model.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot)
        self._model.setRootPath(str(self.data_root()))

        self._tree = QTreeView()
        self._tree.setModel(self._model)
        self._tree.setRootIndex(self._model.index(str(self.data_root())))
        for col in (1, 2, 3):
            self._tree.setColumnHidden(col, True)
        self._tree.clicked.connect(self._on_tree_clicked)

        # Middle: a stacked widget — frame list / csv table / placeholder
        self._middle = QStackedWidget()
        self._placeholder = QLabel("Click a folder of masks or a CSV file.")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._middle.addWidget(self._placeholder)

        self._frames = QListWidget()
        self._frames.itemClicked.connect(self._on_frame_clicked)
        self._middle.addWidget(self._frames)

        self._csv_table = QTableWidget()
        self._csv_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._csv_table.setAlternatingRowColors(True)
        self._middle.addWidget(self._csv_table)

        self._preview = ClickablePreview()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._tree)
        splitter.addWidget(self._middle)
        splitter.addWidget(self._preview)
        splitter.setSizes([280, 360, 540])
        self._layout.addWidget(splitter)

    # ------------------------------------------------------------------
    def on_data_root_changed(self, path: Path) -> None:
        self._model.setRootPath(str(path))
        self._tree.setRootIndex(self._model.index(str(path)))

    def _on_tree_clicked(self, index) -> None:  # noqa: ANN001
        path = Path(self._model.filePath(index))
        if path.is_dir():
            self._show_mask_folder(path)
            return
        suffix = path.suffix.lower()
        if suffix == ".csv":
            self._show_csv(path)
            return
        if suffix in IMAGE_EXTS:
            self._preview.set_full_pixmap(QPixmap(str(path)))
            self._middle.setCurrentWidget(self._placeholder)
            self._placeholder.setText(f"Image: {path.name}")
            return
        self._middle.setCurrentWidget(self._placeholder)
        self._placeholder.setText(f"(no preview for {suffix or 'this file'})")
        self._preview.set_full_pixmap(None)

    def _show_mask_folder(self, folder: Path) -> None:
        from toolsym.io.masks import iter_mask_paths

        self._frames.clear()
        try:
            paths = list(iter_mask_paths(folder))
        except FileNotFoundError:
            paths = []
        if not paths:
            self._middle.setCurrentWidget(self._placeholder)
            self._placeholder.setText(f"{folder.name} — no mask images inside")
            return
        for p in paths:
            self._frames.addItem(p.name)
        self._frames.setProperty("folder", str(folder))
        self._middle.setCurrentWidget(self._frames)

    def _show_csv(self, path: Path) -> None:
        max_rows = 2000
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.reader(fh)
            try:
                header = next(reader)
            except StopIteration:
                self._csv_table.setRowCount(0)
                self._csv_table.setColumnCount(0)
                self._middle.setCurrentWidget(self._csv_table)
                return
            rows: list[list[str]] = []
            for i, row in enumerate(reader):
                if i >= max_rows:
                    break
                rows.append(row)
        self._csv_table.setColumnCount(len(header))
        self._csv_table.setHorizontalHeaderLabels(header)
        self._csv_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row[: len(header)]):
                item = QTableWidgetItem(val)
                self._csv_table.setItem(r, c, item)
        header_view = self._csv_table.horizontalHeader()
        header_view.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header_view.setStretchLastSection(True)
        self._middle.setCurrentWidget(self._csv_table)

    def _on_frame_clicked(self, item) -> None:  # noqa: ANN001
        folder = Path(self._frames.property("folder") or "")
        if not folder.is_dir():
            return
        path = folder / item.text()
        pix = QPixmap(str(path))
        if not pix.isNull():
            self._preview.set_full_pixmap(pix)
