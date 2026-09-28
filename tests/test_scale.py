"""Test: OpenSim Scale only (needs model + scale_setup.xml)."""

from __future__ import annotations

from pathlib import Path

from gait.opensim_scale_ik_id import run_scale
from tests.common import out_dir, parse_config_source


def main() -> None:
    cfg, _source = parse_config_source("Test Scale")
    osim = cfg["opensim"]
    scaled = out_dir(cfg) / osim["outputs"]["scaled_model"]
    run_scale(osim["generic_model"], osim["scale_setup"], str(scaled))
    print("wrote", scaled, "exists=", Path(scaled).exists())
    print("OK")


if __name__ == "__main__":
    main()
