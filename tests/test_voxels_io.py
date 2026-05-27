"""Tests for ``toolsym.io.voxels``."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from toolsym.io.voxels import load_voxel_grid, save_voxel_grid


def test_save_load_roundtrip(tmp_path: Path) -> None:
    grid = np.zeros((8, 8, 8), dtype=bool)
    grid[2:6, 2:6, 2:6] = True
    bounds = ((-10, 10), (-10, 10), (-10, 10))
    shape = (8, 8, 8)
    path = tmp_path / "v.npz"
    save_voxel_grid(grid, bounds, shape, path)
    g2, b2, s2 = load_voxel_grid(path)
    np.testing.assert_array_equal(g2, grid)
    np.testing.assert_array_equal(b2, np.asarray(bounds, dtype=np.float32))
    np.testing.assert_array_equal(s2, np.asarray(shape, dtype=np.int32))


def test_obj_export_skipped_when_optional_libs_missing(tmp_path: Path) -> None:
    """OBJ export depends on scikit-image or pyvista — fine to skip if neither installed."""
    pytest.importorskip(
        "skimage",
        reason="OBJ export uses scikit-image when present; pyvista is a fallback",
    )
    from toolsym.io.voxels import voxel_grid_to_obj

    grid = np.zeros((10, 10, 10), dtype=bool)
    grid[3:7, 3:7, 3:7] = True
    out = tmp_path / "v.obj"
    voxel_grid_to_obj(grid, ((-10, 10), (-10, 10), (-10, 10)), out)
    assert out.is_file()
    assert out.stat().st_size > 0
