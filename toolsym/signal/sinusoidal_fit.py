"""Per-segment sinusoidal fitting (Falah et al. 2025 §2.2.4).

Each segment of the preprocessed signal is fitted with

    f(x) = A · sin(B·x + C) + D

where ``x`` is the *relative angle within the segment* in radians (each
segment starts at 0). The four-tuple ``(A, B, C, D)`` becomes a fingerprint
of one cutting edge's geometry; pairwise comparison of these fingerprints
across segments is what eventually drives the fracture decision.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import curve_fit

__all__ = [
    "SinusoidalFit",
    "SinusoidalParameters",
    "fit_segment_sinusoidals",
    "fit_sinusoidal",
]


@dataclass(frozen=True, slots=True)
class SinusoidalParameters:
    """The four coefficients of ``A·sin(B·x+C) + D``."""

    A: float
    B: float
    C: float
    D: float

    def as_array(self) -> np.ndarray:
        return np.asarray([self.A, self.B, self.C, self.D], dtype=np.float64)

    def predict(self, x_rad: np.ndarray) -> np.ndarray:
        return self.A * np.sin(self.B * x_rad + self.C) + self.D


@dataclass(frozen=True, slots=True)
class SinusoidalFit:
    """One fitted segment.

    Attributes
    ----------
    parameters
        The four coefficients.
    r_squared
        Goodness-of-fit on the segment's data.
    relative_angles_rad, values
        The data points the fit was computed on, useful for plotting.
    """

    parameters: SinusoidalParameters
    r_squared: float
    relative_angles_rad: np.ndarray
    values: np.ndarray


def _model(x: np.ndarray, A: float, B: float, C: float, D: float) -> np.ndarray:
    return A * np.sin(B * x + C) + D


def fit_sinusoidal(
    relative_angles_rad: np.ndarray,
    values: np.ndarray,
    *,
    max_nfev: int = 5000,
) -> SinusoidalFit:
    """Fit ``A·sin(B·x+C) + D`` to one segment.

    The initial guess uses the segment's amplitude and mean for ``(A, D)``
    and a frequency that fits one full cycle in the segment span — this
    is the heuristic that consistently converges on the paper's data.
    """
    x = np.asarray(relative_angles_rad, dtype=np.float64)
    y = np.asarray(values, dtype=np.float64)
    if x.shape != y.shape or x.size < 4:
        raise ValueError(
            "need ≥4 matched samples; got "
            f"x={x.shape}, y={y.shape}"
        )

    A0 = (y.max() - y.min()) / 2.0
    D0 = float(np.mean(y))
    span = float(x.max() - x.min())
    B0 = 2.0 * np.pi / span if span > 0 else 1.0
    C0 = 0.0
    p0 = (A0, B0, C0, D0)

    try:
        popt, _ = curve_fit(_model, x, y, p0=p0, maxfev=max_nfev)
    except RuntimeError:
        popt = np.asarray(p0)

    y_pred = _model(x, *popt)
    ss_res = float(np.sum((y - y_pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    return SinusoidalFit(
        parameters=SinusoidalParameters(*map(float, popt)),
        r_squared=r2,
        relative_angles_rad=x,
        values=y,
    )


def fit_segment_sinusoidals(
    signal: np.ndarray,
    angles_deg: np.ndarray | None,
    n_segments: int,
) -> list[SinusoidalFit]:
    """Split the signal into ``n_segments`` equal pieces and fit each.

    The paper deliberately divides the full 360° span *evenly* rather
    than using the peak-to-peak distances, so the coefficients are
    directly comparable. Each segment's angles are shifted so it starts
    at 0 before fitting; this anchors the phase ``C`` to a common origin
    (also per the paper).
    """
    if n_segments < 1:
        raise ValueError(f"n_segments must be ≥1, got {n_segments}")
    n = signal.size
    if angles_deg is None:
        angles_deg = np.linspace(0.0, 360.0, n, endpoint=False)
    # Even split: take floor(n / k) samples per segment, drop the remainder.
    chunk = n // n_segments
    if chunk < 4:
        raise ValueError(
            f"signal too short ({n} samples) for {n_segments} segments"
        )
    fits: list[SinusoidalFit] = []
    for i in range(n_segments):
        start = i * chunk
        stop = start + chunk
        y = signal[start:stop]
        seg_angles = angles_deg[start:stop]
        x_rad = np.deg2rad(seg_angles - seg_angles[0])
        fits.append(fit_sinusoidal(x_rad, y))
    return fits
