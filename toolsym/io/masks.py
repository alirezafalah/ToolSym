"""Binary-mask IO: ordered loading from a tool's 360-frame folder.

The dataset convention is one binary PNG/TIFF per degree of rotation,
named so that ``sorted()`` returns angle-ascending order (e.g.
``mask_000.png`` ... ``mask_359.png`` or ``000.tif`` ... ``359.tif``).
This module hides the variations behind a single :func:`load_mask_sequence`
that returns a NumPy array shaped ``(N, H, W)`` with ``uint8`` values in
``{0, 255}``.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from pathlib import Path

import numpy as np
from PIL import Image

__all__ = [
    "MASK_SUFFIXES",
    "binarise",
    "iter_mask_paths",
    "load_mask",
    "load_mask_sequence",
    "save_mask",
]

MASK_SUFFIXES: tuple[str, ...] = (".png", ".tif", ".tiff", ".bmp")
"""File extensions recognised as binary-mask images."""


def iter_mask_paths(
    folder: str | Path, suffixes: Iterable[str] = MASK_SUFFIXES
) -> Iterator[Path]:
    """Yield mask paths in lexical order from ``folder``.

    Sorting is case-insensitive so mixed ``.PNG``/``.png`` casing on
    Windows-acquired datasets still order correctly.
    """
    folder = Path(folder)
    if not folder.is_dir():
        raise FileNotFoundError(folder)
    allowed = {s.lower() for s in suffixes}
    paths = [p for p in folder.iterdir() if p.suffix.lower() in allowed]
    paths.sort(key=lambda p: p.name.lower())
    yield from paths


def binarise(arr: np.ndarray, threshold: int = 127) -> np.ndarray:
    """Threshold an image array to ``{0, 255}`` ``uint8``.

    Handles single-channel and 3-channel inputs (RGB is reduced via the
    maximum across channels, matching the simulation renderer's
    convention).
    """
    if arr.ndim == 3:
        arr = arr.max(axis=2)
    return np.where(arr > threshold, 255, 0).astype(np.uint8)


def load_mask(path: str | Path, *, binarise_it: bool = True) -> np.ndarray:
    """Load a single mask. Returns an ``(H, W)`` ``uint8`` array."""
    arr = np.asarray(Image.open(Path(path)))
    if binarise_it:
        return binarise(arr)
    if arr.ndim == 3:
        arr = arr.max(axis=2)
    return arr.astype(np.uint8)


def load_mask_sequence(
    folder: str | Path,
    *,
    binarise_it: bool = True,
    suffixes: Iterable[str] = MASK_SUFFIXES,
) -> tuple[np.ndarray, list[Path]]:
    """Load every mask in a folder, ordered.

    Returns
    -------
    masks : np.ndarray
        Stacked array shaped ``(N, H, W)``, ``uint8``.
    paths : list[Path]
        Source paths in load order, useful for error reporting.

    Raises
    ------
    FileNotFoundError
        If the folder has no masks.
    ValueError
        If frames have inconsistent shapes.
    """
    paths = list(iter_mask_paths(folder, suffixes=suffixes))
    if not paths:
        raise FileNotFoundError(f"No mask files in {folder}")
    first = load_mask(paths[0], binarise_it=binarise_it)
    masks = np.empty((len(paths), *first.shape), dtype=np.uint8)
    masks[0] = first
    for i, p in enumerate(paths[1:], start=1):
        frame = load_mask(p, binarise_it=binarise_it)
        if frame.shape != first.shape:
            raise ValueError(
                f"Inconsistent mask shape in {folder}: "
                f"{paths[0].name}={first.shape} vs {p.name}={frame.shape}"
            )
        masks[i] = frame
    return masks, paths


def save_mask(mask: np.ndarray, path: str | Path) -> None:
    """Persist a binary mask as PNG or TIFF (extension picks the format)."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if mask.dtype != np.uint8:
        mask = binarise(mask)
    Image.fromarray(mask).save(Path(path))
