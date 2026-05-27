"""Segment identification via peak detection (Falah et al. 2025 §2.2.2).

After Savitzky-Golay smoothing exposes the fundamental periodicity, the
paper uses ``scipy.signal.find_peaks`` with ``distance=30°`` and
``prominence=0.2`` to count peaks robustly across two- to eight-edge
tools. Each peak corresponds to one cutting edge; segment boundaries
are derived from peak positions.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import find_peaks as _find_peaks

from toolsym.signal.smoothing import savgol_circular

__all__ = ["SegmentInfo", "find_segments"]


@dataclass(frozen=True, slots=True)
class SegmentInfo:
    """Result of segment identification.

    Attributes
    ----------
    n_segments
        Number of cutting edges = number of detected peaks.
    peak_indices
        Sample indices of the detected peaks in the (smoothed) signal.
    peak_angles_deg
        Same peaks expressed in degrees.
    segment_sizes_deg
        Angular distance from each peak to the next, wrapping around 360°.
        Length equals ``n_segments``.
    smoothed
        The smoothed signal used for peak detection (kept so callers
        can plot it).
    """

    n_segments: int
    peak_indices: np.ndarray
    peak_angles_deg: np.ndarray
    segment_sizes_deg: np.ndarray
    smoothed: np.ndarray


def find_segments(
    signal: np.ndarray,
    angles_deg: np.ndarray | None = None,
    *,
    sg_window: int = 51,
    sg_polyorder: int = 3,
    min_distance_deg: float = 30.0,
    prominence: float = 0.2,
) -> SegmentInfo:
    """Identify cutting-edge peaks and segment sizes.

    Parameters
    ----------
    signal
        Preprocessed (scaled, shifted) 1D signal — see
        :func:`toolsym.signal.preprocess.preprocess_signal`.
    angles_deg
        Matching angles. Default: evenly spaced over [0°, 360°).
    sg_window, sg_polyorder
        Savitzky-Golay parameters for the smoothing pass.
    min_distance_deg
        Minimum angular spacing between peaks. The paper uses ``30°``
        (a generous lower bound for an 8-edge tool whose peaks land at
        ~45° intervals).
    prominence
        ``find_peaks`` prominence threshold. With signal scaled to
        [0, 1], ``0.2`` reliably separates true peaks from ripple.

    Returns
    -------
    SegmentInfo

    Raises
    ------
    RuntimeError
        If no peaks are detected — the signal is unusable.
    """
    n = signal.size
    if angles_deg is None:
        angles_deg = np.linspace(0.0, 360.0, n, endpoint=False)
    elif angles_deg.shape != signal.shape:
        raise ValueError(
            f"angles {angles_deg.shape} != signal {signal.shape}"
        )

    smoothed = savgol_circular(signal, window_length=sg_window, polyorder=sg_polyorder)
    distance_samples = max(1, int(round(min_distance_deg / 360.0 * n)))
    peaks, _ = _find_peaks(smoothed, distance=distance_samples, prominence=prominence)

    if peaks.size == 0:
        raise RuntimeError(
            "No peaks detected — signal lacks periodicity at the given "
            f"prominence={prominence}, distance={min_distance_deg}°."
        )

    peak_angles = angles_deg[peaks]
    sorted_idx = np.argsort(peak_angles)
    peaks = peaks[sorted_idx]
    peak_angles = peak_angles[sorted_idx]
    next_peak = np.roll(peak_angles, -1)
    sizes = (next_peak - peak_angles) % 360.0

    return SegmentInfo(
        n_segments=int(peaks.size),
        peak_indices=peaks,
        peak_angles_deg=peak_angles,
        segment_sizes_deg=sizes,
        smoothed=smoothed,
    )
