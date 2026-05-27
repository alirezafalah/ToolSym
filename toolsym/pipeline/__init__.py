"""Vendored full image-to-signal pipeline (Falah 2025).

This subpackage carries the original step-by-step pipeline from the
legacy ``image_to_signal`` repo verbatim, so the GUI can drive the same
processing your published work used. The newer pure-function modules in
``toolsym.signal`` / ``toolsym.geometry`` / ``toolsym.symmetry`` remain
the canonical library API; this package is the *runtime* pipeline the
analysis app calls.

Steps
-----
* :mod:`step1_blur_and_rename` — median blur of raw frames.
* :mod:`step2_generate_masks` — background subtraction → binary masks.
* :mod:`step3_analyze_and_plot` — raw area-vs-angle CSV + plot.
* :mod:`step4_process_and_plot` — scaled + shifted + segmented plot.
* :mod:`dashboard_generator` — single-tool dashboard.
* :mod:`compare_dashboard_generator` — multi-tool comparison dashboard.

Utilities
---------
* :mod:`utils.optimized_processing` — GPU (OpenCL) / multicore / single
  backend dispatch for every step.
* :mod:`utils.filters` — background subtraction + morphology filters.
* :mod:`utils.image_utils`, :mod:`utils.mask_refinement` — helpers.
"""

from toolsym.pipeline.utils.optimized_processing import (
    check_gpu_available,
    get_optimization_info,
)

__all__ = ["check_gpu_available", "get_optimization_info"]
