"""Test: OpenSim IK only (needs scaled.osim + ik_setup.xml + markers.trc)."""

from __future__ import annotations

from pathlib import Path

from gait.opensim_scale_ik_id import run_ik
from tests.common import out_dir, parse_config_source


def main() -> None:
    cfg, _source = parse_config_source("Test IK")
    osim = cfg["opensim"]
    out = out_dir(cfg)
    scaled = out / osim["outputs"]["scaled_model"]
    ik_mot = out / osim["outputs"]["ik_mot"]
    if not scaled.exists():
        raise SystemExit(f"Missing {scaled}; run test_scale.py first")
    run_ik(str(scaled), osim["ik_setup"], str(ik_mot))
    print("wrote", ik_mot, "exists=", Path(ik_mot).exists())
    print("OK")


if __name__ == "__main__":
    main()
