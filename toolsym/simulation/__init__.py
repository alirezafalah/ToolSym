"""Synthetic dataset generation pipeline.

These modules were originally distributed in the standalone repo
``CNC-Tool-CAD-to-Mask-Simulation``. They are reproduced here with
minimal modifications so the existing CAD → mask → noise → augment
workflow keeps working.

Requires the ``[simulation]`` extras (``pyvista``, ``vtk``, ``cadquery``).

Submodules
----------
* :mod:`toolsym.simulation.render_engine` — CAD → 360 binary masks
* :mod:`toolsym.simulation.noise_injector` — temporal cosine dent noise
* :mod:`toolsym.simulation.augmentor` — non-uniform CAD scaling
* :mod:`toolsym.simulation.presets` — bundled noise + augment presets
"""

from toolsym.simulation.presets import AUGMENT_PRESETS, NOISE_PRESETS

__all__ = ["AUGMENT_PRESETS", "NOISE_PRESETS"]

# Heavy imports (pyvista, vtk) are kept inside submodules so importing
# the package is cheap. The submodules raise ImportError on use if the
# `[simulation]` extras aren't installed.
