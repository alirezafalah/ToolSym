"""Shared pytest fixtures.

The bulk of the regression-style fixtures are synthetic: a procedurally
generated four-edge tool whose ideal area-vs-angle signal is known
analytically. This means the suite runs in CI without needing the real
ELTE-TCM-46k dataset present.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pytest


@pytest.fixture(scope="session")
def rng() -> np.random.Generator:
    return np.random.default_rng(42)


@pytest.fixture(scope="session")
def synthetic_signal_4edge() -> tuple[np.ndarray, np.ndarray]:
    """A clean 4-edge area signal: ``A + B·|cos(2θ)|``.

    Returns ``(angles_deg, values)`` with 360 samples — exactly what a
    healthy 4-flute tool's projected-area signal should look like, give
    or take a phase shift.
    """
    angles = np.linspace(0.0, 360.0, 360, endpoint=False)
    values = 0.4 + 0.6 * np.abs(np.cos(2.0 * np.deg2rad(angles)))
    return angles, values


@pytest.fixture(scope="session")
def synthetic_signal_3edge() -> tuple[np.ndarray, np.ndarray]:
    """A clean 3-edge signal: ``A + B·|cos(1.5θ)|``."""
    angles = np.linspace(0.0, 360.0, 360, endpoint=False)
    values = 0.4 + 0.6 * np.abs(np.cos(1.5 * np.deg2rad(angles)))
    return angles, values


@pytest.fixture
def fractured_signal_4edge(
    synthetic_signal_4edge: tuple[np.ndarray, np.ndarray],
) -> tuple[np.ndarray, np.ndarray]:
    """Same as ``synthetic_signal_4edge`` but one segment is gouged."""
    angles, values = synthetic_signal_4edge
    out = values.copy()
    # Knock down the second cycle by 60% — simulates a chipped edge.
    sl = slice(90, 180)
    out[sl] *= 0.4
    return angles, out


def _disc_silhouette(h: int, w: int, radius_px: int) -> np.ndarray:
    cy, cx = h // 2, w // 2
    y, x = np.ogrid[:h, :w]
    mask = ((x - cx) ** 2 + (y - cy) ** 2) <= radius_px**2
    return (mask.astype(np.uint8) * 255)


@pytest.fixture
def synthetic_mask_stack(rng: np.random.Generator) -> np.ndarray:
    """A trivial 360-frame stack: a fixed disc, frame-independent.

    This is enough to exercise IO + master mask + pixel-area code paths.
    """
    h, w = 64, 64
    base = _disc_silhouette(h, w, radius_px=20)
    return np.broadcast_to(base, (360, h, w)).copy()


@pytest.fixture
def mask_folder(tmp_path: Path, synthetic_mask_stack: np.ndarray) -> Path:
    """Persist the synthetic mask stack as PNGs in a tmp folder."""
    from PIL import Image

    folder = tmp_path / "masks"
    folder.mkdir()
    for i, m in enumerate(synthetic_mask_stack):
        Image.fromarray(m).save(folder / f"mask_{i:03d}.png")
    return folder
