"""Augment tab — non-uniform CAD scaling.

Skeleton; full port lands in v0.2.
"""

from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QFormLayout, QGroupBox, QLabel, QVBoxLayout

from toolsym.simulation.presets import AUGMENT_PRESETS

from apps.toolsym_sim.tabs._base import BaseTab


class AugmentTab(BaseTab):
    title = "Augment"

    def build(self) -> None:
        layout: QVBoxLayout = self._layout  # type: ignore[assignment]

        group = QGroupBox("Preset")
        form = QFormLayout(group)
        self._preset = QComboBox()
        for key, val in AUGMENT_PRESETS.items():
            self._preset.addItem(f"{val['label']}  ({key})", userData=key)
        form.addRow("Augmentation preset", self._preset)
        layout.addWidget(group)

        layout.addWidget(
            QLabel(
                "Full UI port deferred to v0.2 — use the legacy simulation_gui.py "
                "or the toolsym.simulation.augmentor CLI in the meantime."
            )
        )
