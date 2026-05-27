# Architecture

ToolSym ships two desktop applications backed by one shared library.

## Library boundary (the hard rule)

```
┌────────────────────────────────────────────────────────────┐
│  apps/toolsym_tcm/    apps/toolsym_sim/                    │  ← Qt allowed
│       │                    │                               │
│       ▼                    ▼                               │
│  ┌──────────────────────────────────────────────┐          │
│  │ toolsym/widgets/  (the ONLY Qt-aware module) │          │
│  └──────────────────────────────────────────────┘          │
│       │                                                    │
│       ▼                                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ toolsym/{config,io,signal,geometry,symmetry,…}      │  │  ← Qt forbidden
│  │  — pure functions, type-hinted, headless, testable   │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

The library never imports Qt. This is what lets you:

* Run any algorithm from a notebook.
* Run the entire test suite in headless CI on Linux containers.
* Swap PySide6 for a future Web UI without touching algorithm code.

## Data flow (analysis app)

```
DATA folder (binary masks)
   │
   ▼
toolsym.io.masks.load_mask_sequence
   │
   ├── toolsym.geometry.build_master_mask
   │   └── toolsym.geometry.estimate_tilt_and_centerline → rotate_to_axis
   │
   ├── toolsym.signal.area_signal_from_masks (full pipeline)
   │   → preprocess → smooth → find_peaks → fit → classify
   │
   ├── toolsym.symmetry.mean_absolute_difference (2-edge tools)
   │   → three_zone_classify
   │
   └── toolsym.reconstruction.carve_visual_hull → toolsym.io.voxels.save
```

## Data flow (simulation app)

```
CAD STEP/STL
   │
   ├── toolsym.simulation.augmentor (optional non-uniform scaling)
   │
   ├── toolsym.simulation.render_engine
   │   → 360 binary masks per tool
   │   └── toolsym.simulation.noise_injector
   │       → noisy mask variants for Sim2Real training
   │
   └── toolsym.reconstruction.cad_voxelizer
       → 128³ ground-truth voxel NPZ
```

## Why two apps?

Different audiences with disjoint workflows. A factory operator running
the analysis app doesn't need a CAD voxelizer; a researcher generating
training data doesn't need a per-tool fracture diagnostic. Two focused
apps beat one cluttered mega-app — and both share `toolsym.widgets` so
they look and feel the same.

## Optional dependencies

| Group | Used by | Heavy? |
|-------|---------|--------|
| (core) | TCM app + signal/symmetry library | No |
| `simulation` | sim app + cad_voxelizer | **Yes** (pyvista, vtk, cadquery) |
| `gpu` | visual_hull OpenCL backend (auto-fallback to CPU) | Medium (pyopencl + drivers) |
| `ml` | future deep shape prior | **Yes** (torch) |

Users only install what they need.
