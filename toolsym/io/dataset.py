"""Discovery helpers for the ELTE-TCM-46k dataset layout.

The legacy code expects this folder structure under the DATA root::

    DATA/
    ├── tools_metadata.csv            # columns: tool_id, edges, condition, ...
    ├── masks/
    │   ├── tool002_final_masks/
    │   │   ├── 000.tiff
    │   │   ├── 001.tiff
    │   │   └── …
    │   ├── tool002gain10_final_masks/   # alternative naming, same data
    │   └── tool002gain10paperBG_final_masks/
    └── raw/                              (optional)

This module wraps that convention so other code never has to spell it
out. It is *advisory*, not enforced — ``load_mask_sequence`` still
accepts any folder of binary PNGs/TIFFs.
"""

from __future__ import annotations

import csv
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "MASK_FOLDER_PATTERNS",
    "DatasetLayout",
    "ToolRecord",
    "build_legacy_config",
    "find_mask_folder",
    "iter_tools",
    "load_tools_metadata",
    "resolve_masks_root",
    "tool_ids_with_masks",
]


MASK_FOLDER_PATTERNS: tuple[str, ...] = (
    "{tool_id}_final_masks",
    "{tool_id}gain10_final_masks",
    "{tool_id}gain10paperBG_final_masks",
)
"""Folder-name patterns the legacy pipeline searched, in priority order."""


@dataclass(frozen=True, slots=True)
class ToolRecord:
    """One row of ``tools_metadata.csv`` plus its mask folder, if any."""

    tool_id: str
    metadata: dict[str, str]
    mask_folder: Path | None

    @property
    def n_edges(self) -> int | None:
        v = self.metadata.get("edges")
        try:
            return int(v) if v else None
        except (TypeError, ValueError):
            return None

    @property
    def condition(self) -> str | None:
        return self.metadata.get("condition") or None


def resolve_masks_root(data_root: Path) -> Path:
    """Return ``data_root / 'masks'`` (does not require existence)."""
    return Path(data_root) / "masks"


def find_mask_folder(
    tool_id: str,
    data_root: Path,
    *,
    patterns: tuple[str, ...] = MASK_FOLDER_PATTERNS,
) -> Path | None:
    """Locate a mask folder for ``tool_id`` under ``DATA/masks/``.

    Returns the first existing folder matching :data:`MASK_FOLDER_PATTERNS`,
    or ``None`` when no folder is found.
    """
    masks_root = resolve_masks_root(data_root)
    for pattern in patterns:
        candidate = masks_root / pattern.format(tool_id=tool_id)
        if candidate.is_dir():
            return candidate
    return None


def load_tools_metadata(data_root: Path) -> dict[str, dict[str, str]]:
    """Parse ``DATA/tools_metadata.csv`` into ``{tool_id: row_dict}``.

    Returns an empty dict if the CSV does not exist — the rest of the
    library tolerates missing metadata.
    """
    path = Path(data_root) / "tools_metadata.csv"
    if not path.is_file():
        return {}
    out: dict[str, dict[str, str]] = {}
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            tid = row.get("tool_id")
            if tid:
                out[tid] = dict(row)
    return out


def iter_tools(
    data_root: Path, *, only_with_masks: bool = True
) -> Iterator[ToolRecord]:
    """Yield one :class:`ToolRecord` per row of ``tools_metadata.csv``.

    When ``only_with_masks=True`` (default), tools without a discoverable
    mask folder are filtered out.
    """
    metadata = load_tools_metadata(data_root)
    for tool_id, row in sorted(metadata.items()):
        folder = find_mask_folder(tool_id, data_root)
        if only_with_masks and folder is None:
            continue
        yield ToolRecord(tool_id=tool_id, metadata=row, mask_folder=folder)


def tool_ids_with_masks(data_root: Path) -> list[str]:
    """Convenience: list every tool id that has a mask folder."""
    return [rec.tool_id for rec in iter_tools(data_root, only_with_masks=True)]


