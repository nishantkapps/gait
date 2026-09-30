"""Helpers for the marker-map UI: OpenSim targets + C3D source labels."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from gait.config import load_yaml

_SKIP_SUFFIX = ("Ground", "Joint")
_SKIP_NAMES = frozenset({"MidASIS", "MidPSIS", "L_HJC", "R_HJC"})


def strip_marker_prefix(name: str) -> str:
    return name.split(":", 1)[-1]


def opensim_marker_names(markerset_path: str | Path) -> list[str]:
    """Marker names from an OpenSim MarkerSet XML (walk markerset)."""
    root = ET.parse(str(markerset_path)).getroot()
    names: list[str] = []
    for el in root.iter("Marker"):
        name = el.get("name")
        if not name:
            continue
        if name in _SKIP_NAMES or name.endswith(_SKIP_SUFFIX):
            continue
        names.append(name)
    return sorted(set(names))


def c3d_marker_labels(c3d_path: str | Path) -> list[str]:
    """Point labels from a C3D, subject prefix stripped, sorted unique."""
    from ezc3d import c3d

    raw = c3d(str(c3d_path))
    labels = [strip_marker_prefix(str(x)) for x in raw["parameters"]["POINT"]["LABELS"]["value"]]
    # Drop empty / purely numeric unlabeled markers from the picker noise.
    cleaned = []
    for name in labels:
        if not name or re.match(r"^\*\d+$", name):
            continue
        cleaned.append(name)
    return sorted(set(cleaned))


def default_marker_map(map_path: str | Path) -> dict:
    return load_yaml(map_path)


def marker_map_to_yaml(markers: dict[str, str], average_markers: dict | None = None) -> str:
    lines = [
        "# Marker map edited in the gait UI",
        "drop_unmapped: true",
        "",
        "markers:",
    ]
    for src, dest in sorted((markers or {}).items(), key=lambda kv: (kv[1], kv[0])):
        if not src or not dest:
            continue
        lines.append(f"  {src}: {dest}")
    av = average_markers or {}
    if av:
        lines.append("")
        lines.append("average_markers:")
        for dest, spec in sorted(av.items()):
            sources = spec.get("sources") if isinstance(spec, dict) else spec
            sources = [s for s in (sources or []) if s]
            if not sources:
                continue
            lines.append(f"  {dest}:")
            lines.append(f"    sources: [{', '.join(sources)}]")
    return "\n".join(lines) + "\n"
