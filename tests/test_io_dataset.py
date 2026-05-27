"""Tests for ``toolsym.io.dataset`` — the legacy ELTE-TCM-46k layout."""

from __future__ import annotations

import csv
from pathlib import Path

from toolsym.io.dataset import (
    find_mask_folder,
    iter_tools,
    load_tools_metadata,
    resolve_masks_root,
    tool_ids_with_masks,
)


def _make_dataset(root: Path, tools: dict[str, dict[str, str]]) -> None:
    masks = root / "masks"
    masks.mkdir(parents=True, exist_ok=True)
    for tool_id, _row in tools.items():
        (masks / f"{tool_id}_final_masks").mkdir()
    csv_path = root / "tools_metadata.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["tool_id", "edges", "condition"])
        writer.writeheader()
        for tool_id, row in tools.items():
            writer.writerow({"tool_id": tool_id, **row})


def test_resolve_masks_root() -> None:
    assert resolve_masks_root(Path("/tmp/d")).name == "masks"


def test_load_tools_metadata_missing_returns_empty(tmp_path: Path) -> None:
    assert load_tools_metadata(tmp_path) == {}


def test_find_mask_folder_returns_none_when_missing(tmp_path: Path) -> None:
    assert find_mask_folder("toolXYZ", tmp_path) is None


def test_full_layout_roundtrip(tmp_path: Path) -> None:
    _make_dataset(
        tmp_path,
        {
            "tool001": {"edges": "2", "condition": "new"},
            "tool062": {"edges": "2", "condition": "fractured"},
            "tool115": {"edges": "2", "condition": "new"},
        },
    )
    meta = load_tools_metadata(tmp_path)
    assert set(meta.keys()) == {"tool001", "tool062", "tool115"}
    assert meta["tool062"]["condition"] == "fractured"

    assert find_mask_folder("tool062", tmp_path).name == "tool062_final_masks"
    assert tool_ids_with_masks(tmp_path) == ["tool001", "tool062", "tool115"]

    records = list(iter_tools(tmp_path))
    assert [r.tool_id for r in records] == ["tool001", "tool062", "tool115"]
    assert records[0].n_edges == 2
    assert records[1].condition == "fractured"


def test_iter_tools_skips_those_without_masks(tmp_path: Path) -> None:
    _make_dataset(tmp_path, {"tool001": {"edges": "2", "condition": "new"}})
    # Add a metadata row whose mask folder doesn't exist.
    with (tmp_path / "tools_metadata.csv").open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["tool_id", "edges", "condition"])
        writer.writerow({"tool_id": "ghost", "edges": "4", "condition": "new"})

    visible = [r.tool_id for r in iter_tools(tmp_path, only_with_masks=True)]
    assert visible == ["tool001"]
    all_ids = [r.tool_id for r in iter_tools(tmp_path, only_with_masks=False)]
    assert sorted(all_ids) == ["ghost", "tool001"]
