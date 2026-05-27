"""Command-line interface for the headless parts of ToolSym.

Provides a small ``toolsym`` console script with subcommands that wrap
the library's batch operations. The GUI apps (``toolsym-tcm``,
``toolsym-sim``) have their own entry points; this CLI is for scripting,
CI, and Docker.

Subcommands
-----------
``signal``
    Compute the 1D area-vs-angle signal for one tool (a folder of masks).
``classify``
    Run the hybrid Falah 2025 pipeline on a signal CSV and print the
    intact/fractured decision plus diagnostics.
``symmetry``
    Compute the symmetry-paper D̄ metric for a folder of masks.
``info``
    Print the resolved DATA root, version, bundled spec, and a quick
    environment self-check (which optional dependencies are available).
``tools``
    List every ``tool_id`` discovered under the DATA root via the
    legacy ELTE-TCM-46k folder convention.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from toolsym import __version__
from toolsym.config import data_root, load_voxel_grid_spec


def _cmd_info(_: argparse.Namespace) -> int:
    spec = load_voxel_grid_spec()
    optional: dict[str, bool] = {}
    for mod_name in ("pyvista", "vtk", "cadquery", "pyopencl", "torch", "PySide6"):
        try:
            __import__(mod_name)
            optional[mod_name] = True
        except ImportError:
            optional[mod_name] = False
    info = {
        "toolsym_version": __version__,
        "data_root": str(data_root()),
        "voxel_grid_spec": {
            "grid_shape": list(spec.grid_shape),
            "voxel_size_mm": spec.voxel_size_mm,
            "camera": spec.camera.to_dict(),
        },
        "optional_dependencies": optional,
    }
    json.dump(info, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def _cmd_signal(args: argparse.Namespace) -> int:
    from toolsym.io.masks import load_mask_sequence
    from toolsym.signal import area_signal_from_masks

    masks, _ = load_mask_sequence(args.masks_dir)
    signal = area_signal_from_masks(masks, roi_height=args.roi_height)
    angles = np.linspace(0.0, 360.0, len(signal), endpoint=False)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savetxt(
        out,
        np.column_stack([angles, signal]),
        delimiter=",",
        header="Angle (Degrees),ROI Area (Pixels)",
        comments="",
        fmt=["%.6f", "%d"],
    )
    print(f"Wrote {out} ({len(signal)} samples)")
    return 0


def _cmd_classify(args: argparse.Namespace) -> int:
    import pandas as pd

    from toolsym.signal import (
        classify_segment_consistency,
        classify_sinusoidal_distances,
        find_segments,
        fit_segment_sinusoidals,
        pairwise_coefficient_distances,
        preprocess_signal,
    )

    df = pd.read_csv(args.signal_csv)
    angles = df.iloc[:, 0].to_numpy()
    raw_signal = df.iloc[:, 1].to_numpy()
    signal, angles = preprocess_signal(raw_signal, angles)
    segs = find_segments(signal, angles)
    consistency = classify_segment_consistency(segs.segment_sizes_deg)
    fits = fit_segment_sinusoidals(signal, angles, segs.n_segments)
    dists = pairwise_coefficient_distances(fits)
    decision = classify_sinusoidal_distances(
        dists, alpha=args.alpha, beta=args.beta
    )
    out = {
        "tool": Path(args.signal_csv).stem,
        "n_segments": segs.n_segments,
        "segment_sizes_deg": segs.segment_sizes_deg.tolist(),
        "max_size_deviation_pct": consistency.max_deviation_pct,
        "size_check": "intact" if consistency.intact else "fractured",
        "sinusoidal_threshold": decision.threshold,
        "sinusoidal_max_distance": decision.max_distance,
        "decision": "intact" if decision.intact else "fractured",
    }
    json.dump(out, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def _cmd_tools(args: argparse.Namespace) -> int:
    from toolsym.io.dataset import iter_tools

    root = data_root(args.data_root)
    records = list(iter_tools(root, only_with_masks=not args.all))
    if not records:
        print(f"No tools found under {root} (expected `tools_metadata.csv` + `masks/`)")
        return 1
    width = max(len(r.tool_id) for r in records)
    for r in records:
        edges = r.n_edges if r.n_edges is not None else "?"
        cond = r.condition or "?"
        folder = r.mask_folder.name if r.mask_folder else "—"
        print(f"{r.tool_id:<{width}}  edges={edges:<3}  condition={cond:<12}  {folder}")
    return 0


def _cmd_symmetry(args: argparse.Namespace) -> int:
    from toolsym.io.masks import load_mask_sequence
    from toolsym.symmetry import mean_absolute_difference

    masks, _ = load_mask_sequence(args.masks_dir)
    d_bar = mean_absolute_difference(masks, n_edges=args.n_edges)
    print(f"D̄ = {d_bar:.4f} px")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="toolsym", description=__doc__)
    p.add_argument("--version", action="version", version=f"toolsym {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("info", help="Print environment, version, spec.").set_defaults(
        func=_cmd_info
    )

    sp = sub.add_parser("tools", help="List tools discovered under DATA root.")
    sp.add_argument("--data-root", type=Path, default=None)
    sp.add_argument("--all", action="store_true", help="Include tools without masks.")
    sp.set_defaults(func=_cmd_tools)

    sp = sub.add_parser("signal", help="Mask folder → 1D area signal CSV.")
    sp.add_argument("masks_dir", type=Path)
    sp.add_argument("output", type=Path)
    sp.add_argument(
        "--roi-height",
        type=int,
        default=350,
        help="ROI height in pixels at the tool tip (default: 350).",
    )
    sp.set_defaults(func=_cmd_signal)

    sp = sub.add_parser("classify", help="Run the hybrid classifier on a signal CSV.")
    sp.add_argument("signal_csv", type=Path)
    sp.add_argument("--alpha", type=float, default=1.1)
    sp.add_argument("--beta", type=float, default=10.0)
    sp.set_defaults(func=_cmd_classify)

    sp = sub.add_parser("symmetry", help="Compute D̄ on a mask folder.")
    sp.add_argument("masks_dir", type=Path)
    sp.add_argument("--n-edges", type=int, default=2)
    sp.set_defaults(func=_cmd_symmetry)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
