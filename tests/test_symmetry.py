"""Tests for ``toolsym.symmetry``."""

from __future__ import annotations

import numpy as np
import pytest

from toolsym.symmetry import (
    ThreeZoneConfig,
    mean_absolute_difference,
    phase_shift_metric,
    three_zone_classify,
)
from toolsym.symmetry.three_zone import Zone
from toolsym.symmetry.weibull import fit_weibull, weibull_threshold


def test_phase_shift_metric_perfectly_symmetric() -> None:
    """A constant signal has D̄ = 0."""
    p = np.full(360, 100, dtype=np.int64)
    result = phase_shift_metric(p, n_edges=2)
    assert result.mean_abs_diff == 0.0
    assert result.relative_pct == 0.0


def test_phase_shift_metric_pure_180_asymmetry() -> None:
    """A signal that swings between 100 and 200 every 180° → D̄ = 100."""
    p = np.zeros(360, dtype=np.int64)
    p[:180] = 100
    p[180:] = 200
    result = phase_shift_metric(p, n_edges=2, span=180)
    assert result.mean_abs_diff == 100.0


def test_phase_shift_rejects_odd_edges() -> None:
    p = np.ones(360, dtype=np.int64)
    with pytest.raises(ValueError, match="even"):
        phase_shift_metric(p, n_edges=3)


def test_mean_absolute_difference_via_masks(synthetic_mask_stack: np.ndarray) -> None:
    """A disc has perfect symmetry → D̄ should be 0."""
    d_bar = mean_absolute_difference(synthetic_mask_stack, n_edges=2)
    assert d_bar == 0.0


def test_three_zone_safe() -> None:
    result = three_zone_classify(100.0, ThreeZoneConfig(t_noise=1500, t_fracture=3500))
    assert result.zone == Zone.SAFE


def test_three_zone_warning() -> None:
    result = three_zone_classify(2500.0, ThreeZoneConfig(t_noise=1500, t_fracture=3500))
    assert result.zone == Zone.WARNING


def test_three_zone_fracture() -> None:
    result = three_zone_classify(10000.0, ThreeZoneConfig(t_noise=1500, t_fracture=3500))
    assert result.zone == Zone.FRACTURE


def test_three_zone_rejects_inverted_thresholds() -> None:
    with pytest.raises(ValueError):
        three_zone_classify(100, ThreeZoneConfig(t_noise=4000, t_fracture=2000))


def test_weibull_fit_min_samples() -> None:
    with pytest.raises(ValueError, match="≥5"):
        fit_weibull(np.array([1.0, 2.0]))


def test_weibull_threshold_monotonic(rng) -> None:
    samples = rng.weibull(2.0, size=200) * 100.0 + 10.0
    t_001 = weibull_threshold(samples, p_fa=0.01)
    t_0001 = weibull_threshold(samples, p_fa=0.001)
    # Smaller P_FA → stricter threshold → larger T.
    assert t_0001 >= t_001
