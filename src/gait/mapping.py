"""Rename source markers to model marker names via YAML map."""

from __future__ import annotations

import numpy as np

from gait.schema import TrialRecord


def apply_marker_map(
    trial: TrialRecord,
    name_map: dict[str, str],
    drop_unmapped: bool = False,
) -> TrialRecord:
    mapped: dict[str, np.ndarray] = {}
    for src, arr in trial.markers.items():
        base = src.split(":", 1)[-1]
        if base not in name_map:
            if drop_unmapped:
                continue
            mapped[base] = arr
            continue
        mapped[name_map[base]] = arr
    trial.markers = mapped
    return trial


def apply_marker_map_file(trial: TrialRecord, marker_cfg: dict) -> TrialRecord:
    return apply_marker_map(
        trial,
        dict(marker_cfg["markers"]),
        drop_unmapped=bool(marker_cfg.get("drop_unmapped", False)),
    )
