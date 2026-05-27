"""Backwards-compatibility shim.

The centerline is currently computed inside
:mod:`toolsym.geometry.alignment` (see :class:`TiltCenterline`). This
module re-exports the dataclass for callers expecting a separate
``centerline`` module.
"""

from toolsym.geometry.alignment import TiltCenterline

__all__ = ["TiltCenterline"]
