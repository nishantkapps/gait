"""Discover static and dynamic C3Ds in a subject directory (globs from config)."""

from __future__ import annotations

from pathlib import Path


def discover_c3ds(input_dir: str | Path, cfg: dict) -> tuple[Path, list[Path]]:
    root = Path(input_dir)
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")
    sd = cfg["subject_dir"]
    static = sorted(root.glob(sd["static_glob"]))
    dynamic = sorted(root.glob(sd["dynamic_glob"]))
    if len(static) != 1:
        raise FileNotFoundError(
            f"Need exactly 1 static C3D matching {sd['static_glob']!r} in {root}, "
            f"found {len(static)}: {[p.name for p in static]}"
        )
    if not dynamic:
        raise FileNotFoundError(
            f"No dynamic C3Ds matching {sd['dynamic_glob']!r} in {root}"
        )
    return static[0], dynamic
