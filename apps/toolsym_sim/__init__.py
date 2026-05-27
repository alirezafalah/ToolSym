"""ToolSym Sim — synthetic dataset generation app.

Tabs:

* **Render** — CAD → 360 binary masks.
* **Noise** — temporal cosine dent noise injection.
* **Augment** — non-uniform CAD scaling.
* **Voxelize** — CAD → 128³ ground-truth voxel grid.

The full UI is the existing ``simulation_gui.py`` from
``CNC-Tool-CAD-to-Mask-Simulation``, due to be split into per-tab
modules under ``tabs/``. The skeleton ships placeholders that surface
the underlying CLI for now.
"""
