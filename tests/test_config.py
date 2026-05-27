"""Tests for ``toolsym.config``."""

from __future__ import annotations

from pathlib import Path

import pytest

from toolsym.config import (
    CameraIntrinsics,
    bundled_voxel_grid_spec_path,
    data_root,
    load_intrinsics,
    load_voxel_grid_spec,
)


def test_data_root_uses_override(tmp_path: Path) -> None:
    out = data_root(tmp_path / "data")
    assert out == (tmp_path / "data").resolve()
    assert out.is_dir()


def test_data_root_uses_env_var(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("TOOLSYM_DATA", str(tmp_path / "fromenv"))
    out = data_root()
    assert out == (tmp_path / "fromenv").resolve()
    assert out.is_dir()


def test_bundled_spec_loads() -> None:
    spec = load_voxel_grid_spec()
    assert spec.grid_shape == (128, 128, 128)
    assert len(spec.volume_bounds_mm) == 3
    # 20 mm span / 128 voxels ≈ 0.156 mm
    assert spec.voxel_size_mm == pytest.approx(0.15625, rel=1e-3)


def test_camera_intrinsics_geometry() -> None:
    cam = CameraIntrinsics()
    # visible_width = 6.4 * 250 / 75 ≈ 21.33 mm
    assert cam.visible_width_mm == pytest.approx(21.3333, rel=1e-3)
    assert cam.visible_height_mm == pytest.approx(16.0, rel=1e-3)
    assert cam.mm_per_pixel_x > 0


def test_load_intrinsics_from_bundled_spec() -> None:
    cam = load_intrinsics(bundled_voxel_grid_spec_path())
    assert cam.focal_length_mm == pytest.approx(75.0)
    assert cam.working_distance_mm == pytest.approx(250.0)


def test_load_intrinsics_none_returns_defaults() -> None:
    assert load_intrinsics(None) == CameraIntrinsics()
