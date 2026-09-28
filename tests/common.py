"""Shared CLI for piece-wise tests: --config and --source."""

from __future__ import annotations

import argparse
from pathlib import Path

from gait.config import load_yaml


def parse_config_source(description: str):
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--config", required=True)
    p.add_argument("--source", required=True, help="Trial file (e.g. .c3d)")
    args = p.parse_args()
    cfg = load_yaml(args.config)
    return cfg, Path(args.source)


def out_dir(cfg: dict) -> Path:
    path = Path(cfg["paths"]["processed_dir"]) / cfg["subject"]["subject_id"]
    path.mkdir(parents=True, exist_ok=True)
    return path
