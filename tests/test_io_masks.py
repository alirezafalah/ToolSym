"""Tests for ``toolsym.io.masks``."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from toolsym.io.masks import (
    binarise,
    iter_mask_paths,
    load_mask,
    load_mask_sequence,
    save_mask,
)


def test_binarise_rgb_collapse() -> None:
    arr = np.zeros((4, 4, 3), dtype=np.uint8)
    arr[:, :, 0] = 200
    out = binarise(arr, threshold=100)
    assert out.dtype == np.uint8
    assert (out == 255).all()


def test_binarise_below_threshold() -> None:
    arr = np.full((4, 4), 50, dtype=np.uint8)
    assert (binarise(arr, threshold=100) == 0).all()


def test_iter_mask_paths_sorted(tmp_path: Path) -> None:
    for name in ("c.png", "a.png", "b.png", "ignored.txt"):
        (tmp_path / name).write_bytes(b"")
    paths = list(iter_mask_paths(tmp_path))
    assert [p.name for p in paths] == ["a.png", "b.png", "c.png"]


def test_iter_mask_paths_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        list(iter_mask_paths(tmp_path / "nope"))


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    mask = (np.eye(8, dtype=np.uint8) * 255)
    out = tmp_path / "m.png"
    save_mask(mask, out)
    back = load_mask(out)
    np.testing.assert_array_equal(back, mask)


def test_load_mask_sequence_shape_consistency(tmp_path: Path) -> None:
    for i in range(3):
        arr = np.full((8, 8), 200, dtype=np.uint8)
        Image.fromarray(arr).save(tmp_path / f"m_{i:03d}.png")
    masks, paths = load_mask_sequence(tmp_path)
    assert masks.shape == (3, 8, 8)
    assert len(paths) == 3


def test_load_mask_sequence_rejects_mismatched_shapes(tmp_path: Path) -> None:
    Image.fromarray(np.zeros((8, 8), dtype=np.uint8)).save(tmp_path / "a.png")
    Image.fromarray(np.zeros((4, 4), dtype=np.uint8)).save(tmp_path / "b.png")
    with pytest.raises(ValueError, match="Inconsistent"):
        load_mask_sequence(tmp_path)
