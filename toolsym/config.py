"""Centralised configuration: DATA root, camera intrinsics, voxel-grid spec.

The legacy code in `Tool_Condition_Monitoring` and
`CNC-Tool-CAD-to-Mask-Simulation` hardcoded paths like
``C:\\Users\\uik07077\\...`` and assumed sibling directory layouts
(``../Tool_Condition_Monitoring/3D_reconstruction/voxel_grid_spec.json``).
This module replaces all of that with a single resolution chain so the
library works on any machine without source edits.

Resolution chain for the DATA folder
------------------------------------
1. Explicit argument to :func:`data_root` (highest precedence).
2. The ``TOOLSYM_DATA`` environment variable.
3. ``~/.toolsym/data`` (created on first call).

GUI applications additionally honour a user-set value through ``QSettings``
(persisted under ``~/.toolsym/settings.ini``); the GUI passes that value
into :func:`data_root` explicitly so this module never imports Qt.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from functools import lru_cache
from importlib.resources import files
from pathlib import Path
from typing import Any

__all__ = [
    "CameraIntrinsics",
    "VoxelGridSpec",
    "bundled_voxel_grid_spec_path",
    "data_root",
    "load_intrinsics",
    "load_voxel_grid_spec",
    "settings_dir",
]

# ---------------------------------------------------------------------------
# DATA root
# ---------------------------------------------------------------------------

ENV_VAR = "TOOLSYM_DATA"
"""Environment variable that overrides the default DATA root."""

_DEFAULT_DATA_ROOT = Path.home() / ".toolsym" / "data"
_SETTINGS_DIR = Path.home() / ".toolsym"


def data_root(override: str | Path | None = None) -> Path:
    """Resolve the DATA root directory.

    Parameters
    ----------
    override
        If provided, used directly (after expansion). This lets the GUIs
        pass a user-configured path without touching environment variables.

    Returns
    -------
    Path
        The resolved DATA root. The directory is created if missing.
    """
    if override is not None:
        path = Path(override).expanduser().resolve()
    elif env := os.environ.get(ENV_VAR):
        path = Path(env).expanduser().resolve()
    else:
        path = _DEFAULT_DATA_ROOT
    path.mkdir(parents=True, exist_ok=True)
    return path


def settings_dir() -> Path:
    """Return ``~/.toolsym/`` (the per-user settings directory)."""
    _SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    return _SETTINGS_DIR


# ---------------------------------------------------------------------------
# Camera intrinsics
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CameraIntrinsics:
    """Physical camera parameters used by the renderer and voxel spec.

    Defaults match the rig described in Falah et al. (2025): a Basler
    a2A2600 with a VS-LDV75 lens at 250 mm working distance.

    Attributes
    ----------
    focal_length_mm
        Lens focal length.
    sensor_width_mm, sensor_height_mm
        Physical sensor dimensions.
    working_distance_mm
        Distance from lens to object plane.
    image_width_px, image_height_px
        Capture resolution. Defaults match the renderer's 4:3 output.
    """

    focal_length_mm: float = 75.0
    sensor_width_mm: float = 6.4
    sensor_height_mm: float = 4.8
    working_distance_mm: float = 250.0
    image_width_px: int = 2600
    image_height_px: int = 2128

    @property
    def visible_width_mm(self) -> float:
        """Field of view width at the working distance."""
        return self.sensor_width_mm * self.working_distance_mm / self.focal_length_mm

    @property
    def visible_height_mm(self) -> float:
        """Field of view height at the working distance."""
        return self.sensor_height_mm * self.working_distance_mm / self.focal_length_mm

    @property
    def mm_per_pixel_x(self) -> float:
        return self.visible_width_mm / self.image_width_px

    @property
    def mm_per_pixel_y(self) -> float:
        return self.visible_height_mm / self.image_height_px

    def to_dict(self) -> dict[str, Any]:
        return {
            "focal_length_mm": self.focal_length_mm,
            "sensor_width_mm": self.sensor_width_mm,
            "sensor_height_mm": self.sensor_height_mm,
            "working_distance_mm": self.working_distance_mm,
            "image_width_px": self.image_width_px,
            "image_height_px": self.image_height_px,
            "visible_width_mm": self.visible_width_mm,
            "visible_height_mm": self.visible_height_mm,
        }


def load_intrinsics(spec_path: str | Path | None = None) -> CameraIntrinsics:
    """Load camera intrinsics from a voxel-grid spec JSON.

    Falls back to defaults if ``spec_path`` is ``None`` or the JSON does
    not include a ``camera_parameters`` block.
    """
    if spec_path is None:
        return CameraIntrinsics()
    raw = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    cam = raw.get("camera_parameters", {})
    return CameraIntrinsics(
        focal_length_mm=cam.get("focal_length_mm", CameraIntrinsics.focal_length_mm),
        sensor_width_mm=cam.get("sensor_width_mm", CameraIntrinsics.sensor_width_mm),
        sensor_height_mm=cam.get("sensor_height_mm", CameraIntrinsics.sensor_height_mm),
        working_distance_mm=cam.get(
            "working_distance_mm", CameraIntrinsics.working_distance_mm
        ),
        image_width_px=cam.get("image_width_px", CameraIntrinsics.image_width_px),
        image_height_px=cam.get("image_height_px", CameraIntrinsics.image_height_px),
    )


# ---------------------------------------------------------------------------
# Voxel-grid spec
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class VoxelGridSpec:
    """Shared voxel grid definition for the visual-hull carver and the
    CAD-to-voxel ground-truth voxelizer.

    Both the real-data carver in :mod:`toolsym.reconstruction.visual_hull`
    and the CAD voxelizer in :mod:`toolsym.reconstruction.cad_voxelizer`
    must agree on this so trained models transfer.
    """

    grid_shape: tuple[int, int, int] = (128, 128, 128)
    volume_bounds_mm: tuple[tuple[float, float], ...] = (
        (-10.0, 10.0),
        (-10.0, 10.0),
        (-10.0, 10.0),
    )
    voxel_dtype: str = "bool"
    camera: CameraIntrinsics = field(default_factory=CameraIntrinsics)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def voxel_size_mm(self) -> float:
        """Edge length of one voxel (assumes isotropic, cubic volume)."""
        span_mm = self.volume_bounds_mm[0][1] - self.volume_bounds_mm[0][0]
        return span_mm / self.grid_shape[0]


def bundled_voxel_grid_spec_path() -> Path:
    """Path to the spec JSON bundled inside the installed wheel."""
    return Path(str(files("toolsym").joinpath("data/voxel_grid_spec.json")))


@lru_cache(maxsize=4)
def load_voxel_grid_spec(spec_path: str | Path | None = None) -> VoxelGridSpec:
    """Load a voxel-grid spec from disk (or the bundled default).

    Parameters
    ----------
    spec_path
        Path to a ``voxel_grid_spec.json`` file. If ``None``, the spec
        bundled with the package is loaded.

    Returns
    -------
    VoxelGridSpec
        Parsed spec with attached camera intrinsics. Cached.
    """
    path = Path(spec_path) if spec_path else bundled_voxel_grid_spec_path()
    raw = json.loads(path.read_text(encoding="utf-8"))
    bounds = raw.get(
        "global_volume_bounds_mm",
        raw.get("volume_bounds_mm", [[-10.0, 10.0]] * 3),
    )
    return VoxelGridSpec(
        grid_shape=tuple(raw.get("grid_shape", [128, 128, 128])),  # type: ignore[arg-type]
        volume_bounds_mm=tuple(tuple(b) for b in bounds),  # type: ignore[misc]
        voxel_dtype=raw.get("voxel_dtype", "bool"),
        camera=load_intrinsics(path),
        raw=raw,
    )
