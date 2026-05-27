"""Pairwise Euclidean distances on sinusoidal coefficient vectors.

Each segment is summarised by a four-vector ``(A, B, C, D)``. The
distance between two segments is the ``L2`` norm of their difference.
For an intact tool every pair should sit close together; a fractured
edge produces a much larger distance to all healthy peers, which the
classifier picks up.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from toolsym.signal.sinusoidal_fit import SinusoidalFit

__all__ = ["pairwise_coefficient_distances"]


def pairwise_coefficient_distances(
    fits: Sequence[SinusoidalFit],
) -> np.ndarray:
    """Return a symmetric ``(K, K)`` distance matrix.

    Diagonal entries are zero. Entry ``(i, j)`` is the Euclidean distance
    between the ``(A, B, C, D)`` vectors of segments ``i`` and ``j``.
    """
    k = len(fits)
    if k < 2:
        return np.zeros((k, k), dtype=np.float64)
    coefs = np.stack([f.parameters.as_array() for f in fits], axis=0)
    diff = coefs[:, None, :] - coefs[None, :, :]
    return np.sqrt(np.sum(diff**2, axis=-1))
