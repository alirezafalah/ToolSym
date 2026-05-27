"""3D reconstruction: visual hull from real masks and ground-truth
voxelisation from CAD.

Two carvers, one grid:

* :func:`carve_visual_hull` carves the 128³ occupancy grid from a tool's
  360 real-world binary masks (Shape-from-Silhouette). This is the
  Sim2Real test input for the deep shape prior.
* :func:`voxelise_cad` builds the ground-truth grid from a STEP / STL
  CAD model via ``vtkSelectEnclosedPoints``. Used to render the training
  set the prior is fitted on.

Both produce identical schemas (boolean grid + bounds + shape), so the
prior trained on the second can be evaluated directly on the first.
"""

from toolsym.reconstruction.visual_hull import (
    CarverConfig,
    HullResult,
    carve_visual_hull,
)

__all__ = [
    "CarverConfig",
    "HullResult",
    "carve_visual_hull",
]

try:
    from toolsym.reconstruction.cad_voxelizer import (  # noqa: F401
        VoxelisationResult,
        voxelise_cad,
    )

    __all__.extend(["VoxelisationResult", "voxelise_cad"])
except ImportError:
    # cad_voxelizer requires the [simulation] extras (pyvista, vtk).
    pass
