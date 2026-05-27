"""Phase-shifted profile comparison (symmetry paper §2.4).

For an even-edged tool with ``N`` flutes, the silhouette projected from
rotation angle ``θ`` is geometrically identical to that at
``θ + 360°/N``. The damage metric is the absolute difference of
white-pixel counts in (by default) the right half of the tip ROI:

    D_i = | P_R(θ_i) - P_R(θ_i + 360°/N) |

Averaging ``D_i`` over a quarter rotation (90 frames for a 2-edge tool)
yields the scalar ``D̄`` per tool.

This module accepts either a raw mask sequence (and computes the
``P_R`` series internally) or a pre-computed pair of arrays. Use the
high-level :func:`mean_absolute_difference` for the common case.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = [
    "PhaseShiftResult",
    "mean_absolute_difference",
    "phase_shift_metric",
    "right_half_pixel_counts",
]


@dataclass(frozen=True, slots=True)
class PhaseShiftResult:
    """Per-frame and aggregate phase-shift metrics."""

    differences: np.ndarray
    mean_abs_diff: float
    relative_pct: float
    """``mean_abs_diff`` divided by the mean of the source signal × 100."""


def right_half_pixel_counts(
    masks: np.ndarray,
    *,
    roi_height: int | None = None,
    centerline_x: int | None = None,
    threshold: int = 127,
) -> np.ndarray:
    """White-pixel count for the right half of each frame's tip ROI.

    Parameters
    ----------
    masks
        ``(N, H, W)`` ``uint8`` stack.
    roi_height
        Optional crop at the tip. ``None`` uses the whole mask height
        (caller may pre-crop instead).
    centerline_x
        Column index of the tool centerline. ``None`` defaults to the
        image's middle column.
    threshold
        Foreground binarisation cut-off (default ``127``).
    """
    if masks.ndim != 3:
        raise ValueError(f"expected (N, H, W) stack, got {masks.shape}")
    n, h, w = masks.shape
    sl_y = slice(h - roi_height, h) if roi_height else slice(None)
    cx = w // 2 if centerline_x is None else int(centerline_x)
    return np.count_nonzero(masks[:, sl_y, cx + 1 :] > threshold, axis=(1, 2)).astype(np.int64)


def phase_shift_metric(
    pixel_counts: np.ndarray,
    *,
    n_edges: int = 2,
    span: int | None = None,
) -> PhaseShiftResult:
    """Compute the phase-shift metric from a precomputed series.

    Parameters
    ----------
    pixel_counts
        1D array of per-frame pixel counts (one frame per degree, length
        usually 360).
    n_edges
        Tool flute count. Must be even (the paper formalises only even
        cases). Determines the phase offset = ``360° / n_edges``.
    span
        Number of consecutive frames to average over. Default is one
        full segment, i.e. ``360 / n_edges`` (90 frames for ``n=2``).
    """
    p = np.asarray(pixel_counts, dtype=np.int64)
    n = p.size
    if n == 0:
        raise ValueError("pixel_counts is empty")
    if n_edges < 2 or n_edges % 2:
        raise ValueError(f"n_edges must be even ≥2; got {n_edges}")
    samples_per_degree = n / 360.0
    shift = int(round(360.0 / n_edges * samples_per_degree))
    if shift <= 0 or shift >= n:
        raise ValueError(f"derived shift={shift} invalid for n={n}, n_edges={n_edges}")
    if span is None:
        span = shift
    span = min(span, n - shift)
    diffs = np.abs(p[:span].astype(np.int64) - p[shift : shift + span].astype(np.int64))
    mean_abs = float(np.mean(diffs))
    mean_signal = float(np.mean(p)) if np.mean(p) > 0 else 1.0
    return PhaseShiftResult(
        differences=diffs,
        mean_abs_diff=mean_abs,
        relative_pct=mean_abs / mean_signal * 100.0,
    )


def mean_absolute_difference(
    masks: np.ndarray,
    *,
    n_edges: int = 2,
    roi_height: int | None = None,
    centerline_x: int | None = None,
    span: int | None = None,
    threshold: int = 127,
) -> float:
    """End-to-end convenience: masks → D̄.

    See :func:`right_half_pixel_counts` and :func:`phase_shift_metric`
    for argument semantics.
    """
    counts = right_half_pixel_counts(
        masks,
        roi_height=roi_height,
        centerline_x=centerline_x,
        threshold=threshold,
    )
    return phase_shift_metric(counts, n_edges=n_edges, span=span).mean_abs_diff
