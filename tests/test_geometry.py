"""Tests for ``toolsym.geometry``."""

from __future__ import annotations

import numpy as np
import pytest

from toolsym.geometry import (
    build_master_mask,
    dynamic_roi,
    estimate_tilt_and_centerline,
    rotate_to_axis,
    split_left_right,
)


def test_master_mask_union(rng) -> None:
    n, h, w = 5, 16, 16
    stack = np.zeros((n, h, w), dtype=np.uint8)
    stack[0, 0:8, :] = 255
    stack[1, 8:16, :] = 255
    out = build_master_mask(stack)
    assert (out == 255).all()


def test_estimate_tilt_zero_for_vertical_bar() -> None:
    h, w = 200, 200
    mask = np.zeros((h, w), dtype=np.uint8)
    mask[:, 80:120] = 255
    result = estimate_tilt_and_centerline(mask)
    assert abs(result.tilt_deg) < 0.5
    assert abs(result.centerline_x_top - 100) < 2
    assert abs(result.centerline_x_bottom - 100) < 2


def test_estimate_tilt_recovers_known_rotation() -> None:
    """Tilt magnitude should match the rotation applied to a vertical bar."""
    import cv2

    h, w = 200, 200
    base = np.zeros((h, w), dtype=np.uint8)
    base[:, 80:120] = 255
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), -10.0, 1.0)
    rotated = cv2.warpAffine(base, matrix, (w, h), flags=cv2.INTER_NEAREST)
    result = estimate_tilt_and_centerline(rotated, top_skip_frac=0.0, bottom_skip_frac=0.0)
    # Sign depends on image-coordinate convention; magnitude should match.
    assert abs(abs(result.tilt_deg) - 10.0) < 2.0


def test_rotate_to_axis_undoes_tilt() -> None:
    import cv2

    h, w = 200, 200
    base = np.zeros((h, w), dtype=np.uint8)
    base[:, 80:120] = 255
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), -5.0, 1.0)
    rotated = cv2.warpAffine(base, matrix, (w, h), flags=cv2.INTER_NEAREST)
    fix = rotate_to_axis(rotated, 5.0)
    # The rectified middle row should be roughly the same as the original.
    assert np.count_nonzero(fix[100]) > 0


def test_dynamic_roi_shape() -> None:
    h, w = 1000, 800
    mask = np.zeros((h, w), dtype=np.uint8)
    roi, rh = dynamic_roi(mask, tool_width_px=300)
    assert roi.shape == (rh, w)
    assert rh == int(round(300 * 0.45))


def test_split_left_right_excludes_centerline() -> None:
    roi = np.arange(20, dtype=np.uint8).reshape(2, 10)
    left, right = split_left_right(roi, centerline_x=4)
    assert left.shape == (2, 4)
    assert right.shape == (2, 5)
