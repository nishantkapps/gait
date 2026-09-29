"""Allocate numbered run folders under outputs/ and logs/."""

from __future__ import annotations

import re
from pathlib import Path

_RUN_RE = re.compile(r"^run_(\d+)$")


def latest_run_number(*roots: Path) -> int:
    """Highest run_N across the given roots (0 if none)."""
    latest = 0
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.iterdir():
            if not path.is_dir():
                continue
            m = _RUN_RE.match(path.name)
            if m:
                latest = max(latest, int(m.group(1)))
    return latest


def next_run_number(*roots: Path) -> int:
    return latest_run_number(*roots) + 1


def run_name(n: int) -> str:
    return f"run_{n:03d}"


def allocate_run(outputs_root: Path, logs_root: Path) -> tuple[int, Path, Path]:
    """Create the next outputs/run_XXX and logs/run_XXX dirs."""
    n = next_run_number(outputs_root, logs_root)
    name = run_name(n)
    out_dir = outputs_root / name
    log_dir = logs_root / name
    out_dir.mkdir(parents=True, exist_ok=False)
    log_dir.mkdir(parents=True, exist_ok=False)
    return n, out_dir, log_dir
