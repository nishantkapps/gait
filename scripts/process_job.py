"""Process one inbox job: C3D + YAML → TRC/GRF (OpenSim optional)."""

from __future__ import annotations

import argparse
from pathlib import Path

from gait.adapters.c3d_adapter import C3dAdapter
from gait.config import load_yaml
from gait.mapping import apply_marker_map
from gait.opensim_scale_ik_id import run_id, run_ik, run_scale
from gait.writers.grf import write_external_loads_xml, write_grf_mot
from gait.writers.trc import write_trc


def main() -> None:
    args = _parse()
    cfg = load_yaml(args.config)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    names = cfg["opensim"]["outputs"]
    trial = C3dAdapter().load(args.source, cfg)
    trial = apply_marker_map(trial, load_yaml(cfg["paths"]["marker_map"])["markers"])
    write_trc(trial, out / names["trc"], cfg["units"]["trc_output"])
    if trial.forces:
        write_grf_mot(trial, out / names["grf_mot"])
        write_external_loads_xml(
            trial,
            str(out / names["grf_mot"]),
            out / names["external_loads"],
            cfg["opensim"]["ground_body"],
        )
    if cfg.get("opensim", {}).get("enabled"):
        _opensim(cfg, out)


def _opensim(cfg: dict, out: Path) -> None:
    o = cfg["opensim"]
    n = o["outputs"]
    scaled = out / n["scaled_model"]
    run_scale(o["generic_model"], o["scale_setup"], str(scaled))
    run_ik(str(scaled), o["ik_setup"], str(out / n["ik_mot"]))
    ext = out / n["external_loads"]
    if not ext.exists():
        raise ValueError("GRF missing; cannot run ID")
    run_id(str(scaled), o["id_setup"], str(out / n["id_sto"]))


def _parse():
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--out-dir", required=True)
    return p.parse_args()


if __name__ == "__main__":
    main()
