"""Render tab — CAD → 360 binary masks.

This is a thin skeleton that points at the existing
:mod:`toolsym.simulation.render_engine` module. The full UI port from
``CNC-Tool-CAD-to-Mask-Simulation/simulation_gui.py`` (with the live
camera preview and the realistic-shading toggle) lands in v0.2.
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

from apps.toolsym_sim.tabs._base import BaseTab


class RenderTab(BaseTab):
    title = "Render"

    def build(self) -> None:
        layout: QVBoxLayout = self._layout  # type: ignore[assignment]

        inputs = QGroupBox("Inputs")
        form = QFormLayout(inputs)

        cad_row = QHBoxLayout()
        self._cad = QLineEdit()
        self._cad.setPlaceholderText("Pick a CAD (STEP/STL) file…")
        browse_cad = QPushButton("Browse…")
        browse_cad.clicked.connect(self._on_browse_cad)
        cad_row.addWidget(self._cad, 1)
        cad_row.addWidget(browse_cad)
        form.addRow("CAD model", cad_row)

        out_row = QHBoxLayout()
        self._out = QLineEdit()
        self._out.setPlaceholderText("Output folder for masks…")
        browse_out = QPushButton("Browse…")
        browse_out.clicked.connect(self._on_browse_out)
        out_row.addWidget(self._out, 1)
        out_row.addWidget(browse_out)
        form.addRow("Output", out_row)

        self._n_frames = QSpinBox()
        self._n_frames.setRange(8, 3600)
        self._n_frames.setValue(360)
        form.addRow("Frames", self._n_frames)

        layout.addWidget(inputs)

        run = QPushButton("Render 360°")
        run.clicked.connect(self._on_run)
        layout.addWidget(run, alignment=Qt.AlignmentFlag.AlignLeft)

        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setStyleSheet(
            "QPlainTextEdit { background: #000; color: #d0d0d0; font-family: Consolas, monospace; }"
        )
        layout.addWidget(self._log, 1)

    def _on_browse_cad(self) -> None:
        f, _ = QFileDialog.getOpenFileName(
            self,
            "Pick a CAD model",
            str(self.data_root()),
            "CAD files (*.step *.stp *.STEP *.STP *.stl *.STL)",
        )
        if f:
            self._cad.setText(f)

    def _on_browse_out(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Output folder", str(self.data_root()))
        if d:
            self._out.setText(d)

    def _on_run(self) -> None:
        cad = Path(self._cad.text().strip())
        out = Path(self._out.text().strip())
        if not cad.is_file():
            self._log.appendPlainText("Pick a valid CAD file first")
            return
        if not out:
            self._log.appendPlainText("Pick an output folder first")
            return
        self._log.appendPlainText(
            f"TODO: invoke toolsym.simulation.render_engine on {cad.name} → {out}\n"
            "(Wiring deferred to v0.2; the legacy simulation_gui.py still works.)"
        )
