"""Weibull-based probabilistic thresholding (symmetry paper §4.2).

Future work in the paper proposes replacing the empirical three-zone
boundaries with a Weibull fit on the functional-tool baseline:

    f(x; λ, k) = (k/λ)·(x/λ)^(k-1)·exp(-(x/λ)^k)

and deriving a threshold from a target Probability of False Alarm:

    T = λ · (−ln P_FA)^(1/k)

The current dataset (16 tools) is too small for a robust fit; this
module ships the math so the calculation slots in directly when a
larger baseline becomes available.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import weibull_min

__all__ = ["fit_weibull", "weibull_threshold"]


def fit_weibull(
    baseline_d_bars: np.ndarray,
) -> tuple[float, float]:
    """Fit a Weibull distribution to a sample of healthy ``D̄`` values.

    Returns
    -------
    (lam, k)
        Scale ``λ`` and shape ``k`` parameters.

    Raises
    ------
    ValueError
        If the input has fewer than 5 samples — the fit is meaningless
        below that.
    """
    x = np.asarray(baseline_d_bars, dtype=np.float64)
    if x.size < 5:
        raise ValueError(
            f"need ≥5 baseline samples for a Weibull fit, got {x.size}"
        )
    if np.any(x < 0):
        raise ValueError("baseline values must be non-negative")
    k, _, lam = weibull_min.fit(x, floc=0.0)
    return float(lam), float(k)


def weibull_threshold(
    baseline_d_bars: np.ndarray, p_fa: float = 0.001
) -> float:
    """Compute a P_FA threshold from a healthy baseline.

    Parameters
    ----------
    baseline_d_bars
        ``D̄`` values from confirmed-healthy tools.
    p_fa
        Target Probability of False Alarm (default ``0.001`` = 0.1 %).
    """
    if not 0.0 < p_fa < 1.0:
        raise ValueError(f"p_fa must be in (0, 1); got {p_fa}")
    lam, k = fit_weibull(baseline_d_bars)
    return float(lam * (-np.log(p_fa)) ** (1.0 / k))
