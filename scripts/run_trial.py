"""Run one trial through adapters → writers → Scale/IK/ID."""

from __future__ import annotations

import argparse
from pathlib import Path

from gait.adapters.c3d_adapter import C3dAdapter
from gait.config import load_yaml
from gait.mapping import apply_marker_map
from gait.opensim_scale_ik_id import run_id, run_ik, run_scale
from gait.writers.grf import write_external_loads_xml, write_grf_mot
from gait.writers.trc import write_trc

ADAPTERS = {"c3d": C3dAdapter}


def main() -> None:
    args = _parse()
    cfg = load_yaml(args.config)
    names = cfg["opensim"]["outputs"]
    out = Path(cfg["paths"]["processed_dir"]) / cfg["subject"]["subject_id"]
    out.mkdir(parents=True, exist_ok=True)
    trial = ADAPTERS[cfg["adapter"]["type"]]().load(args.source, cfg)
    marker_map = load_yaml(cfg["paths"]["marker_map"])
    trial = apply_marker_map(trial, marker_map["markers"])
    trc = out / names["trc"]
    grf = out / names["grf_mot"]
    ext = out / names["external_loads"]
    write_trc(trial, trc, cfg["units"]["trc_output"])
    if trial.forces:
        write_grf_mot(trial, grf)
        write_external_loads_xml(
            trial, str(grf), ext, cfg["opensim"]["ground_body"]
        )
    _run_opensim(cfg, out, ext)


def _run_opensim(cfg: dict, out: Path, ext: Path) -> None:
    osim_cfg = cfg["opensim"]
    names = osim_cfg["outputs"]
    scaled = out / names["scaled_model"]
    ik_mot = out / names["ik_mot"]
    id_sto = out / names["id_sto"]
    run_scale(osim_cfg["generic_model"], osim_cfg["scale_setup"], str(scaled))
    run_ik(str(scaled), osim_cfg["ik_setup"], str(ik_mot))
    if not ext.exists():
        raise ValueError("GRF/ExternalLoads missing; cannot run ID")
    run_id(str(scaled), osim_cfg["id_setup"], str(id_sto))


def _parse():
    p = argparse.ArgumentParser(description="Gait → OpenSim Scale/IK/ID")
    p.add_argument("--config", required=True)
    p.add_argument("--source", required=True, help="Input trial file (e.g. .c3d)")
    return p.parse_args()


if __name__ == "__main__":
    main()
