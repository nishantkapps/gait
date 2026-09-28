"""Test: write OpenSim .trc from C3D trial."""

from __future__ import annotations

from gait.adapters.c3d_adapter import C3dAdapter
from gait.config import load_yaml
from gait.mapping import apply_marker_map
from gait.writers.trc import write_trc
from tests.common import out_dir, parse_config_source


def main() -> None:
    cfg, source = parse_config_source("Test TRC writer")
    trial = C3dAdapter().load(str(source), cfg)
    trial = apply_marker_map(trial, load_yaml(cfg["paths"]["marker_map"])["markers"])
    path = out_dir(cfg) / cfg["opensim"]["outputs"]["trc"]
    write_trc(trial, path, cfg["units"]["trc_output"])
    print("wrote", path, "bytes=", path.stat().st_size)
    print("OK")


if __name__ == "__main__":
    main()
