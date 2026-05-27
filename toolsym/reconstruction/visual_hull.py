"""Shape-from-Silhouette carver for real-world masks.

Implements the carver originally in
``Tool_Condition_Monitoring/3D_reconstruction/visual_hull_engine.py``
as a clean library function with two backends:

* CPU (NumPy) — always available, vectorised.
* OpenCL — opt-in via the ``[gpu]`` extras; ~10× faster on Intel Iris XE
  and discrete GPUs. Selected by passing ``backend="opencl"`` or
  ``backend="auto"`` (default; falls back to CPU when no GPU).

The grid layout follows ``voxel_grid_spec.json`` exactly so the output
is compatible with the simulation voxelizer and the deep shape prior.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Literal

import numpy as np

from toolsym.config import VoxelGridSpec, load_voxel_grid_spec

ProgressCallback = Callable[[float, str], None]
Backend = Literal["auto", "cpu", "opencl"]

__all__ = ["CarverConfig", "HullResult", "carve_visual_hull"]


@dataclass(frozen=True, slots=True)
class CarverConfig:
    """Knobs for the visual-hull carver.

    Attributes
    ----------
    grid_shape
        Voxel grid resolution. Default ``(128, 128, 128)`` matches the
        bundled spec.
    volume_bounds_mm
        Physical bounding cube. Default ±10 mm per axis.
    backend
        ``"cpu"``, ``"opencl"``, or ``"auto"`` (default).
    chunk_views
        How many views to carve per CPU loop iteration. Trade memory for
        speed: 36 fits in <1 GiB at 128³ and 360 views, 360 is single-shot.
    threshold
        Foreground binarisation cut-off applied per mask.
    """

    grid_shape: tuple[int, int, int] = (128, 128, 128)
    volume_bounds_mm: tuple[tuple[float, float], ...] = (
        (-10.0, 10.0),
        (-10.0, 10.0),
        (-10.0, 10.0),
    )
    backend: Backend = "auto"
    chunk_views: int = 36
    threshold: int = 127
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_spec(cls, spec: VoxelGridSpec | None = None, **overrides: object) -> CarverConfig:
        spec = spec or load_voxel_grid_spec()
        kwargs: dict = {
            "grid_shape": spec.grid_shape,
            "volume_bounds_mm": spec.volume_bounds_mm,
        }
        kwargs.update(overrides)
        return cls(**kwargs)  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True)
class HullResult:
    """Output of :func:`carve_visual_hull`."""

    voxel_grid: np.ndarray
    volume_bounds_mm: tuple[tuple[float, float], ...]
    grid_shape: tuple[int, int, int]
    n_views: int
    backend_used: str
    elapsed_seconds: float


def _voxel_centres(
    grid_shape: tuple[int, int, int],
    volume_bounds_mm: tuple[tuple[float, float], ...],
) -> np.ndarray:
    """Build a ``(N, 3)`` array of voxel-centre coordinates in mm."""
    axes = []
    for n, (lo, hi) in zip(grid_shape, volume_bounds_mm, strict=True):
        edges = np.linspace(lo, hi, n + 1, dtype=np.float32)
        centres = 0.5 * (edges[:-1] + edges[1:])
        axes.append(centres)
    xs, ys, zs = np.meshgrid(*axes, indexing="ij")
    return np.stack([xs.ravel(), ys.ravel(), zs.ravel()], axis=-1).astype(np.float32)


def _project_orthographic(
    points_mm: np.ndarray,
    angle_rad: float,
    mask_shape: tuple[int, int],
    mm_per_px_x: float,
    mm_per_px_y: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Project voxel centres to image pixel coordinates at ``angle_rad``.

    Rotation is about the Y axis (the spindle axis in our setup) — see
    the symmetry paper's coordinate definition.
    """
    cos_t = float(np.cos(angle_rad))
    sin_t = float(np.sin(angle_rad))
    # Rotate X-Z plane.
    x_rot = points_mm[:, 0] * cos_t - points_mm[:, 2] * sin_t
    y_rot = points_mm[:, 1]
    h, w = mask_shape
    u = x_rot / mm_per_px_x + w / 2.0
    v = h / 2.0 - y_rot / mm_per_px_y  # image origin at top-left
    return u, v


def _carve_cpu(
    masks: np.ndarray,
    config: CarverConfig,
    mm_per_px_x: float,
    mm_per_px_y: float,
    progress: ProgressCallback | None,
) -> np.ndarray:
    n_views = masks.shape[0]
    centres = _voxel_centres(config.grid_shape, config.volume_bounds_mm)
    occupancy = np.ones(centres.shape[0], dtype=bool)
    angle_step = 2.0 * np.pi / n_views
    h, w = masks.shape[1], masks.shape[2]
    binary = masks > config.threshold
    for i in range(n_views):
        u, v = _project_orthographic(
            centres, i * angle_step, (h, w), mm_per_px_x, mm_per_px_y
        )
        iu = np.rint(u).astype(np.int32)
        iv = np.rint(v).astype(np.int32)
        in_frame = (iu >= 0) & (iu < w) & (iv >= 0) & (iv < h)
        # A voxel is *retained* if it projects inside the mask in this view.
        # Voxels projecting outside the frame are conservatively kept (would
        # need that view's silhouette to confirm — common in tight FOVs).
        idx = np.where(in_frame & occupancy)[0]
        if idx.size:
            keep = binary[i, iv[idx], iu[idx]]
            occupancy[idx[~keep]] = False
        if progress is not None and (i % 12 == 0 or i == n_views - 1):
            progress((i + 1) / n_views, f"view {i + 1}/{n_views}")
    return occupancy.reshape(config.grid_shape)


