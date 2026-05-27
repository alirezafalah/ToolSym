"""Symmetry-based fracture detection (Falah et al. 2026).

Adds an N=2 path that the Falah 2025 hybrid classifier can't handle: by
comparing a tool's profile at angle θ to its phase-shifted counterpart
at θ + 360°/N, you get a per-frame asymmetry metric ``D_i`` that doesn't
need three segments to self-calibrate.

The three-zone thresholding handles the segmentation noise the paper
observes on bright-coated tools without sacrificing the lightweight
nature of the algorithm.
"""

from toolsym.symmetry.phase_shift import (
    PhaseShiftResult,
    mean_absolute_difference,
    phase_shift_metric,
)
from toolsym.symmetry.three_zone import ThreeZoneClassification, ThreeZoneConfig, three_zone_classify
from toolsym.symmetry.weibull import weibull_threshold

__all__ = [
    "PhaseShiftResult",
    "ThreeZoneClassification",
    "ThreeZoneConfig",
    "mean_absolute_difference",
    "phase_shift_metric",
    "three_zone_classify",
    "weibull_threshold",
]
