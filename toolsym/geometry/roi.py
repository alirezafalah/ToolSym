"""Dynamic ROI extraction and left/right split (symmetry paper §2.3).

The paper bases the analysis on a ROI at the tool tip whose **height
scales with the tool's bounding-cylinder width** — ``H_ROI = 0.45 · W``.
This keeps the analysis focused on the primary cutting zone regardless
of tool diameter. The ROI is then split along the recovered centerline
into a left half and a right half; the symmetry metric runs on the
right half by default.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = ["RoiSplit", "dynamic_roi", "split_left_right"]


@dataclass(frozen=True, slots=True)
class RoiSplit:
    """A tip ROI split along the tool centerline."""

    full: np.ndarray
    left: np.ndarray
    right: np.ndarray
    roi_height: int
    centerline_x: int


def dynamic_roi(
    mask: np.ndarray,
    tool_width_px: int,
    *,
    roi_to_width_ratio: float = 0.45,
) -> tuple[np.ndarray, int]:
    """Crop the bottom portion of ``mask`` to a ROI of dynamic height.

    Parameters
    ----------
    mask
        ``(H, W)`` rectified mask.
    tool_width_px
        Tool bounding-cylinder width, in pixels (measure on the master
        mask, then reuse for every frame of that tool).
    roi_to_width_ratio
        ``0.45`` per the symmetry paper. Lower this if the tool is short.

    Returns
    -------
    roi : np.ndarray
        ``(H_ROI, W)`` slice from the bottom of the image.
    roi_height : int
        ``H_ROI`` actually used (clipped to image height).
    """
    if mask.ndim != 2:
        raise ValueError(f"expected 2-D mask, got {mask.shape}")
    h = mask.shape[0]
    target = int(round(tool_width_px * roi_to_width_ratio))
    roi_height = max(1, min(target, h))
    return mask[h - roi_height : h, :], roi_height


def split_left_right(
    roi: np.ndarray, centerline_x: int
) -> tuple[np.ndarray, np.ndarray]:
    """Split a ROI into ``(left, right)`` halves at ``centerline_x``.

    The split column itself belongs to *neither* half so the metrics
    are exactly symmetric.
    """
    if roi.ndim != 2:
        raise ValueError(f"expected 2-D roi, got {roi.shape}")
    w = roi.shape[1]
    cx = int(np.clip(centerline_x, 1, w - 1))
    return roi[:, :cx], roi[:, cx + 1 :]
