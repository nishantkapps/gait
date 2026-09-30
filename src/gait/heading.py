"""Normalize walking heading so progress is +X in the OpenSim frame.

Reverse walks (lab −X) get a 180° yaw about Y applied to markers and forces.
Static / little-progress trials are left unchanged.
"""

from __future__ import annotations

import numpy as np

from gait.schema import TrialRecord

# Minimum |Δx| of the pelvis track to treat the trial as a walk (meters).
_MIN_WALK_PROGRESS_M = 0.5

# 180° about vertical (Y): (x, y, z) -> (−x, y, −z)
_YAW180 = np.diag([-1.0, 1.0, -1.0])


def _pelvis_track(trial: TrialRecord) -> np.ndarray | None:
    """Return (T, 3) mid-pelvis path from ASIS pair, else S2, else None."""
    m = trial.markers
    if "L.ASIS" in m and "R.ASIS" in m:
        return 0.5 * (np.asarray(m["L.ASIS"], dtype=float) + np.asarray(m["R.ASIS"], dtype=float))
    if "S2" in m:
        return np.asarray(m["S2"], dtype=float)
    return None


def walk_progress_x(trial: TrialRecord) -> float | None:
    """Signed Δx of mid-pelvis (last − first). None if no pelvis markers."""
    track = _pelvis_track(trial)
    if track is None or len(track) < 2:
        return None
    return float(track[-1, 0] - track[0, 0])


def needs_yaw180(trial: TrialRecord) -> bool:
    dx = walk_progress_x(trial)
    if dx is None:
        return False
    return dx < -_MIN_WALK_PROGRESS_M


def _rotate_xyz(arr: np.ndarray) -> np.ndarray:
    pts = np.asarray(arr, dtype=float)
    return pts @ _YAW180.T


def apply_yaw180(trial: TrialRecord) -> TrialRecord:
    """Rotate markers and force plate series 180° about Y in place."""
    trial.markers = {name: _rotate_xyz(arr) for name, arr in trial.markers.items()}
    for plate in trial.forces:
        plate.force = _rotate_xyz(plate.force)
        plate.cop = _rotate_xyz(plate.cop)
        plate.moment = _rotate_xyz(plate.moment)
    return trial


def normalize_walking_heading(trial: TrialRecord) -> bool:
    """If the trial walks −X, yaw 180° so progress is +X. Returns True if rotated."""
    if not needs_yaw180(trial):
        return False
    apply_yaw180(trial)
    return True
