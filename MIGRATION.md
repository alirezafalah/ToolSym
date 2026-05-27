# Migration guide: legacy repos → ToolSym

This document maps every module / script in the two legacy repos to its
home in the new `toolsym` package, so you can resume your existing
workflows without searching.

## High-level

| Legacy repo | New location |
|-------------|--------------|
| `Tool_Condition_Monitoring/image_to_signal/` | `toolsym.signal.*` + `apps/toolsym_tcm/tabs/image_to_signal.py` |
| `Tool_Condition_Monitoring/symmetry_analysis_and_master_masks/` | `toolsym.geometry.*`, `toolsym.symmetry.*` + `apps/toolsym_tcm/tabs/symmetry.py` |
| `Tool_Condition_Monitoring/3D_reconstruction/` | `toolsym.reconstruction.visual_hull` + `apps/toolsym_tcm/tabs/visual_hull.py` |
| `Tool_Condition_Monitoring/tool_profile_viz/` | `apps/toolsym_tcm/tabs/dataset_browser.py` |
| `Tool_Condition_Monitoring/mask_refiner/` | **Out of scope.** Lives outside ToolSym (per spec). |
| `Tool_Condition_Monitoring/old/` | **Deleted.** |
| `Tool_Condition_Monitoring/signal_processing/` | Likely duplicated by `image_to_signal`; verify and delete. |
| `Tool_Condition_Monitoring/paper_figure_generator.py` | TODO: `apps/toolsym_tcm/tabs/figures/` |
| `CNC-Tool-CAD-to-Mask-Simulation/render_engine.py` | `toolsym.simulation.render_engine` |
| `CNC-Tool-CAD-to-Mask-Simulation/noise_injector.py` | `toolsym.simulation.noise_injector` |
| `CNC-Tool-CAD-to-Mask-Simulation/augmentor.py` | `toolsym.simulation.augmentor` |
| `CNC-Tool-CAD-to-Mask-Simulation/voxelizer.py` | `toolsym.reconstruction.cad_voxelizer` |
| `CNC-Tool-CAD-to-Mask-Simulation/voxel_grid_spec.json` | `toolsym/data/voxel_grid_spec.json` |
| `CNC-Tool-CAD-to-Mask-Simulation/simulation_gui.py` | `apps/toolsym_sim/main_window.py` + per-tab modules under `apps/toolsym_sim/tabs/` |

## Algorithm mapping (Tool_Condition_Monitoring/image_to_signal)

| Legacy file or function | New library symbol |
|-------------------------|--------------------|
| `step3_analyze_and_plot.py: analyze_roi(...)` | `toolsym.signal.area_signal_from_masks` |
| `step4_process_and_plot.py: scale + shift` | `toolsym.signal.preprocess_signal` |
| `utils/optimized_processing.py: roi white pixels` | `toolsym.signal.white_pixels_in_roi` |
| Savitzky-Golay smoothing (inline) | `toolsym.signal.savgol_circular` |
| `find_peaks` invocation (inline) | `toolsym.signal.find_segments` |
| Segment-size check (inline) | `toolsym.signal.classify_segment_consistency` |
| Sinusoidal fit (inline) | `toolsym.signal.fit_segment_sinusoidals` |
| Pairwise distance + threshold (inline) | `toolsym.signal.pairwise_coefficient_distances` + `classify_sinusoidal_distances` |
| `dashboard_generator.py` | TODO: `apps/toolsym_tcm/tabs/figures/` (v0.2) |
| `find360.py`, `rename_by_angle.py` | Out of scope helpers; ship as separate `scripts/` in v0.2. |
| `step1_blur_and_rename.py`, `step2_generate_masks.py` | Pipeline pre-steps; will become part of the "Capture" tab in v0.2. |

## Algorithm mapping (Tool_Condition_Monitoring/symmetry_analysis_and_master_masks)

