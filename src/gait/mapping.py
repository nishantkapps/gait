"""Rename source markers to model marker names via YAML map."""

from __future__ import annotations

import numpy as np

from gait.schema import TrialRecord


def apply_marker_map(trial: TrialRecord, name_map: dict[str, str]) -> TrialRecord:
    mapped: dict[str, np.ndarray] = {}
    for src, arr in trial.markers.items():
        dst = name_map.get(src, src)
        mapped[dst] = arr
    trial.markers = mapped
    return trial
