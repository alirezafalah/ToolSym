"""Smoke tests for the ``toolsym`` CLI."""

from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path

import pytest

from toolsym.cli import build_parser, main


def test_parser_has_subcommands() -> None:
    parser = build_parser()
    # Just make sure the parser builds and lists the commands.
    help_text = parser.format_help()
    for cmd in ("info", "signal", "classify", "symmetry"):
        assert cmd in help_text


def test_info_prints_json(capsys, monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("TOOLSYM_DATA", str(tmp_path))
    rc = main(["info"])
    assert rc == 0
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert "toolsym_version" in parsed
    assert "voxel_grid_spec" in parsed
    assert parsed["voxel_grid_spec"]["grid_shape"] == [128, 128, 128]


def test_signal_subcommand_end_to_end(
    tmp_path: Path, mask_folder: Path
) -> None:
    out = tmp_path / "signal.csv"
    rc = main(["signal", str(mask_folder), str(out), "--roi-height", "32"])
    assert rc == 0
    assert out.is_file()
    # Two columns, 360 rows + header
    lines = out.read_text().strip().splitlines()
    assert len(lines) == 361


def test_symmetry_subcommand(mask_folder: Path, capsys) -> None:
    rc = main(["symmetry", str(mask_folder), "--n-edges", "2"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "D̄" in out
