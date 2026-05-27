"""Axial-misalignment estimation and rectification (symmetry paper §2.2).

If the camera's optical axis isn't perfectly perpendicular to the
spindle, the projected tool silhouette will appear *tilted* in the
frames. The fix is purely geometric:

1. Build the master mask (bounding cylinder).
2. For each row of the master mask, take the leftmost and rightmost
   foreground pixels.
3. Linear-regress each of those two columns of (row, x) points → a left
   edge line and a right edge line.
4. The bisector of those two lines is the tool's true axis. Its angle
   off vertical is the tilt; rotating every frame by ``-tilt`` rectifies
   the dataset. The bisector itself, after rotation, is the centerline
   used by :func:`toolsym.geometry.roi.split_left_right`.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

__all__ = ["TiltCenterline", "estimate_tilt_and_centerline", "rotate_to_axis"]


@dataclass(frozen=True, slots=True)
class TiltCenterline:
    """Result of :func:`estimate_tilt_and_centerline`.

    Attributes
    ----------
    tilt_deg
        Signed angle of the tool axis from vertical, in degrees.
        Positive = leaning right at the top.
    left_slope, left_intercept
        Linear fit ``x = slope · y + intercept`` for the left edge.
    right_slope, right_intercept
        Same for the right edge.
    centerline_x_top, centerline_x_bottom
        The bisector's X position at ``y = 0`` and ``y = H-1``, before
        any rectification.
    """

    tilt_deg: float
    left_slope: float
    left_intercept: float
    right_slope: float
    right_intercept: float
    centerline_x_top: float
    centerline_x_bottom: float


def estimate_tilt_and_centerline(
    master_mask: np.ndarray, *, top_skip_frac: float = 0.05, bottom_skip_frac: float = 0.15
) -> TiltCenterline:
    """Recover tilt + centerline from a master mask.

    Parameters
    ----------
    master_mask
        ``(H, W)`` foreground mask (``> 0`` = tool).
    top_skip_frac, bottom_skip_frac
        Fractions of the image height to ignore at the top (shank area)
        and bottom (tip — variable due to flutes) before fitting. The
        midsection of the bounding cylinder is the most reliable.

    Returns
    -------
    TiltCenterline

    Raises
    ------
    ValueError
        If the master mask has no foreground rows.
    """
    if master_mask.ndim != 2:
        raise ValueError(f"expected 2-D mask, got {master_mask.shape}")
    h, w = master_mask.shape
    foreground = master_mask > 0
    cols_per_row = foreground.any(axis=1)
    rows_with_tool = np.where(cols_per_row)[0]
    if rows_with_tool.size == 0:
        raise ValueError("master mask is empty")

    y_min = int(rows_with_tool.min() + top_skip_frac * h)
    y_max = int(rows_with_tool.max() - bottom_skip_frac * h)
    if y_max <= y_min + 10:
        # Tool span is tiny; fall back to using all rows-with-tool.
        y_min = int(rows_with_tool.min())
        y_max = int(rows_with_tool.max())

    rows = np.arange(y_min, y_max + 1)
    left_x = np.full(rows.size, np.nan, dtype=np.float64)
    right_x = np.full(rows.size, np.nan, dtype=np.float64)
    for i, y in enumerate(rows):
        xs = np.where(foreground[y])[0]
        if xs.size:
            left_x[i] = xs[0]
            right_x[i] = xs[-1]
    mask_ok = ~(np.isnan(left_x) | np.isnan(right_x))
    rows = rows[mask_ok]
    left_x = left_x[mask_ok]
    right_x = right_x[mask_ok]

    if rows.size < 2:
        raise ValueError("not enough rows to regress edges")

    # x = slope · y + intercept (regress x on y so vertical edges are well-conditioned)
    ls, li = np.polyfit(rows, left_x, 1)
    rs, ri = np.polyfit(rows, right_x, 1)

    # Bisector slope is the mean (in tan-space these are small angles, so OK)
    center_slope = (ls + rs) / 2.0
    center_intercept = (li + ri) / 2.0
    center_top = center_intercept + center_slope * 0.0
    center_bottom = center_intercept + center_slope * (h - 1)
    tilt_rad = np.arctan(center_slope)
    tilt_deg = float(np.rad2deg(tilt_rad))

    return TiltCenterline(
        tilt_deg=tilt_deg,
        left_slope=float(ls),
        left_intercept=float(li),
        right_slope=float(rs),
        right_intercept=float(ri),
        centerline_x_top=float(center_top),
        centerline_x_bottom=float(center_bottom),
    )


def rotate_to_axis(mask: np.ndarray, tilt_deg: float) -> np.ndarray:
    """Rotate ``mask`` by ``-tilt_deg`` about its centre to undo tilt.

    Uses nearest-neighbour interpolation so binary masks stay binary.
    """
    if mask.ndim != 2:
        raise ValueError(f"expected 2-D mask, got {mask.shape}")
    h, w = mask.shape
    center = (w / 2.0, h / 2.0)
    matrix = cv2.getRotationMatrix2D(center, tilt_deg, 1.0)
    return cv2.warpAffine(
        mask,
        matrix,
        (w, h),
        flags=cv2.INTER_NEAREST,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )
