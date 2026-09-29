"""Rename source markers to model marker names via YAML map."""

from __future__ import annotations

import numpy as np

from gait.schema import TrialRecord


def _strip_prefix(name: str) -> str:
    return name.split(":", 1)[-1]


def apply_marker_map(
    trial: TrialRecord,
    name_map: dict[str, str],
    drop_unmapped: bool = False,
    average_markers: dict | None = None,
) -> TrialRecord:
    raw: dict[str, np.ndarray] = {
        _strip_prefix(src): arr for src, arr in trial.markers.items()
    }
    mapped: dict[str, np.ndarray] = {}

    for dest, spec in (average_markers or {}).items():
        sources = list(spec.get("sources") or [])
        arrs = [raw[s] for s in sources if s in raw]
        if not arrs:
            continue
        stacked = np.stack(arrs, axis=0)
        mapped[str(dest)] = np.nanmean(stacked, axis=0)

    for src, arr in raw.items():
        if src not in name_map:
            if drop_unmapped:
                continue
            mapped[src] = arr
            continue
        mapped[name_map[src]] = arr

    trial.markers = mapped
    return trial


def apply_marker_map_file(trial: TrialRecord, marker_cfg: dict) -> TrialRecord:
    return apply_marker_map(
        trial,
        dict(marker_cfg.get("markers") or {}),
        drop_unmapped=bool(marker_cfg.get("drop_unmapped", False)),
        average_markers=marker_cfg.get("average_markers"),
    )
