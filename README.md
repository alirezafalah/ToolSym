# ToolSym

[![CI](https://github.com/alirezafalah/ToolSym/actions/workflows/ci.yml/badge.svg)](https://github.com/alirezafalah/ToolSym/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/toolsym.svg)](https://pypi.org/project/toolsym/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

**ToolSym** — *Tool Condition Monitoring + CNC tool **Sim**ulation /
**Sym**metry analysis.*

A single library + two desktop apps consolidating three papers from the
ELTE PhD work of Alireza Falah, Mátyás Andó, and Béla Szekeres:

| Paper | Module(s) |
|-------|-----------|
| [Tool Condition Monitoring in CNC Systems: A Hybrid Computer Vision and Signal Processing Approach](https://doi.org/10.1007/s00170-025-17051-z) (IJAMT 2025) | `toolsym.signal` |
| Symmetry-Based Geometric Profile Analysis for Fracture Detection (2026, under review) | `toolsym.geometry`, `toolsym.symmetry` |
| Learning Deep Shape Priors for the 3D Reconstruction of Highly Reflective CNC Tools (ECCV submission) | `toolsym.reconstruction`, `toolsym.simulation`, `toolsym.ml` |

The companion dataset is [ELTE-TCM-46k on Hugging Face](https://huggingface.co/datasets/alirezafalah/ELTE-TCM-46k).

---

## What's in the box

```
toolsym/         shared library (pure functions, no Qt)
  config.py      DATA root, camera intrinsics, voxel grid spec
  io/            masks, signals, voxels
  geometry/      master mask, tilt regression, ROI
  signal/        1D pipeline (hybrid paper)
  symmetry/      phase-shift metric (symmetry paper)
  reconstruction/ visual hull (real masks) + voxelizer (CAD)
  simulation/    render, noise, augment
  widgets/       shared PySide6 widgets and theme
apps/
  toolsym_tcm/   analysis app
  toolsym_sim/   dataset-generation app
```

## Install

ToolSym is one package, three pip flavours:

```bash
pip install toolsym                     # core (analysis, no heavy 3D deps)
pip install "toolsym[simulation]"       # add pyvista/vtk/cadquery — sim app + voxelizer
pip install "toolsym[gpu]"              # add pyopencl — GPU-accelerated visual hull
pip install "toolsym[ml]"               # add torch — deep shape prior (future)
pip install "toolsym[all]"              # everything
```

`pip install -e .` works the same from a clone.

## Launch

```bash
toolsym-tcm         # analysis: image-to-signal, symmetry, visual hull
toolsym-sim         # dataset generation: render, noise, augment, voxelize
toolsym info        # CLI: print version + DATA root + spec
toolsym signal MASKS_DIR signal.csv
toolsym classify signal.csv
toolsym symmetry MASKS_DIR --n-edges 2
```

## DATA root

ToolSym never hardcodes paths. The location of your dataset is resolved
in this order:

1. The `--data-root` flag (CLI) or the "Browse" button (GUI).
2. `TOOLSYM_DATA` environment variable.
3. `~/.toolsym/data/` (created on first run).

Both apps remember the last picked folder via `QSettings`.

## Library example

```python
from toolsym.io.masks import load_mask_sequence
from toolsym.signal import (
    area_signal_from_masks,
    classify_segment_consistency,
    classify_sinusoidal_distances,
    find_segments,
    fit_segment_sinusoidals,
    pairwise_coefficient_distances,
    preprocess_signal,
)

masks, _ = load_mask_sequence("/path/to/tool007/masks")
signal = area_signal_from_masks(masks, roi_height=350)
signal, angles = preprocess_signal(signal)
segments = find_segments(signal)
consistency = classify_segment_consistency(segments.segment_sizes_deg)
if not consistency.intact:
    print("Fractured (segment-size deviation)")
else:
    fits = fit_segment_sinusoidals(signal, None, segments.n_segments)
    distances = pairwise_coefficient_distances(fits)
    print(classify_sinusoidal_distances(distances))
```

For the two-edge fracture case (where the hybrid classifier doesn't
self-calibrate), use the symmetry path:

```python
from toolsym.symmetry import mean_absolute_difference, three_zone_classify

d_bar = mean_absolute_difference(masks, n_edges=2)
print(three_zone_classify(d_bar))
```

## Citing

If ToolSym helps your work, please cite the package (`CITATION.cff`) and
the underlying papers — both are listed in `CITATION.cff` and importable
via GitHub's "Cite this repository" button.

## Roadmap

* **v0.1** — library + analysis-app skeleton + sim-app skeleton, CI on Win/Mac/Linux, PyPI.
* **v0.2** — full PySide6 port of the rich legacy UIs (live previews, plot exports, batch runners) for both apps; PyInstaller `.exe` bundles attached to GitHub releases.
* **v0.3** — `toolsym.ml`: deep shape prior trained on the simulation pipeline, Sim2Real evaluation on ELTE-TCM-46k, model published to Hugging Face.

See `CHANGELOG.md`, `MIGRATION.md`, and `CONTRIBUTING.md` for details.

## License

Apache-2.0. See `LICENSE`.
