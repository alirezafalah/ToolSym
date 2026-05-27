"""Convert a 360-frame mask sequence into a 1D area-vs-angle signal.

This is the core data transformation from Falah et al. (2025): the
*projected area* of the tool's cutting tip at each rotation angle is
counted as the number of foreground pixels inside an ROI at the bottom
of the silhouette. With one frame per degree this yields a 360-sample
periodic signal whose periodicity matches the tool's number of flutes.
"""

from __future__ import annotations

import numpy as np

__all__ = ["area_signal_from_masks", "white_pixels_in_roi"]


def _roi_slice(mask_height: int, roi_height: int) -> slice:
    if roi_height <= 0 or roi_height > mask_height:
        raise ValueError(
            f"roi_height={roi_height} out of range for mask height={mask_height}"
        )
    return slice(mask_height - roi_height, mask_height)


def white_pixels_in_roi(
    mask: np.ndarray, roi_height: int, *, threshold: int = 127
) -> int:
    """Count foreground pixels in the bottom ``roi_height`` rows of one mask.

    Parameters
    ----------
    mask
        ``(H, W)`` array; any positive intensity above ``threshold`` is
        treated as foreground.
    roi_height
        How many rows at the bottom of the image to consider. The paper
        uses ~350 px (≈3 mm on the rig from Falah et al. 2025).
    threshold
        Binarisation cut-off (default ``127``).
    """
    if mask.ndim != 2:
        raise ValueError(f"expected 2-D mask, got shape {mask.shape}")
    sl = _roi_slice(mask.shape[0], roi_height)
    return int(np.count_nonzero(mask[sl] > threshold))


def area_signal_from_masks(
    masks: np.ndarray,
    roi_height: int = 350,
    *,
    threshold: int = 127,
) -> np.ndarray:
    """Compute the 1D area signal from an ordered stack of masks.

    Parameters
    ----------
    masks
        ``(N, H, W)`` ``uint8`` stack as returned by
        :func:`toolsym.io.masks.load_mask_sequence`.
    roi_height
        Pixel height of the tip ROI. Default ``350`` matches the rig in
        the original paper.
    threshold
        Foreground binarisation cut-off.

    Returns
    -------
    np.ndarray
        ``(N,)`` int64 array of pixel counts per frame.
    """
    if masks.ndim != 3:
        raise ValueError(f"expected (N, H, W) stack, got shape {masks.shape}")
    sl = _roi_slice(masks.shape[1], roi_height)
    return np.count_nonzero(masks[:, sl, :] > threshold, axis=(1, 2)).astype(np.int64)
