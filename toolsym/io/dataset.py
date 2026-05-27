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
    "ToolRecord",
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
