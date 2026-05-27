"""Preprocessing per Falah et al. (2025) §2.2.1.

Two operations make signals from different tools directly comparable:

* **Scale** the values to ``[0, 1]`` (min → 0, max → 1).
* **Shift** so the angular position of the global minimum becomes 0°,
  using a circular rotation. After shifting, every tool's 0° corresponds
  to its narrowest projected area.
"""

from __future__ import annotations

import numpy as np

__all__ = ["preprocess_signal", "scale_signal", "shift_min_to_zero"]


def scale_signal(values: np.ndarray) -> np.ndarray:
    """Linearly rescale to ``[0, 1]``.

    Constant inputs (max == min) are returned as zeros to avoid NaNs.
    """
    v = np.asarray(values, dtype=np.float64)
    lo, hi = v.min(), v.max()
    if hi <= lo:
        return np.zeros_like(v)
    return (v - lo) / (hi - lo)


def shift_min_to_zero(
    values: np.ndarray, angles_deg: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Circularly rotate the signal so its minimum lands at angle 0°.

    Parameters
    ----------
    values
        1D periodic signal.
    angles_deg
        Matching angle samples, assumed monotonically increasing and
        evenly spaced over [0°, 360°).

    Returns
    -------
    values_shifted, angles_shifted
        Same length as inputs, with element ``i = 0`` now corresponding
        to the previous global minimum.
    """
    v = np.asarray(values)
    a = np.asarray(angles_deg, dtype=np.float64)
    if v.shape != a.shape:
        raise ValueError(f"shape mismatch: values={v.shape} angles={a.shape}")
    if v.size == 0:
        return v.copy(), a.copy()
    k = int(np.argmin(v))
    v_shifted = np.roll(v, -k)
    n = v.size
    step = 360.0 / n
    a_shifted = (np.arange(n) * step) % 360.0
    return v_shifted, a_shifted


def preprocess_signal(
    values: np.ndarray, angles_deg: np.ndarray | None = None
) -> tuple[np.ndarray, np.ndarray]:
    """Scale to ``[0, 1]`` and shift the minimum to 0°.

    If ``angles_deg`` is omitted, samples are assumed evenly spaced over
    ``[0°, 360°)``.
    """
    v = np.asarray(values, dtype=np.float64)
    a = (
        np.asarray(angles_deg, dtype=np.float64)
        if angles_deg is not None
        else np.linspace(0.0, 360.0, v.size, endpoint=False)
    )
    return shift_min_to_zero(scale_signal(v), a)
