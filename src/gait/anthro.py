"""Read subject mass/height from Vicon C3D PROCESSING (or .mp fallback)."""

from __future__ import annotations

from pathlib import Path

from ezc3d import c3d


def anthro_from_c3d(path: str | Path) -> dict:
    """Return {mass_kg, height_m} when present in C3D PROCESSING group."""
    raw = c3d(str(path))
    proc = raw["parameters"].get("PROCESSING")
    if not proc:
        return {}
    out: dict = {}
    if "Bodymass" in proc:
        out["mass_kg"] = float(proc["Bodymass"]["value"][0])
    if "Height" in proc:
        h = float(proc["Height"]["value"][0])
        out["height_m"] = h / 1000.0 if h > 3.0 else h
    return out


def anthro_from_subject_dir(c3d_paths: list[Path]) -> dict:
    """First C3D that has Bodymass/Height wins (walk trials usually do)."""
    for path in c3d_paths:
        info = anthro_from_c3d(path)
        if "mass_kg" in info and "height_m" in info:
            return info
    for path in c3d_paths:
        info = anthro_from_c3d(path)
        if info:
            return info
    return {}
