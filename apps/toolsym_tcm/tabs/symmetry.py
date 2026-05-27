"""Symmetry tab.

Computes the symmetry paper's D̄ metric and classifies via the three-zone
thresholds. Two-edge tools that the hybrid classifier can't handle live
here.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

import numpy as np

from toolsym.geometry import (
    build_master_mask,
    estimate_tilt_and_centerline,
    rotate_to_axis,
)
from toolsym.io.masks import load_mask_sequence
from toolsym.symmetry import (
    ThreeZoneConfig,
    phase_shift_metric,
    three_zone_classify,
)
from toolsym.symmetry.phase_shift import right_half_pixel_counts

from apps.toolsym_tcm.tabs._base import BaseTab


class SymmetryTab(BaseTab):
    title = "Symmetry"

    def build(self) -> None:
        layout: QVBoxLayout = self._layout  # type: ignore[assignment]

        inputs = QGroupBox("Inputs")
        form = QFormLayout(inputs)

        folder_row = QHBoxLayout()
        self._folder = QLineEdit()
        self._folder.setPlaceholderText("Pick a folder of binary masks…")
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._on_browse)
        folder_row.addWidget(self._folder, 1)
        folder_row.addWidget(browse)
        form.addRow("Mask folder", folder_row)

        self._n_edges = QSpinBox()
        self._n_edges.setRange(2, 12)
        self._n_edges.setSingleStep(2)
        self._n_edges.setValue(2)
        form.addRow("Number of edges (even)", self._n_edges)

        self._roi_height = QSpinBox()
        self._roi_height.setRange(0, 4000)
        self._roi_height.setValue(0)
        self._roi_height.setSpecialValueText("(full height)")
        form.addRow("ROI height (px)", self._roi_height)

        self._t_noise = QDoubleSpinBox()
        self._t_noise.setRange(0.0, 1e6)
        self._t_noise.setValue(1500.0)
        form.addRow("T_noise", self._t_noise)

        self._t_fracture = QDoubleSpinBox()
        self._t_fracture.setRange(0.0, 1e6)
        self._t_fracture.setValue(3500.0)
        form.addRow("T_fracture", self._t_fracture)

        self._do_perspective = QCheckBox("Run perspective correction (master mask → tilt → centerline)")
        self._do_perspective.setChecked(True)
        form.addRow("", self._do_perspective)

        layout.addWidget(inputs)

        run = QPushButton("Compute D̄")
        run.clicked.connect(self._on_run)
        layout.addWidget(run, alignment=Qt.AlignmentFlag.AlignLeft)

        self._verdict = QLabel("(no result yet)")
        self._verdict.setStyleSheet("font-size: 14pt; font-weight: 600;")
        layout.addWidget(self._verdict)

        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setStyleSheet(
            "QPlainTextEdit { background: #000; color: #d0d0d0; font-family: Consolas, monospace; }"
        )
        layout.addWidget(self._log, 1)

    def _on_browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Pick a folder of binary masks", str(self.data_root())
        )
        if folder:
            self._folder.setText(folder)

    def _on_run(self) -> None:
        folder = Path(self._folder.text().strip())
        if not folder.is_dir():
            self._verdict.setText("✗ Pick a valid mask folder first")
            return
        self._log.clear()
        try:
            masks, _ = load_mask_sequence(folder)
            self._log.appendPlainText(f"Loaded {masks.shape[0]} masks, shape {masks.shape[1:]}")

            centerline_x: int | None = None
            if self._do_perspective.isChecked():
                # Symmetry paper §2.2: build master mask, regress tilt + centerline,
                # rotate every frame to undo tilt, use the recovered centerline.
                master = build_master_mask(masks)
                tc = estimate_tilt_and_centerline(master)
                self._log.appendPlainText(
                    f"Tilt: {tc.tilt_deg:+.3f}°  centerline_x (top, bottom): "
                    f"{tc.centerline_x_top:.1f}, {tc.centerline_x_bottom:.1f}"
                )
                if abs(tc.tilt_deg) > 0.05:
                    self._log.appendPlainText("Rotating frames to rectify axial misalignment…")
                    rectified = np.empty_like(masks)
                    for i in range(masks.shape[0]):
                        rectified[i] = rotate_to_axis(masks[i], tc.tilt_deg)
                    masks = rectified
                # Use centerline at the tip (bottom) of the image.
                centerline_x = int(round(tc.centerline_x_bottom))

            roi = self._roi_height.value() or None
            counts = right_half_pixel_counts(
                masks, roi_height=roi, centerline_x=centerline_x
            )
            phase = phase_shift_metric(counts, n_edges=self._n_edges.value())
            d_bar = phase.mean_abs_diff
            cfg = ThreeZoneConfig(t_noise=self._t_noise.value(), t_fracture=self._t_fracture.value())
            result = three_zone_classify(d_bar, cfg)
            self._log.appendPlainText(
                f"D̄ = {d_bar:.2f} px ({phase.relative_pct:.2f}% of mean right-half area) "
                f"→ zone {result.zone.value}"
            )
            colour = {
                "safe": "#50c070",
                "warning": "#d0a050",
                "fracture": "#d05050",
            }[result.zone.value]
            self._verdict.setText(f"D̄ = {d_bar:.1f}  →  {result.zone.value.upper()}")
            self._verdict.setStyleSheet(
                f"color: {colour}; font-size: 14pt; font-weight: 700;"
            )
        except Exception as exc:  # noqa: BLE001
            self._verdict.setText(f"✗ Error: {exc}")
            self._verdict.setStyleSheet("color: #d05050; font-size: 12pt;")
            self._log.appendPlainText(f"ERROR: {exc!r}")