| Legacy file | New library symbol |
|-------------|--------------------|
| `phase_shift_analysis.py` | `toolsym.symmetry.phase_shift` (`phase_shift_metric`, `mean_absolute_difference`) |
| `perspective/build_master_masks_all_two_edge_tools.py` | `toolsym.geometry.master_mask.build_master_mask` |
| `perspective/find_optimal_offset.py`, `fix_perspective.py` | `toolsym.geometry.alignment.estimate_tilt_and_centerline`, `rotate_to_axis` |
| `perspective/roi_figure_creator.py` | `toolsym.geometry.roi.dynamic_roi`, `split_left_right` |
| `half_tool_analysis_gui.py` | `apps/toolsym_tcm/tabs/symmetry.py` (skeleton; full UI port in v0.2) |
| `run_perspective_tools_gui.py` | `apps/toolsym_tcm/tabs/symmetry.py` (combined into one tab) |
| `paper_figures/` scripts | TODO: `apps/toolsym_tcm/tabs/figures/` (v0.2) |

## Algorithm mapping (Tool_Condition_Monitoring/3D_reconstruction)

| Legacy file | New library symbol |
|-------------|--------------------|
| `visual_hull_engine.py: run_visual_hull` | `toolsym.reconstruction.carve_visual_hull` |
| `visual_hull_engine.py: OpenCL kernel` | `toolsym.reconstruction.visual_hull._carve_opencl` |
| `visual_hull.py` | (CLI) → `toolsym.cli` could grow a `visual-hull` subcommand in v0.2. |
| `visual_hull_gui.py` | `apps/toolsym_tcm/tabs/visual_hull.py` |
| `voxel_grid_spec.json` | `toolsym/data/voxel_grid_spec.json` (now bundled in the wheel) |

## Algorithm mapping (CNC-Tool-CAD-to-Mask-Simulation)

These modules were the cleanest of the bunch and are copied verbatim
(import paths only changed):

| Legacy file | New file |
|-------------|----------|
| `render_engine.py` | `toolsym/simulation/render_engine.py` |
| `noise_injector.py` | `toolsym/simulation/noise_injector.py` |
| `augmentor.py` | `toolsym/simulation/augmentor.py` |
| `voxelizer.py` | `toolsym/reconstruction/cad_voxelizer.py` |
| `NOISE_PRESETS`, `AUGMENT_PRESETS` (scattered) | `toolsym/simulation/presets.py` (centralised) |
| `simulation_gui.py` | `apps/toolsym_sim/main_window.py` + `apps/toolsym_sim/tabs/{render,noise,augment,voxelize}.py` (skeleton in v0.1; full port v0.2) |

## What changed beyond moving files

* **Path resolution.** All hardcoded `C:\Users\uik07077\...` and
  `c:\Users\alrfa\...` paths are removed. `toolsym.config.data_root()`
  is the single resolver, honouring `--data-root` → `TOOLSYM_DATA` env
  → `~/.toolsym/data`.
* **No more sibling-directory assumption.** The sim GUI used to default
  to `../Tool_Condition_Monitoring/3D_reconstruction/voxel_grid_spec.json`;
  the spec is now bundled inside the wheel at
  `toolsym/data/voxel_grid_spec.json` and loaded via
  `toolsym.config.load_voxel_grid_spec()`.
* **Algorithm modules are GUI-free.** The hard rule going forward is
  that nothing under `toolsym/` (except `widgets/`) imports Qt. This
  unblocks notebook use, CI testing, and alternate front-ends.
* **One licence, one packaging story.** Apache-2.0, `pyproject.toml`,
  optional extras for the heavy 3D dependencies, console scripts
  registered (`toolsym-tcm`, `toolsym-sim`, `toolsym`).
* **CI + pre-commit.** Ruff + mypy + pytest run on Windows/macOS/Linux
  on every PR; pre-commit hooks enforce locally.
* **Tests with synthetic fixtures.** No need to commit the real
  dataset; pure-algorithm tests use procedurally-generated 4- and
  3-edge signals that the algorithms ought to handle perfectly.

## Recommended migration order for downstream users

If you have scripts that import the legacy modules:

1. `pip install toolsym` in the same environment.
2. Replace `from image_to_signal.something import X` with
   `from toolsym.signal import X` (see the mapping above).
3. Replace any hardcoded DATA path with `toolsym.config.data_root()`.
4. The two legacy GUIs (`gui_main.py`, `simulation_gui.py`) keep
   working until you uninstall the old repos; they can coexist with
   the ToolSym apps while you migrate workflows over.
