"""Voxelize tab — CAD → 128³ ground-truth voxel grid.

Skeleton; full port lands in v0.2.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout

from toolsym.config import load_voxel_grid_spec

from apps.toolsym_sim.tabs._base import BaseTab


class VoxelizeTab(BaseTab):
    title = "Voxelize"

    def build(self) -> None:
        layout: QVBoxLayout = self._layout  # type: ignore[assignment]

        spec = load_voxel_grid_spec()
        info = QLabel(
            f"Grid:       {spec.grid_shape}\n"
            f"Bounds (mm): {spec.volume_bounds_mm}\n"
            f"Voxel size:  {spec.voxel_size_mm:.4f} mm"
        )
        info.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        info.setStyleSheet("font-family: Consolas, monospace;")
        layout.addWidget(info)

        layout.addWidget(
            QLabel(
                "Full UI port deferred to v0.2 — use the legacy simulation_gui.py "
                "or the toolsym.reconstruction.cad_voxelizer CLI in the meantime."
            )
        )
