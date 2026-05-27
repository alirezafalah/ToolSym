"""Centralised noise + augmentation presets.

These were previously duplicated between ``noise_injector.py``,
``augmentor.py`` and ``simulation_gui.py``. Hosting them here means the
GUI tabs and CLI flags share one source of truth.

The values come from the rig and noise observations described in the
ECCV-submitted shape-prior paper (Falah et al. 2026).
"""

from __future__ import annotations

from typing import Any, TypedDict

__all__ = [
    "AUGMENT_PRESETS",
    "AugmentPreset",
    "NOISE_PRESETS",
    "NoisePreset",
]


class NoisePreset(TypedDict):
    """Configuration for one noise preset.

    Keys mirror ``noise_injector.plan_dent_events`` parameter names.
    """

    n_events: int
    frame_span_min: int
    frame_span_max: int
    dent_span_min: int
    dent_span_max: int
    peak_depth: float
    seed: int | None


NOISE_PRESETS: dict[str, NoisePreset] = {
    "default": {
        "n_events": 1,
        "frame_span_min": 10,
        "frame_span_max": 20,
        "dent_span_min": 250,
        "dent_span_max": 500,
        "peak_depth": 3.5,
        "seed": None,
    },
    "moderate": {
        "n_events": 2,
        "frame_span_min": 10,
        "frame_span_max": 20,
        "dent_span_min": 250,
        "dent_span_max": 500,
        "peak_depth": 5.0,
        "seed": None,
    },
    "aggressive": {
        "n_events": 3,
        "frame_span_min": 10,
        "frame_span_max": 20,
        "dent_span_min": 300,
        "dent_span_max": 600,
        "peak_depth": 4.0,
        "seed": None,
    },
}


class AugmentPreset(TypedDict):
    """Non-uniform CAD scale factors (sx, sy, sz)."""

    label: str
    scale_x: float
    scale_y: float
    scale_z: float


AUGMENT_PRESETS: dict[str, AugmentPreset] = {
    "longer_flutes": {
        "label": "Longer Flutes",
        "scale_x": 1.00,
        "scale_y": 1.00,
        "scale_z": 1.10,
    },
    "thinner_drill": {
        "label": "Thinner Drill",
        "scale_x": 0.90,
        "scale_y": 0.90,
        "scale_z": 1.00,
    },
    "wider_drill": {
        "label": "Wider Drill",
        "scale_x": 1.10,
        "scale_y": 1.10,
        "scale_z": 1.00,
    },
    "long_and_thin": {
        "label": "Long & Thin",
        "scale_x": 0.92,
        "scale_y": 0.92,
        "scale_z": 1.08,
    },
    "short_and_wide": {
        "label": "Short & Wide",
        "scale_x": 1.08,
        "scale_y": 1.08,
        "scale_z": 0.92,
    },
    "uniform_upscale": {
        "label": "Uniform Up-scale",
        "scale_x": 1.05,
        "scale_y": 1.05,
        "scale_z": 1.05,
    },
}


def get_noise_preset(name: str) -> NoisePreset:
    key = name.strip().lower()
    if key not in NOISE_PRESETS:
        raise KeyError(f"unknown noise preset: {name!r}")
    return dict(NOISE_PRESETS[key])  # type: ignore[return-value]


def get_augment_preset(name: str) -> AugmentPreset:
    key = name.strip().lower().replace(" ", "_")
    if key not in AUGMENT_PRESETS:
        raise KeyError(f"unknown augment preset: {name!r}")
    return dict(AUGMENT_PRESETS[key])  # type: ignore[return-value]


def to_dict(preset: Any) -> dict[str, Any]:
    """Helper for serialising a preset (TypedDict) to a plain dict."""
    return dict(preset)
