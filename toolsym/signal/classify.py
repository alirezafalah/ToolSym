"""Fracture classification (Falah et al. 2025 §3).

Two stages, in order:

1. :func:`classify_segment_consistency` — check that segment sizes
   (peak-to-peak distances) all fall within a tolerance of their mean.
   A failure here means *obvious* fracture (missing flute).
2. :func:`classify_sinusoidal_distances` — when the tool passes step 1,
   compare the sinusoidal-coefficient distances against a dynamic
   threshold ``α · min(distance) + β``. The paper uses ``α = 1.1`` and
   ``β = 10`` as conservative defaults.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = [
    "SegmentConsistency",
    "SinusoidalDecision",
    "classify_segment_consistency",
    "classify_sinusoidal_distances",
]


@dataclass(frozen=True, slots=True)
class SegmentConsistency:
    """Outcome of the first-stage size-deviation check."""

    intact: bool
    max_deviation_pct: float
    mean_size_deg: float
    tolerance_pct: float


def classify_segment_consistency(
    segment_sizes_deg: np.ndarray, tolerance_pct: float = 5.0
) -> SegmentConsistency:
    """Flag fracture if any segment deviates more than ``tolerance_pct``
    from the mean segment size.
    """
    s = np.asarray(segment_sizes_deg, dtype=np.float64)
    if s.size == 0:
        raise ValueError("empty segment_sizes_deg")
    mean = float(np.mean(s))
    if mean <= 0:
        return SegmentConsistency(False, float("inf"), mean, tolerance_pct)
    max_dev = float(np.max(np.abs(s - mean)) / mean * 100.0)
    return SegmentConsistency(
        intact=max_dev <= tolerance_pct,
        max_deviation_pct=max_dev,
        mean_size_deg=mean,
        tolerance_pct=tolerance_pct,
    )


@dataclass(frozen=True, slots=True)
class SinusoidalDecision:
    """Outcome of the second-stage sinusoidal-coefficient comparison."""

    intact: bool
    threshold: float
    min_distance: float
    max_distance: float
    alpha: float
    beta: float


def classify_sinusoidal_distances(
    distances: np.ndarray,
    *,
    alpha: float = 1.1,
    beta: float = 10.0,
) -> SinusoidalDecision:
    """Dynamic-threshold classifier.

    ``threshold = α · min_off_diagonal(distances) + β``. The tool is
    flagged fractured if the maximum off-diagonal distance exceeds the
    threshold.

    The default ``α = 1.1``, ``β = 10`` come straight from Falah 2025
    §3.2. Both can be tuned as more data becomes available.

    Notes
    -----
    Requires the input matrix to be at least 3×3 (a two-edge tool has
    only one pairwise comparison and so provides no baseline — handled
    in the symmetry paper instead).
    """
    d = np.asarray(distances, dtype=np.float64)
    if d.ndim != 2 or d.shape[0] != d.shape[1]:
        raise ValueError(f"need square matrix; got {d.shape}")
    k = d.shape[0]
    if k < 3:
        raise ValueError(
            f"need ≥3 segments for a baseline; got {k}. "
            "Use toolsym.symmetry for two-edge tools."
        )

    iu = np.triu_indices(k, k=1)
    off = d[iu]
    dmin = float(np.min(off))
    dmax = float(np.max(off))
    threshold = alpha * dmin + beta
    return SinusoidalDecision(
        intact=dmax <= threshold,
        threshold=threshold,
        min_distance=dmin,
        max_distance=dmax,
        alpha=alpha,
        beta=beta,
    )
