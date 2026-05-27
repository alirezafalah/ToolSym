"""1D signal pipeline from Falah et al. (2025).

The complete sequence is:

1. :func:`area_signal_from_masks` — turn N ordered masks into an N-sample
   signal of white-pixel count vs rotation angle, sampled from a tip ROI.
2. :func:`preprocess_signal` — scale to [0, 1] and shift the minimum to
   angle 0° so different tools become directly comparable.
3. :func:`find_segments` — Savitzky-Golay smoothing → ``find_peaks`` →
   one segment per cutting edge.
4. :func:`classify_segment_consistency` — first-stage fracture check
   based on segment-size deviation.
5. :func:`fit_segment_sinusoidals` → :func:`pairwise_coefficient_distances`
   → :func:`classify_sinusoidal_distances` — second-stage check using the
   self-calibrating dynamic threshold ``α·min + β``.
"""

from toolsym.signal.classify import (
    SegmentConsistency,
    SinusoidalDecision,
    classify_segment_consistency,
    classify_sinusoidal_distances,
)
from toolsym.signal.distance import pairwise_coefficient_distances
from toolsym.signal.peaks import SegmentInfo, find_segments
from toolsym.signal.pixel_area import area_signal_from_masks, white_pixels_in_roi
from toolsym.signal.preprocess import preprocess_signal, scale_signal, shift_min_to_zero
from toolsym.signal.sinusoidal_fit import (
    SinusoidalFit,
    SinusoidalParameters,
    fit_segment_sinusoidals,
    fit_sinusoidal,
)
from toolsym.signal.smoothing import savgol_circular

__all__ = [
    "SegmentConsistency",
    "SegmentInfo",
    "SinusoidalDecision",
    "SinusoidalFit",
    "SinusoidalParameters",
    "area_signal_from_masks",
    "classify_segment_consistency",
    "classify_sinusoidal_distances",
    "find_segments",
    "fit_segment_sinusoidals",
    "fit_sinusoidal",
    "pairwise_coefficient_distances",
    "preprocess_signal",
    "savgol_circular",
    "scale_signal",
    "shift_min_to_zero",
    "white_pixels_in_roi",
]
