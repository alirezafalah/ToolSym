"""Noise tab — temporal cosine dent injection.

Skeleton; full port lands in v0.2. Algorithms already live in
:mod:`toolsym.simulation.noise_injector` and the presets in
:mod:`toolsym.simulation.presets`.
"""

from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QFormLayout, QGroupBox, QLabel, QVBoxLayout

from toolsym.simulation.presets import NOISE_PRESETS

from apps.toolsym_sim.tabs._base import BaseTab


class NoiseTab(BaseTab):
    title = "Noise"

    def build(self) -> None:
        layout: QVBoxLayout = self._layout  # type: ignore[assignment]

        group = QGroupBox("Preset")
        form = QFormLayout(group)
        self._preset = QComboBox()
        for name in NOISE_PRESETS:
            self._preset.addItem(name)
        form.addRow("Noise preset", self._preset)
        layout.addWidget(group)

        layout.addWidget(
            QLabel(
                "Full UI port deferred to v0.2 — use the legacy simulation_gui.py "
                "or the toolsym.simulation.noise_injector CLI in the meantime."
            )
        )
