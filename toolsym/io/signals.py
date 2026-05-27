"""IO for 1D area-vs-angle signals.

A signal CSV has two columns: ``Angle (Degrees)`` and ``ROI Area (Pixels)``.
This matches the format the legacy ``Tool_Condition_Monitoring/image_to_signal``
pipeline wrote, so existing CSVs are forward-compatible.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

__all__ = ["load_signal_csv", "save_signal_csv"]

_HEADER = "Angle (Degrees),ROI Area (Pixels)"


def save_signal_csv(
    angles_deg: np.ndarray, values: np.ndarray, path: str | Path
) -> None:
    """Write a two-column CSV with the legacy header."""
    if angles_deg.shape != values.shape:
        raise ValueError(
            f"shape mismatch: angles {angles_deg.shape} vs values {values.shape}"
        )
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savetxt(
        out,
        np.column_stack([angles_deg, values]),
        delimiter=",",
        header=_HEADER,
        comments="",
        fmt=["%.6f", "%.6f"],
    )


def load_signal_csv(path: str | Path) -> tuple[np.ndarray, np.ndarray]:
    """Load ``(angles_deg, values)`` from a two-column CSV."""
    arr = np.loadtxt(Path(path), delimiter=",", skiprows=1)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    return arr[:, 0], arr[:, 1]