def _carve_opencl(
    masks: np.ndarray,
    config: CarverConfig,
    mm_per_px_x: float,
    mm_per_px_y: float,
    progress: ProgressCallback | None,
) -> np.ndarray | None:
    try:
        import pyopencl as cl
        import pyopencl.array as cla
    except ImportError:
        return None

    kernel_src = """
    __kernel void carve(
        __global const float *points,    // (N, 3) flattened
        __global const uchar *mask,      // (H, W)
        __global uchar *occupancy,
        const float cos_t,
        const float sin_t,
        const int W,
        const int H,
        const float mm_per_px_x,
        const float mm_per_px_y,
        const uchar threshold
    ) {
        int gid = get_global_id(0);
        if (occupancy[gid] == 0) return;
        float x = points[gid * 3 + 0];
        float y = points[gid * 3 + 1];
        float z = points[gid * 3 + 2];
        float x_rot = x * cos_t - z * sin_t;
        float u = x_rot / mm_per_px_x + 0.5f * (float)W;
        float v = 0.5f * (float)H - y / mm_per_px_y;
        int iu = (int)round(u);
        int iv = (int)round(v);
        if (iu < 0 || iu >= W || iv < 0 || iv >= H) return;
        if (mask[iv * W + iu] <= threshold) {
            occupancy[gid] = 0;
        }
    }
    """
    try:
        ctx = cl.create_some_context(interactive=False)
        queue = cl.CommandQueue(ctx)
    except cl.Error:
        return None

    centres = _voxel_centres(config.grid_shape, config.volume_bounds_mm)
    n_views, h, w = masks.shape
    pts_dev = cla.to_device(queue, centres)
    occ_dev = cla.to_device(queue, np.ones(centres.shape[0], dtype=np.uint8))
    program = cl.Program(ctx, kernel_src).build()
    angle_step = 2.0 * np.pi / n_views

    for i in range(n_views):
        mask_dev = cla.to_device(queue, masks[i].astype(np.uint8))
        program.carve(
            queue,
            (centres.shape[0],),
            None,
            pts_dev.data,
            mask_dev.data,
            occ_dev.data,
            np.float32(np.cos(i * angle_step)),
            np.float32(np.sin(i * angle_step)),
            np.int32(w),
            np.int32(h),
            np.float32(mm_per_px_x),
            np.float32(mm_per_px_y),
            np.uint8(config.threshold),
        )
        if progress is not None and (i % 12 == 0 or i == n_views - 1):
            progress((i + 1) / n_views, f"OpenCL view {i + 1}/{n_views}")

    occ = occ_dev.get().astype(bool)
    return occ.reshape(config.grid_shape)


def carve_visual_hull(
    masks: np.ndarray,
    *,
    config: CarverConfig | None = None,
    mm_per_pixel: tuple[float, float] | None = None,
    progress: ProgressCallback | None = None,
) -> HullResult:
    """Carve the 128³ visual hull from a stack of binary silhouettes.

    Parameters
    ----------
    masks
        ``(N, H, W)`` ``uint8`` stack, one frame per equally-spaced
        rotation angle.
    config
        Grid + backend configuration. Defaults to the bundled spec.
    mm_per_pixel
        Image-plane pixel pitch ``(x, y)`` in mm. Default is derived
        from :class:`toolsym.config.CameraIntrinsics` defaults — the
        Falah rig.
    progress
        Optional callback ``(fraction, message)`` invoked from the carve
        loop. Use this to drive a GUI progress bar.
    """
    import time

    if masks.ndim != 3:
        raise ValueError(f"expected (N, H, W) stack, got {masks.shape}")
    cfg = config or CarverConfig.from_spec()
    if mm_per_pixel is None:
        cam = load_voxel_grid_spec().camera
        mm_per_pixel = (cam.mm_per_pixel_x, cam.mm_per_pixel_y)

    t0 = time.perf_counter()
    used = cfg.backend
    grid: np.ndarray | None = None
    if cfg.backend in ("auto", "opencl"):
        grid = _carve_opencl(masks, cfg, *mm_per_pixel, progress)
        if grid is not None:
            used = "opencl"
    if grid is None:
        grid = _carve_cpu(masks, cfg, *mm_per_pixel, progress)
        used = "cpu"
    elapsed = time.perf_counter() - t0

    return HullResult(
        voxel_grid=grid,
        volume_bounds_mm=cfg.volume_bounds_mm,
        grid_shape=cfg.grid_shape,
        n_views=int(masks.shape[0]),
        backend_used=used,
        elapsed_seconds=elapsed,
    )
