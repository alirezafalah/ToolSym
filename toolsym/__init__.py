"""ToolSym — Tool Condition Monitoring + CNC tool simulation.

ToolSym consolidates the algorithms behind three peer-reviewed / submitted
papers by Falah, Andó, and Szekeres at ELTE into a single, importable
Python library plus two PySide6 desktop applications:

* ``toolsym-tcm``  — analysis app (image-to-signal pipeline, symmetry
                     analysis, visual-hull reconstruction)
* ``toolsym-sim``  — dataset-generation app (CAD → silhouette renderer,
                     noise injector, augmentor, voxel-grid ground truth)

The library is intentionally GUI-free. Every algorithm under
``toolsym.{config,io,geometry,signal,symmetry,reconstruction,simulation}``
is a plain function with type hints, so it can be driven from notebooks,
CI tests, or alternative front-ends.

Public re-exports
-----------------
The most commonly used functions are re-exported here so users can write
``from toolsym import area_signal, fit_segments, phase_shift_metric``
without needing to know the internal layout.

See ``CITATION.cff`` for the underlying papers.
"""

from __future__ import annotations

__version__ = "0.1.0"
__author__ = "Alireza Falah"
__license__ = "Apache-2.0"

from toolsym.config import (
    CameraIntrinsics,
    VoxelGridSpec,
    data_root,
    load_intrinsics,
    load_voxel_grid_spec,
)
from toolsym.signal import (
    area_signal_from_masks,
    classify_segment_consistency,
    classify_sinusoidal_distances,
    find_segments,
    fit_segment_sinusoidals,
    pairwise_coefficient_distances,
    preprocess_signal,
)
from toolsym.symmetry import (
    mean_absolute_difference,
    phase_shift_metric,
    three_zone_classify,
)

__all__ = [
    "CameraIntrinsics",
    "VoxelGridSpec",
    "__author__",
    "__license__",
    "__version__",
    "area_signal_from_masks",
    "classify_segment_consistency",
    "classify_sinusoidal_distances",
    "data_root",
    "find_segments",
    "fit_segment_sinusoidals",
    "load_intrinsics",
    "load_voxel_grid_spec",
    "mean_absolute_difference",
    "pairwise_coefficient_distances",
    "phase_shift_metric",
    "preprocess_signal",
    "three_zone_classify",
]
