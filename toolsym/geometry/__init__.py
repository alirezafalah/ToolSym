"""Geometric pre-processing of binary masks.

The symmetry paper (Falah et al. 2026, under review) introduced two
shared infrastructure pieces used by both the symmetry analyser and the
visual-hull carver:

* :func:`build_master_mask` — pixel-wise OR across all rotation frames.
  The resulting silhouette traces the *bounding cylinder* of the tool,
  independent of helical-flute direction and robust to local tip damage.
* :func:`estimate_tilt_and_centerline` — linear regression of the
  master mask's left and right outer edges to recover (a) the small
  angular misalignment between spindle and camera and (b) the tool's
  true centerline.

Once those are known, :func:`rotate_to_axis` rectifies individual frames
and :func:`dynamic_roi` returns a tip ROI proportional to the tool's
estimated width.
"""

from toolsym.geometry.alignment import (
    TiltCenterline,
    estimate_tilt_and_centerline,
    rotate_to_axis,
)
from toolsym.geometry.master_mask import build_master_mask
from toolsym.geometry.roi import RoiSplit, dynamic_roi, split_left_right

__all__ = [
    "RoiSplit",
    "TiltCenterline",
    "build_master_mask",
    "dynamic_roi",
    "estimate_tilt_and_centerline",
    "rotate_to_axis",
    "split_left_right",
]