# ---------------------------------------------------------------------------
# Full legacy-layout mapping
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DatasetLayout:
    """Every output path the legacy ``image_to_signal/main.py`` derived
    from ``DATA_ROOT`` and ``TOOL_ID``. Centralising it here means tabs
    never have to spell paths out.
    """

    data_root: Path
    tool_id: str

    @property
    def raw_dir(self) -> Path:
        return self.data_root / "tools" / self.tool_id

    @property
    def blurred_dir(self) -> Path:
        return self.data_root / "blurred" / f"{self.tool_id}_blurred"

    @property
    def final_masks_dir(self) -> Path:
        return self.data_root / "masks" / f"{self.tool_id}_final_masks"

    @property
    def roi_csv(self) -> Path:
        return self.data_root / "1d_profiles" / f"{self.tool_id}_raw_data.csv"

    @property
    def roi_plot(self) -> Path:
        return self.data_root / "1d_profiles" / f"{self.tool_id}_raw_plot.svg"

    @property
    def processed_csv(self) -> Path:
        return self.data_root / "1d_profiles" / f"{self.tool_id}_processed_data.csv"

    @property
    def processed_plot(self) -> Path:
        return self.data_root / "1d_profiles" / f"{self.tool_id}_processed_plot.svg"

    @property
    def background_image(self) -> Path:
        return self.data_root / "backgrounds" / "paper_background.tiff"

    @property
    def analysis_output_dir(self) -> Path:
        return self.data_root / "1d_profiles" / "analysis_metadata"


def build_legacy_config(
    layout: DatasetLayout,
    *,
    optimization_method: str = "gpu",
    blur_kernel: int = 13,
    closing_kernel: int = 21,
    roi_height: int = 200,
    number_of_peaks: int = 2,
    apply_moving_average: bool = True,
    moving_average_window: int = 5,
    white_ratio_outlier_threshold: float = 0.8,
    background_subtraction_method: str = "lab",
    difference_threshold: int = 33,
    apply_multichannel_mask: bool = False,
    is_synthetic: bool = False,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    """Produce the dict-shaped ``CONFIG`` the vendored pipeline steps expect.

    Every key set by the legacy ``image_to_signal/main.py`` is reproduced
    here. Pass overrides as keyword arguments — the GUI builds this dict
    from its parameter spinboxes.
    """
    config: dict[str, object] = {
        # paths
        "RAW_DIR": str(layout.raw_dir),
        "BLURRED_DIR": str(layout.blurred_dir),
        "FINAL_MASKS_DIR": str(layout.final_masks_dir),
        "ROI_CSV_PATH": str(layout.roi_csv),
        "ROI_PLOT_PATH": str(layout.roi_plot),
        "PROCESSED_CSV_PATH": str(layout.processed_csv),
        "PROCESSED_PLOT_PATH": str(layout.processed_plot),
        "BACKGROUND_IMAGE_PATH": str(layout.background_image),
        "ANALYSIS_OUTPUT_DIR": str(layout.analysis_output_dir),
        # backend
        "OPTIMIZATION_METHOD": optimization_method,
        # image processing
        "blur_kernel": blur_kernel,
        "closing_kernel": closing_kernel,
        # HSV/LAB thresholds — defaults match legacy CONFIG
        "h_threshold_min": 70 // 2,
        "h_threshold_max": 100 // 2,
        "s_threshold_min": 15 * 2.55,
        "s_threshold_max": 70 * 2.55,
        "V_threshold_min": 45 * 2.55,
        "V_threshold_max": 55 * 2.55,
        "L_threshold_min": 50 * 2.55,
        "L_threshold_max": 56 * 2.55,
        "a_threshold_min": -10 + 128,
        "a_threshold_max": -1 + 128,
        "b_threshold_min": -10 + 128,
        "b_threshold_max": -8 + 128,
        # background subtraction
        "BACKGROUND_SUBTRACTION_METHOD": background_subtraction_method,
        "APPLY_MULTICHANNEL_MASK": apply_multichannel_mask,
        "DIFFERENCE_THRESHOLD": difference_threshold,
        # analysis
        "roi_height": roi_height,
        "WHITE_RATIO_OUTLIER_THRESHOLD": white_ratio_outlier_threshold,
        "APPLY_MOVING_AVERAGE": apply_moving_average,
        "MOVING_AVERAGE_WINDOW": moving_average_window,
        "NUMBER_OF_PEAKS": number_of_peaks,
        "IS_SYNTHETIC": is_synthetic,
    }
    if extra:
        config.update(extra)
    return config
