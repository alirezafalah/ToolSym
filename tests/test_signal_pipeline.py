"""End-to-end tests for the ``toolsym.signal`` package.

The fixtures generate synthetic 4-edge and 3-edge signals so the pure
algorithms can be validated without the real dataset.
"""

from __future__ import annotations

import numpy as np
import pytest

from toolsym.signal import (
    area_signal_from_masks,
    classify_segment_consistency,
    classify_sinusoidal_distances,
    find_segments,
    fit_segment_sinusoidals,
    pairwise_coefficient_distances,
    preprocess_signal,
    savgol_circular,
    white_pixels_in_roi,
)
from toolsym.signal.preprocess import scale_signal, shift_min_to_zero


def test_white_pixels_in_roi_counts_only_bottom() -> None:
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[90:, :] = 255
    assert white_pixels_in_roi(mask, roi_height=20) == 10 * 100
    assert white_pixels_in_roi(mask, roi_height=5) == 5 * 100


def test_area_signal_from_masks_shape(synthetic_mask_stack: np.ndarray) -> None:
    out = area_signal_from_masks(synthetic_mask_stack, roi_height=32)
    assert out.shape == (360,)
    # The disc is constant across frames → all values equal.
    assert (out == out[0]).all()


def test_scale_signal_range() -> None:
    v = np.linspace(2.0, 4.0, 10)
    s = scale_signal(v)
    assert s.min() == pytest.approx(0.0)
    assert s.max() == pytest.approx(1.0)


def test_scale_signal_constant() -> None:
    assert (scale_signal(np.full(5, 3.0)) == 0).all()


def test_shift_min_to_zero(synthetic_signal_4edge: tuple[np.ndarray, np.ndarray]) -> None:
    angles, values = synthetic_signal_4edge
    shifted, _ = shift_min_to_zero(values, angles)
    assert np.argmin(shifted) == 0


def test_preprocess_signal_roundtrip(synthetic_signal_4edge: tuple[np.ndarray, np.ndarray]) -> None:
    angles, values = synthetic_signal_4edge
    proc, ang = preprocess_signal(values, angles)
    assert proc.min() == pytest.approx(0.0, abs=1e-9)
    assert proc.max() == pytest.approx(1.0, abs=1e-9)
    assert ang[0] == 0.0


def test_savgol_circular_preserves_periodicity(
    synthetic_signal_4edge: tuple[np.ndarray, np.ndarray],
) -> None:
    _, values = synthetic_signal_4edge
    smoothed = savgol_circular(values, window_length=31, polyorder=3)
    # First and last samples should match the periodic continuity.
    diff = abs(smoothed[0] - smoothed[-1])
    raw_diff = abs(values[0] - values[-1])
    assert diff <= raw_diff + 1e-6  # smoothing can't increase the wrap discontinuity


def test_find_segments_counts_4(synthetic_signal_4edge: tuple[np.ndarray, np.ndarray]) -> None:
    _, values = synthetic_signal_4edge
    proc, _ = preprocess_signal(values)
    info = find_segments(proc)
    assert info.n_segments == 4
    # All segment sizes ~90°
    assert np.allclose(info.segment_sizes_deg, 90.0, atol=2.0)


def test_find_segments_counts_3(synthetic_signal_3edge: tuple[np.ndarray, np.ndarray]) -> None:
    _, values = synthetic_signal_3edge
    proc, _ = preprocess_signal(values)
    info = find_segments(proc)
    assert info.n_segments == 3
    assert np.allclose(info.segment_sizes_deg, 120.0, atol=2.0)


def test_segment_consistency_intact(
    synthetic_signal_4edge: tuple[np.ndarray, np.ndarray],
) -> None:
    _, values = synthetic_signal_4edge
    proc, _ = preprocess_signal(values)
    info = find_segments(proc)
    result = classify_segment_consistency(info.segment_sizes_deg)
    assert result.intact is True
    assert result.max_deviation_pct < 5.0


def test_segment_consistency_fractured(
    fractured_signal_4edge: tuple[np.ndarray, np.ndarray],
) -> None:
    _, values = fractured_signal_4edge
    proc, _ = preprocess_signal(values)
    info = find_segments(proc)
    # The gouge moves one peak; size deviation should exceed 5%.
    result = classify_segment_consistency(info.segment_sizes_deg)
    if result.intact:
        # If the gouge didn't kill the peak count, the sinusoidal stage
        # should flag it instead.
        fits = fit_segment_sinusoidals(proc, None, info.n_segments)
        d = pairwise_coefficient_distances(fits)
        if info.n_segments >= 3:
            decision = classify_sinusoidal_distances(d)
            assert decision.intact is False
    else:
        assert result.max_deviation_pct >= 5.0


def test_sinusoidal_fit_intact(
    synthetic_signal_4edge: tuple[np.ndarray, np.ndarray],
) -> None:
    _, values = synthetic_signal_4edge
    proc, _ = preprocess_signal(values)
    info = find_segments(proc)
    fits = fit_segment_sinusoidals(proc, None, info.n_segments)
    d = pairwise_coefficient_distances(fits)
    decision = classify_sinusoidal_distances(d)
    assert decision.intact is True


def test_sinusoidal_classifier_requires_three_segments() -> None:
    d = np.zeros((2, 2))
    with pytest.raises(ValueError, match="≥3"):
        classify_sinusoidal_distances(d)
