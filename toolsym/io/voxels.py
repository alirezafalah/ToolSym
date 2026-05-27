"""Voxel grid IO: NPZ persistence + OBJ export via marching cubes.

The NPZ format matches the schema in ``voxel_grid_spec.json``: three
arrays per file — ``voxel_grid`` (the boolean occupancy grid),
``volume_bounds`` (``(3, 2)`` float32), and ``grid_shape`` (``(3,)`` int32).
This keeps the file self-describing so loaders never need a paired JSON.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

__all__ = ["load_voxel_grid", "save_voxel_grid", "voxel_grid_to_obj"]


def save_voxel_grid(
    voxel_grid: np.ndarray,
    volume_bounds: tuple[tuple[float, float], ...],
    grid_shape: tuple[int, int, int],
    path: str | Path,
) -> None:
    """Write a voxel grid + its bounds + its shape into one NPZ."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out,
        voxel_grid=voxel_grid.astype(bool),
        volume_bounds=np.asarray(volume_bounds, dtype=np.float32),
        grid_shape=np.asarray(grid_shape, dtype=np.int32),
    )


def load_voxel_grid(
    path: str | Path,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load ``(voxel_grid, volume_bounds, grid_shape)`` from an NPZ."""
    data = np.load(Path(path))
    return data["voxel_grid"], data["volume_bounds"], data["grid_shape"]


def voxel_grid_to_obj(
    voxel_grid: np.ndarray,
    volume_bounds: tuple[tuple[float, float], ...],
    path: str | Path,
    *,
    iso: float = 0.5,
) -> None:
    """Export a boolean voxel grid as a Wavefront OBJ via marching cubes.

    Uses :mod:`skimage.measure.marching_cubes` when scikit-image is
    available, otherwise falls back to PyVista. Both produce equivalent
    isosurfaces for the ``{0, 1}`` field.
    """
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    arr = voxel_grid.astype(np.float32)
    span = np.array(
        [b[1] - b[0] for b in volume_bounds], dtype=np.float32
    )
    spacing = tuple(float(s) for s in span / np.asarray(voxel_grid.shape))
    origin = tuple(float(b[0]) for b in volume_bounds)

    try:
        from skimage.measure import marching_cubes  # type: ignore[import-not-found]

        verts, faces, _, _ = marching_cubes(arr, level=iso, spacing=spacing)
        verts = verts + np.asarray(origin)
        _write_obj(out, verts, faces)
        return
    except ImportError:
        pass

    try:
        import pyvista as pv  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "Either scikit-image or pyvista is required for OBJ export"
        ) from exc

    grid = pv.ImageData(
        dimensions=tuple(d + 1 for d in voxel_grid.shape),
        spacing=spacing,
        origin=origin,
    )
    grid.cell_data["v"] = arr.ravel(order="F")
    surface = grid.cells_to_points("v").contour([iso], scalars="v")
    surface.save(str(out))


def _write_obj(path: Path, verts: np.ndarray, faces: np.ndarray) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for v in verts:
            fh.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
        for f in faces + 1:  # OBJ is 1-indexed
            fh.write(f"f {int(f[0])} {int(f[1])} {int(f[2])}\n")
