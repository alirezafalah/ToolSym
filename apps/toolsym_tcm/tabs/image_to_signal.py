"""Image-to-Signal tab.

Skeleton that wires the toolsym.signal pipeline to a minimal PySide6
UI: pick a folder of masks, set ROI height, run the full hybrid
classification, and display the verdict.

The full feature-rich port of the legacy PyQt6 GUI (live previews,
per-step parameter tuning, plot exports) is tracked in MIGRATION.md
and will land in subsequent commits — this skeleton is enough to prove
the library wiring works end-to-end.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
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

from toolsym.io.masks import load_mask_sequence
from toolsym.signal import (
    area_signal_from_masks,
    classify_segment_consistency,
    classify_sinusoidal_distances,
    find_segments,
    fit_segment_sinusoidals,
    pairwise_coefficient_distances,
    preprocess_signal,
)

from apps.toolsym_tcm.tabs._base import BaseTab


class ImageToSignalTab(BaseTab):
    title = "Image to Signal"

    def build(self) -> None:
        layout: QVBoxLayout = self._layout  # type: ignore[assignment]

        # ── Inputs ──────────────────────────────────────────────────────
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

        self._roi_height = QSpinBox()
        self._roi_height.setRange(20, 4000)
        self._roi_height.setValue(350)
        form.addRow("ROI height (px)", self._roi_height)

        layout.addWidget(inputs)

        # ── Action ──────────────────────────────────────────────────────
        run = QPushButton("Run hybrid classifier")
        run.clicked.connect(self._on_run)
        layout.addWidget(run, alignment=Qt.AlignmentFlag.AlignLeft)

        # ── Output ──────────────────────────────────────────────────────
        self._verdict = QLabel("(no result yet)")
        self._verdict.setStyleSheet("font-size: 14pt; font-weight: 600;")
        layout.addWidget(self._verdict)

        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumBlockCount(2000)
        self._log.setStyleSheet(
            "QPlainTextEdit { background: #000; color: #d0d0d0; font-family: Consolas, monospace; }"
        )
        layout.addWidget(self._log, 1)

    # ------------------------------------------------------------------
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
            self._log.appendPlainText(f"Loading masks from {folder}…")
            masks, paths = load_mask_sequence(folder)
            self._log.appendPlainText(f"  loaded {len(paths)} masks, shape {masks.shape[1:]}")

            signal = area_signal_from_masks(masks, roi_height=self._roi_height.value())
            self._log.appendPlainText(
                f"  area signal: min={signal.min()} max={signal.max()} mean={signal.mean():.1f}"
            )

            signal_proc, _ = preprocess_signal(signal)
            segs = find_segments(signal_proc)
            self._log.appendPlainText(
                f"  {segs.n_segments} segments, sizes={segs.segment_sizes_deg.round(1).tolist()}°"
            )

            consistency = classify_segment_consistency(segs.segment_sizes_deg)
            self._log.appendPlainText(
                f"  segment-size deviation: {consistency.max_deviation_pct:.2f}% "
                f"(tolerance {consistency.tolerance_pct}%) — "
                f"{'INTACT' if consistency.intact else 'FRACTURED'}"
            )
            if not consistency.intact:
                self._verdict.setText("✗ FRACTURED (size-deviation check)")
                self._verdict.setStyleSheet("color: #d05050; font-size: 14pt; font-weight: 700;")
                return

            if segs.n_segments < 3:
                self._verdict.setText(
                    "⚠ INTACT by sizes — too few segments for sinusoidal check (use Symmetry tab)"
                )
                self._verdict.setStyleSheet("color: #d0a050; font-size: 14pt; font-weight: 700;")
                return

            fits = fit_segment_sinusoidals(signal_proc, None, segs.n_segments)
            distances = pairwise_coefficient_distances(fits)
            decision = classify_sinusoidal_distances(distances)
            self._log.appendPlainText(
                f"  sinusoidal: min_d={decision.min_distance:.3f} "
                f"max_d={decision.max_distance:.3f} threshold={decision.threshold:.3f}"
            )
            if decision.intact:
                self._verdict.setText("✓ INTACT")
                self._verdict.setStyleSheet("color: #50c070; font-size: 14pt; font-weight: 700;")
            else:
                self._verdict.setText("✗ FRACTURED (sinusoidal check)")
                self._verdict.setStyleSheet("color: #d05050; font-size: 14pt; font-weight: 700;")
        except Exception as exc:  # noqa: BLE001 — surface anything to the UI
            self._verdict.setText(f"✗ Error: {exc}")
            self._verdict.setStyleSheet("color: #d05050; font-size: 12pt;")
            self._log.appendPlainText(f"ERROR: {exc!r}")
