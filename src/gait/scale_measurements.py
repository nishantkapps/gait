"""Build OpenSim Scale MeasurementSet entries from markers present in a static TRC.

Recipes are anatomical defaults (not subject-specific hand tuning). A measurement
is emitted only when both markers exist in the TRC. Foot segments are intentionally
omitted: Heel→Toe under-scales calcn/toes for PiG (~0.76 here) and fights sole
offsets; heel/toe stay at generic size with fixed markerset offsets.
"""

from __future__ import annotations

from pathlib import Path

# (name, marker_a, marker_b, bodies, optional axes)
_RECIPES: list[tuple] = [
    ("pelvis", "L.ASIS", "R.ASIS", ["pelvis"], ["X", "Z"]),
    ("thigh_r", "R.ASIS", "R.Knee", ["femur_r", "patella_r"], None),
    ("thigh_l", "L.ASIS", "L.Knee", ["femur_l", "patella_l"], None),
    ("shank_r", "R.Knee", "R.Ankle", ["tibia_r", "talus_r"], None),
    ("shank_l", "L.Knee", "L.Ankle", ["tibia_l", "talus_l"], None),
    ("torso", "MidClavicle", "Head", ["torso"], None),
]


def trc_marker_names(trc_path: str | Path) -> set[str]:
    lines = Path(trc_path).read_text(encoding="utf-8").splitlines()
    for line in lines:
        parts = line.split("\t")
        if parts and parts[0] in ("Frame#", "Frame #"):
            return {p for p in parts[2:] if p}
    raise ValueError(f"No Frame# marker header in {trc_path}")


def measurements_from_trc(trc_path: str | Path) -> list[dict]:
    """Return Scale measurement dicts for markers present in the static TRC."""
    present = trc_marker_names(trc_path)
    out: list[dict] = []
    for name, m1, m2, bodies, axes in _RECIPES:
        if m1 not in present or m2 not in present:
            continue
        item: dict = {"name": name, "markers": [m1, m2], "bodies": list(bodies)}
        if axes:
            item["axes"] = list(axes)
        out.append(item)
    return out
