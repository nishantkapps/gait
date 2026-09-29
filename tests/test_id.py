"""Test: OpenSim ID only (needs scaled.osim + id_setup.xml + GRF)."""

from __future__ import annotations

from pathlib import Path

from gait.opensim_scale_ik_id import run_id
from tests.common import out_dir, parse_config_source


def main() -> None:
    cfg, _source = parse_config_source("Test ID")
    osim = cfg["opensim"]
    out = out_dir(cfg)
    scaled = out / osim["outputs"]["scaled_model"]
    id_sto = out / osim["outputs"]["id_sto"]
    if not scaled.exists():
        raise SystemExit(f"Missing {scaled}; run test_scale.py first")
    run_id(
        str(scaled),
        osim["id_setup"],
        str(id_sto),
        str(out / osim["outputs"]["ik_mot"]),
        str(out / osim["outputs"]["external_loads"]),
    )
    print("wrote", id_sto, "exists=", Path(id_sto).exists())
    print("OK")


if __name__ == "__main__":
    main()
