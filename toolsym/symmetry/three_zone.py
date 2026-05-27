"""Three-zone thresholding (symmetry paper §4.1).

Translates the continuous ``D̄`` metric into one of three diagnostic
zones:

* **Safe** (``D̄ ≤ T_noise``) — tool is functional.
* **Warning** (``T_noise < D̄ < T_fracture``) — flagged for re-inspection
  or alternative segmentation. The paper observed that bright-coated
  tools sit in this zone because of segmentation failures, not actual
  fracture.
* **Fracture** (``D̄ ≥ T_fracture``) — confident classification, halt
  the machine.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = ["Zone", "ThreeZoneConfig", "ThreeZoneClassification", "three_zone_classify"]


class Zone(str, Enum):
    SAFE = "safe"
    WARNING = "warning"
    FRACTURE = "fracture"


@dataclass(frozen=True, slots=True)
class ThreeZoneConfig:
    """Thresholds for the three zones.

    Defaults reflect the paper's empirical values on the ELTE-TCM-46k
    subset (16 two-edge specimens). Tune as larger datasets arrive.
    """

    t_noise: float = 1500.0
    t_fracture: float = 3500.0


@dataclass(frozen=True, slots=True)
class ThreeZoneClassification:
    zone: Zone
    d_bar: float
    config: ThreeZoneConfig


def three_zone_classify(
    d_bar: float, config: ThreeZoneConfig | None = None
) -> ThreeZoneClassification:
    """Classify a ``D̄`` value into one of three zones."""
    cfg = config or ThreeZoneConfig()
    if cfg.t_fracture < cfg.t_noise:
        raise ValueError(
            f"t_fracture ({cfg.t_fracture}) must be ≥ t_noise ({cfg.t_noise})"
        )
    if d_bar <= cfg.t_noise:
        zone = Zone.SAFE
    elif d_bar >= cfg.t_fracture:
        zone = Zone.FRACTURE
    else:
        zone = Zone.WARNING
    return ThreeZoneClassification(zone=zone, d_bar=d_bar, config=cfg)
