"""Master-mask aggregation (symmetry paper §2.2).

Sweeping a tool through 360° and taking the pixel-wise union of all
binary frames produces the silhouette of the bounding cylinder. The
weaving helical flutes fill the negative space, so even severely
fractured tools still trace straight outer walls — which is exactly
what the tilt regression in :mod:`toolsym.geometry.alignment` needs.
"""

from __future__ import annotations

import numpy as np

__all__ = ["build_master_mask"]


def build_master_mask(masks: np.ndarray, *, threshold: int = 127) -> np.ndarray:
    """Compute the pixel-wise OR of a binary mask stack.

    Parameters
    ----------
    masks
        ``(N, H, W)`` ``uint8`` stack from
        :func:`toolsym.io.masks.load_mask_sequence`.
    threshold
        Foreground binarisation cut-off (default ``127``).

    Returns
    -------
    np.ndarray
        ``(H, W)`` ``uint8`` mask: ``255`` where any frame had foreground,
        ``0`` elsewhere.
    """
    if masks.ndim != 3:
        raise ValueError(f"expected (N, H, W) stack, got {masks.shape}")
    return (np.any(masks > threshold, axis=0).astype(np.uint8) * 255)
