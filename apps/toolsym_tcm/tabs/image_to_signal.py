"""Image-to-Signal tab — full pipeline GUI.

Mirrors the legacy ``image_to_signal.gui_main`` controls but drives the
vendored pipeline in :mod:`toolsym.pipeline`, with the canonical
classifier from :mod:`toolsym.signal` running afterwards.

Layout
------
Left column (parameters):
  * Tool selector (auto-populated from tools_metadata.csv).
  * Backend: GPU (OpenCL) / Multi-core / Single-core.
  * Image-processing params: blur_kernel, closing_kernel.
  * Background subtraction: method dropdown + difference threshold + L/a/b/V thresholds.
  * Analysis params: roi_height, NUMBER_OF_PEAKS, moving average, outlier threshold.
  * Pipeline step checkboxes (which steps to run).
  * Hybrid classifier params (alpha, beta).

Right column (output):
  * Log console with timestamped progress.
  * Verdict header (INTACT / FRACTURED + diagnostics).
  * "Show raw plot" / "Show processed plot" / "Open CSV folder" buttons.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from toolsym.io.dataset import DatasetLayout, build_legacy_config, iter_tools

from apps.toolsym_tcm.tabs._base import BaseTab


class _PipelineWorker(QThread):
    """Runs steps 1–4 of the legacy pipeline + the hybrid classifier."""

    log = Signal(str)
    finished_ok = Signal(dict)
    failed = Signal(str)

    def __init__(
        self,
        data_root: Path,
        tool_id: str,
        config_overrides: dict,
        steps: list[int],
        run_classifier: bool,
        alpha: float,
        beta: float,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._data_root = data_root
        self._tool_id = tool_id
        self._config_overrides = config_overrides
        self._steps = steps
        self._run_classifier = run_classifier
        self._alpha = alpha
        self._beta = beta

    def run(self) -> None:  # noqa: PLR0912 — pipeline flow is linear, branchy by step
        try:
            layout = DatasetLayout(data_root=self._data_root, tool_id=self._tool_id)
            config = build_legacy_config(layout, **self._config_overrides)
            self.log.emit(f"Using DATA_ROOT={self._data_root}, TOOL_ID={self._tool_id}")
            self.log.emit(f"Backend: {config['OPTIMIZATION_METHOD']}")

            if 1 in self._steps:
                self.log.emit("─── Step 1: Blur and Rename ───")
                from toolsym.pipeline import step1_blur_and_rename

                step1_blur_and_rename.run(config)
            if 2 in self._steps:
                self.log.emit("─── Step 2: Generate Masks ───")
                from toolsym.pipeline import step2_generate_masks

                step2_generate_masks.run(config)
            if 3 in self._steps:
                self.log.emit("─── Step 3: Raw ROI analysis + plot ───")
                from toolsym.pipeline import step3_analyze_and_plot

                step3_analyze_and_plot.run(config)
            if 4 in self._steps:
                self.log.emit("─── Step 4: Processed analysis + plot ───")
                from toolsym.pipeline import step4_process_and_plot

                step4_process_and_plot.run(config)

            verdict: dict[str, object] = {"tool_id": self._tool_id}

            if self._run_classifier:
                self.log.emit("─── Hybrid classifier (Falah 2025) ───")
                verdict.update(self._classify(layout))

            self.finished_ok.emit(verdict)
        except Exception as exc:  # noqa: BLE001 — surface anything to the UI
            import traceback

            tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            self.failed.emit(tb)

    def _classify(self, layout: DatasetLayout) -> dict[str, object]:
        import numpy as np
        import pandas as pd

        from toolsym.signal import (
            classify_segment_consistency,
            classify_sinusoidal_distances,
            find_segments,
            fit_segment_sinusoidals,
            pairwise_coefficient_distances,
            preprocess_signal,
        )

        csv_path = layout.roi_csv
        if not csv_path.is_file():
            self.log.emit(f"  ! Raw CSV not found at {csv_path} — run Step 3 first.")
            return {"decision": "unavailable"}
        df = pd.read_csv(csv_path)
        angles = df.iloc[:, 0].to_numpy()
        values = df.iloc[:, 1].to_numpy()
        signal, _ = preprocess_signal(values, angles)
        segs = find_segments(signal)
        consistency = classify_segment_consistency(segs.segment_sizes_deg)
        self.log.emit(
            f"  segments: {segs.n_segments}, max size deviation "
            f"{consistency.max_deviation_pct:.2f}%"
        )
        if not consistency.intact:
            return {
                "decision": "fractured",
                "stage": "segment_size",
                "max_deviation_pct": consistency.max_deviation_pct,
                "n_segments": segs.n_segments,
            }
        if segs.n_segments < 3:
            return {
                "decision": "ambiguous",
                "stage": "segment_size",
                "note": "fewer than 3 segments → use the Symmetry tab",
                "n_segments": segs.n_segments,
            }
        fits = fit_segment_sinusoidals(signal, None, segs.n_segments)
        dists = pairwise_coefficient_distances(fits)
        decision = classify_sinusoidal_distances(dists, alpha=self._alpha, beta=self._beta)
        self.log.emit(
            f"  sinusoidal: min={decision.min_distance:.3f}, max={decision.max_distance:.3f}, "
            f"threshold={decision.threshold:.3f}"
        )
        return {
            "decision": "intact" if decision.intact else "fractured",
            "stage": "sinusoidal",
            "min_distance": decision.min_distance,
            "max_distance": decision.max_distance,
            "threshold": decision.threshold,
            "n_segments": segs.n_segments,
        }


class ImageToSignalTab(BaseTab):
    title = "Image to Signal"

    def build(self) -> None:
        layout: QVBoxLayout = self._layout  # type: ignore[assignment]

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_left())
        splitter.addWidget(self._build_right())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([460, 820])
        layout.addWidget(splitter)

        self._worker: _PipelineWorker | None = None
        self._refresh_tools()

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------
    def _build_left(self) -> QWidget:
        wrapper = QWidget()
        outer = QVBoxLayout(wrapper)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        col = QVBoxLayout(content)

        # Tool
        tool_group = QGroupBox("Tool")
        f = QFormLayout(tool_group)
        tool_row = QHBoxLayout()
        self._tool_combo = QComboBox()
        self._tool_combo.setMinimumWidth(180)
        refresh = QPushButton("⟲")
        refresh.setFixedWidth(28)
        refresh.setToolTip("Re-scan DATA root for tools")
        refresh.clicked.connect(self._refresh_tools)
        tool_row.addWidget(self._tool_combo, 1)
        tool_row.addWidget(refresh)
        f.addRow("Tool ID", tool_row)
        self._tool_summary = QLabel("(no tool selected)")
        self._tool_summary.setWordWrap(True)
        f.addRow("Details", self._tool_summary)
        self._tool_combo.currentIndexChanged.connect(self._on_tool_changed)
        col.addWidget(tool_group)

        # Backend
        be_group = QGroupBox("Processing backend")
        f = QFormLayout(be_group)
        self._backend = QComboBox()
        self._backend.addItems(["gpu", "multicore", "single"])
        f.addRow("Method", self._backend)
        col.addWidget(be_group)

        # Image processing
        ip_group = QGroupBox("Image processing")
        f = QFormLayout(ip_group)
        self._blur_kernel = self._spin(1, 99, 13, step=2)
        f.addRow("Blur kernel", self._blur_kernel)
        self._closing_kernel = self._spin(1, 99, 21, step=2)
        f.addRow("Closing kernel", self._closing_kernel)
        col.addWidget(ip_group)

        # Background subtraction
        bg_group = QGroupBox("Background subtraction")
        f = QFormLayout(bg_group)
        self._bg_method = QComboBox()
        self._bg_method.addItems(["lab", "absdiff", "none"])
        f.addRow("Method", self._bg_method)
        self._diff_threshold = self._spin(0, 255, 33)
        f.addRow("Difference threshold", self._diff_threshold)
        self._apply_mc = QCheckBox("Apply multi-channel mask")
        f.addRow("", self._apply_mc)
        col.addWidget(bg_group)

        # LAB / HSV thresholds (compact)
        th_group = QGroupBox("LAB / HSV thresholds (advanced)")
        f = QFormLayout(th_group)
        self._L_min = self._dspin(0, 255, 50 * 2.55)
        self._L_max = self._dspin(0, 255, 56 * 2.55)
        f.addRow("L min / max", self._pair(self._L_min, self._L_max))
        self._a_min = self._dspin(0, 255, -10 + 128)
        self._a_max = self._dspin(0, 255, -1 + 128)
        f.addRow("a min / max", self._pair(self._a_min, self._a_max))
        self._b_min = self._dspin(0, 255, -10 + 128)
        self._b_max = self._dspin(0, 255, -8 + 128)
        f.addRow("b min / max", self._pair(self._b_min, self._b_max))
        self._V_min = self._dspin(0, 255, 45 * 2.55)
        self._V_max = self._dspin(0, 255, 55 * 2.55)
        f.addRow("V min / max", self._pair(self._V_min, self._V_max))
        col.addWidget(th_group)

        # Analysis
        an_group = QGroupBox("Analysis parameters")
        f = QFormLayout(an_group)
        self._roi_height = self._spin(0, 5000, 200)
        f.addRow("ROI height (px)", self._roi_height)
        self._n_peaks = self._spin(1, 12, 2)
        f.addRow("NUMBER_OF_PEAKS", self._n_peaks)
        self._moving_avg = QCheckBox("Apply circular moving average")
        self._moving_avg.setChecked(True)
        f.addRow("", self._moving_avg)
        self._mavg_window = self._spin(1, 51, 5)
        f.addRow("Moving avg window", self._mavg_window)
        self._outlier = self._dspin(0.0, 1.0, 0.8, decimals=3, step=0.01)
        f.addRow("White-ratio outlier threshold", self._outlier)
        self._is_synthetic = QCheckBox("Treat as synthetic dataset")
        f.addRow("", self._is_synthetic)
        col.addWidget(an_group)

        # Pipeline steps
        steps_group = QGroupBox("Run pipeline steps")
        v = QVBoxLayout(steps_group)
        self._step1 = QCheckBox("Step 1 — Blur and rename")
        self._step2 = QCheckBox("Step 2 — Generate masks")
        self._step3 = QCheckBox("Step 3 — Raw ROI analysis + plot")
        self._step3.setChecked(True)
        self._step4 = QCheckBox("Step 4 — Processed analysis + plot")
        self._step4.setChecked(True)
        for w in (self._step1, self._step2, self._step3, self._step4):
            v.addWidget(w)
        col.addWidget(steps_group)

        # Hybrid classifier
        cls_group = QGroupBox("Hybrid classifier (Falah 2025)")
        f = QFormLayout(cls_group)
        self._run_cls = QCheckBox("Run classifier after Step 3/4")
        self._run_cls.setChecked(True)
        f.addRow("", self._run_cls)
        self._alpha = self._dspin(0.0, 100.0, 1.1, decimals=3)
        f.addRow("α (slope)", self._alpha)
        self._beta = self._dspin(0.0, 1000.0, 10.0, decimals=3)
        f.addRow("β (offset)", self._beta)
        col.addWidget(cls_group)

        # Run / Stop
        self._run_btn = QPushButton("▶ Run")
        self._run_btn.clicked.connect(self._on_run)
        col.addWidget(self._run_btn)
        col.addStretch(1)

        scroll.setWidget(content)
        outer.addWidget(scroll)
        return wrapper

    def _build_right(self) -> QWidget:
        wrapper = QWidget()
        v = QVBoxLayout(wrapper)
        self._verdict = QLabel("(no result yet)")
        self._verdict.setStyleSheet("font-size: 14pt; font-weight: 700;")
        v.addWidget(self._verdict)

        # Action buttons under the verdict
        actions = QHBoxLayout()
        self._open_raw = QPushButton("Open raw plot")
        self._open_raw.clicked.connect(lambda: self._open(self._current_layout().roi_plot))
        actions.addWidget(self._open_raw)
        self._open_processed = QPushButton("Open processed plot")
        self._open_processed.clicked.connect(
            lambda: self._open(self._current_layout().processed_plot)
        )
        actions.addWidget(self._open_processed)
        self._open_csv = QPushButton("Open CSV folder")
        self._open_csv.clicked.connect(
            lambda: self._open(self._current_layout().roi_csv.parent)
        )
        actions.addWidget(self._open_csv)
        actions.addStretch(1)
        v.addLayout(actions)

        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumBlockCount(8000)
        self._log.setStyleSheet(
            "QPlainTextEdit { background: #000; color: #d0d0d0; font-family: Consolas, monospace; font-size: 10pt; }"
        )
        v.addWidget(self._log, 1)
        return wrapper

    # ------------------------------------------------------------------
    @staticmethod
    def _spin(lo: int, hi: int, val: int, step: int = 1) -> QSpinBox:
        s = QSpinBox()
        s.setRange(lo, hi)
        s.setSingleStep(step)
        s.setValue(val)
        return s

    @staticmethod
    def _dspin(lo: float, hi: float, val: float, *, decimals: int = 2, step: float = 1.0) -> QDoubleSpinBox:
        s = QDoubleSpinBox()
        s.setRange(lo, hi)
        s.setDecimals(decimals)
        s.setSingleStep(step)
        s.setValue(val)
        return s

    @staticmethod
    def _pair(a: QWidget, b: QWidget) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(a)
        h.addWidget(b)
        return w

    # ------------------------------------------------------------------
    def _refresh_tools(self) -> None:
        prev = self._tool_combo.currentData() if self._tool_combo.count() else None
        self._tool_combo.blockSignals(True)
        self._tool_combo.clear()
        for rec in iter_tools(self.data_root(), only_with_masks=False):
            label = f"{rec.tool_id}"
            if rec.n_edges is not None:
                label += f"  ({rec.n_edges}e, {rec.condition or '?'})"
            self._tool_combo.addItem(label, userData=rec.tool_id)
        if self._tool_combo.count() == 0:
            self._tool_combo.addItem("(no tools found — check DATA root)", userData=None)
        self._tool_combo.blockSignals(False)
        if prev is not None:
            idx = self._tool_combo.findData(prev)
            if idx >= 0:
                self._tool_combo.setCurrentIndex(idx)
        self._on_tool_changed()

    def _on_tool_changed(self) -> None:
        tool_id = self._tool_combo.currentData()
        if not tool_id:
            self._tool_summary.setText("(no tool selected)")
            return
        recs = {r.tool_id: r for r in iter_tools(self.data_root(), only_with_masks=False)}
        rec = recs.get(tool_id)
        if rec is None:
            self._tool_summary.setText("(missing metadata)")
            return
        bits = []
        for key in ("type", "diameter_mm", "edges", "condition", "material", "coating", "color"):
            v = rec.metadata.get(key)
            if v:
                bits.append(f"{key}={v}")
        self._tool_summary.setText("  ".join(bits) or "(no metadata)")

    def _current_layout(self) -> DatasetLayout:
        return DatasetLayout(self.data_root(), self._tool_combo.currentData() or "")

    def on_data_root_changed(self, path: Path) -> None:
        self._refresh_tools()

    # ------------------------------------------------------------------
    def _on_run(self) -> None:
        tool_id = self._tool_combo.currentData()
        if not tool_id:
            QMessageBox.warning(self, "No tool", "Pick a tool first (check your DATA root).")
            return
        steps = [s for s, w in [(1, self._step1), (2, self._step2), (3, self._step3), (4, self._step4)] if w.isChecked()]
        if not steps and not self._run_cls.isChecked():
            QMessageBox.warning(self, "Nothing to do", "Tick at least one step or the classifier.")
            return
        config_overrides = {
            "optimization_method": self._backend.currentText(),
            "blur_kernel": self._blur_kernel.value(),
            "closing_kernel": self._closing_kernel.value(),
            "roi_height": self._roi_height.value(),
            "number_of_peaks": self._n_peaks.value(),
            "apply_moving_average": self._moving_avg.isChecked(),
            "moving_average_window": self._mavg_window.value(),
            "white_ratio_outlier_threshold": self._outlier.value(),
            "background_subtraction_method": self._bg_method.currentText(),
            "difference_threshold": self._diff_threshold.value(),
            "apply_multichannel_mask": self._apply_mc.isChecked(),
            "is_synthetic": self._is_synthetic.isChecked(),
            "extra": {
                "L_threshold_min": self._L_min.value(),
                "L_threshold_max": self._L_max.value(),
                "a_threshold_min": self._a_min.value(),
                "a_threshold_max": self._a_max.value(),
                "b_threshold_min": self._b_min.value(),
                "b_threshold_max": self._b_max.value(),
                "V_threshold_min": self._V_min.value(),
                "V_threshold_max": self._V_max.value(),
            },
        }
        self._log.clear()
        self._verdict.setText("Running…")
        self._verdict.setStyleSheet("color: #d0a050; font-size: 14pt; font-weight: 700;")
        self._run_btn.setEnabled(False)
        self._worker = _PipelineWorker(
            data_root=self.data_root(),
            tool_id=tool_id,
            config_overrides=config_overrides,
            steps=steps,
            run_classifier=self._run_cls.isChecked(),
            alpha=self._alpha.value(),
            beta=self._beta.value(),
            parent=self,
        )
        self._worker.log.connect(self._log.appendPlainText)
        self._worker.finished_ok.connect(self._on_done)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(lambda: self._run_btn.setEnabled(True))
        self._worker.start()

    def _on_done(self, verdict: dict) -> None:
        decision = verdict.get("decision", "?")
        if decision == "intact":
            colour = "#50c070"
            text = f"✓ INTACT  ({verdict.get('stage')})"
        elif decision == "fractured":
            colour = "#d05050"
            text = f"✗ FRACTURED  ({verdict.get('stage')})"
        elif decision == "ambiguous":
            colour = "#d0a050"
            text = f"⚠ AMBIGUOUS — {verdict.get('note')}"
        elif decision == "unavailable":
            colour = "#888888"
            text = "(classifier skipped — no Raw CSV available; run Step 3)"
        else:
            colour = "#888888"
            text = "Done"
        self._verdict.setText(text)
        self._verdict.setStyleSheet(f"color: {colour}; font-size: 14pt; font-weight: 700;")
        self._log.appendPlainText("DONE")

    def _on_failed(self, traceback_text: str) -> None:
        self._verdict.setText("✗ Error — see log")
        self._verdict.setStyleSheet("color: #d05050; font-size: 12pt; font-weight: 700;")
        self._log.appendPlainText("ERROR:\n" + traceback_text)

    @staticmethod
    def _open(path: Path) -> None:
        if not path.exists():
            return
        import os

        if hasattr(os, "startfile"):
            os.startfile(str(path))  # type: ignore[attr-defined]
        else:
            import subprocess

            opener = "open" if hasattr(subprocess, "_mswindows") else "xdg-open"
            subprocess.Popen([opener, str(path)])
