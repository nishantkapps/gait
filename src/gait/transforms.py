"""Axis / unit helpers driven by config."""

from __future__ import annotations

import numpy as np


def length_scale(unit: str) -> float:
    if unit == "mm":
        return 0.001
    if unit == "m":
        return 1.0
    raise ValueError(f"Unsupported length unit: {unit}")


def apply_rotation(points: np.ndarray, matrix_3x3: list[list[float]]) -> np.ndarray:
    r = np.asarray(matrix_3x3, dtype=float)
    return points @ r.T
