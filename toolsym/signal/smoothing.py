"""Circular Savitzky-Golay smoothing.

The paper applies an *aggressive* SG filter to expose only the
fundamental periodicity (one peak per cutting edge) before peak
detection. Because the signal is periodic, the filter must wrap at the
endpoints — naive ``scipy.signal.savgol_filter`` produces bogus edge
artefacts at 0° and 359°.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import savgol_filter

__all__ = ["savgol_circular"]


def savgol_circular(
    signal: np.ndarray, window_length: int = 51, polyorder: int = 3
) -> np.ndarray:
    """Apply a Savitzky-Golay filter with circular boundary conditions.

    Parameters
    ----------
    signal
        1D periodic signal.
    window_length
        Odd, ≤ ``len(signal)``. ``51`` works well for 360-sample signals
        in the original paper.
    polyorder
        Polynomial order. ``3`` keeps peaks and troughs faithfully.
    """
    if window_length % 2 == 0:
        raise ValueError(f"window_length must be odd; got {window_length}")
    if polyorder >= window_length:
        raise ValueError(
            f"polyorder ({polyorder}) must be < window_length ({window_length})"
        )
    n = signal.size
    if window_length > n:
        raise ValueError(
            f"window_length ({window_length}) > signal length ({n})"
        )
    pad = window_length // 2
    padded = np.concatenate([signal[-pad:], signal, signal[:pad]])
    smoothed = savgol_filter(padded, window_length=window_length, polyorder=polyorder)
    return smoothed[pad : pad + n]
