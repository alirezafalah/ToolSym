"""Visual Hull tab — Shape-from-Silhouette on real masks."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

import numpy as np

from toolsym.geometry import (
    build_master_mask,
    estimate_tilt_and_centerline,
    rotate_to_axis,
)
from toolsym.io.masks import load_mask_sequence
from toolsym.io.voxels import save_voxel_grid, voxel_grid_to_obj
from toolsym.reconstruction import CarverConfig, carve_visual_hull

from apps.toolsym_tcm.tabs._base import BaseTab


class _CarveWorker(QThread):
    progress = Signal(float, str)
    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        masks_folder: Path,
        out_npz: Path,
        export_obj: bool,
        rectify: bool,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._masks_folder = masks_folder
        self._out_npz = out_npz
        self._export_obj = export_obj
        self._rectify = rectify

    def run(self) -> None:
        try:
            masks, _ = load_mask_sequence(self._masks_folder)
            self.progress.emit(0.05, f"Loaded {masks.shape[0]} masks")
            if self._rectify:
                master = build_master_mask(masks)
                tc = estimate_tilt_and_centerline(master)
                self.progress.emit(0.07, f"Tilt {tc.tilt_deg:+.3f}°")
                if abs(tc.tilt_deg) > 0.05:
                    rectified = np.empty_like(masks)
                    for i in range(masks.shape[0]):
                        rectified[i] = rotate_to_axis(masks[i], tc.tilt_deg)
                    masks = rectified
                    self.progress.emit(0.09, "Rectified all frames")
            cfg = CarverConfig.from_spec()
            result = carve_visual_hull(masks, config=cfg, progress=lambda f, m: self.progress.emit(0.1 + 0.85 * f, m))
            save_voxel_grid(
                result.voxel_grid,
                result.volume_bounds_mm,
                result.grid_shape,
                self._out_npz,
            )
            self.progress.emit(0.97, f"Saved {self._out_npz.name}")
            if self._export_obj:
                obj_path = self._out_npz.with_suffix(".obj")
                voxel_grid_to_obj(result.voxel_grid, result.volume_bounds_mm, obj_path)
                self.progress.emit(0.99, f"Wrote {obj_path.name}")
            self.finished_ok.emit(result)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(repr(exc))


class VisualHullTab(BaseTab):
    title = "Visual Hull"

    def build(self) -> None:
        layout: QVBoxLayout = self._layout  # type: ignore[assignment]

        inputs = QGroupBox("Inputs")
        form = QFormLayout(inputs)

        folder_row = QHBoxLayout()
        self._folder = QLineEdit()
        self._folder.setPlaceholderText("Pick a folder of binary masks…")
        browse_in = QPushButton("Browse…")
        browse_in.clicked.connect(self._on_browse_in)
        folder_row.addWidget(self._folder, 1)
        folder_row.addWidget(browse_in)
        form.addRow("Mask folder", folder_row)

        out_row = QHBoxLayout()
        self._out = QLineEdit()
        self._out.setPlaceholderText("Output .npz path")
        browse_out = QPushButton("Save as…")
        browse_out.clicked.connect(self._on_browse_out)
        out_row.addWidget(self._out, 1)
        out_row.addWidget(browse_out)
        form.addRow("Output", out_row)

        self._export_obj = QCheckBox("Also export .obj (marching cubes)")
        form.addRow("", self._export_obj)

        self._rectify = QCheckBox("Rectify tilt before carving (master mask → tilt regression)")
        self._rectify.setChecked(True)
        form.addRow("", self._rectify)

        layout.addWidget(inputs)

        run = QPushButton("Carve hull")
        run.clicked.connect(self._on_run)
        layout.addWidget(run, alignment=Qt.AlignmentFlag.AlignLeft)

        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        layout.addWidget(self._bar)

        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setStyleSheet(
            "QPlainTextEdit { background: #000; color: #d0d0d0; font-family: Consolas, monospace; }"
        )
        layout.addWidget(self._log, 1)

        self._worker: _CarveWorker | None = None

    def _on_browse_in(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Pick a folder of binary masks", str(self.data_root())
        )
        if folder:
            self._folder.setText(folder)

    def _on_browse_out(self) -> None:
        out, _ = QFileDialog.getSaveFileName(
            self, "Save hull NPZ as", str(self.data_root() / "hull.npz"), "NumPy NPZ (*.npz)"
        )
        if out:
            self._out.setText(out)

    def _on_run(self) -> None:
        folder = Path(self._folder.text().strip())
        out = Path(self._out.text().strip() or self.data_root() / "hull.npz")
        if not folder.is_dir():
            self._log.appendPlainText("Pick a valid mask folder first")
            return
        self._log.clear()
        self._bar.setValue(0)
        self._worker = _CarveWorker(
            folder, out, self._export_obj.isChecked(), self._rectify.isChecked(), self
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_ok.connect(self._on_done)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_progress(self, fraction: float, message: str) -> None:
        self._bar.setValue(int(round(fraction * 100)))
        if message:
            self._log.appendPlainText(message)

    def _on_done(self, result) -> None:  # noqa: ANN001 — HullResult is dataclass
        self._log.appendPlainText(
            f"Done in {result.elapsed_seconds:.1f}s — backend {result.backend_used}, "
            f"occupancy {int(result.voxel_grid.sum())}/{result.voxel_grid.size}"
        )
        self._bar.setValue(100)

    def _on_failed(self, message: str) -> None:
        self._log.appendPlainText(f"ERROR: {message}")
        self._bar.setValue(0)
