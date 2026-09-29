"""Shared single-trial job runner (CI / one file). Prefer run_subject_dir for patients."""

from __future__ import annotations

from pathlib import Path

from gait.adapters.factory import get_adapter
from gait.config import load_yaml
from gait.mapping import apply_marker_map_file
from gait.opensim_scale_ik_id import run_id, run_ik, run_scale
from gait.writers.grf import write_external_loads_xml, write_grf_mot
from gait.writers.trc import write_trc


def run_job(config_path: str, source_path: str, out_dir: str) -> Path:
    cfg = load_yaml(config_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    names = cfg["opensim"]["outputs"]
    trial = get_adapter(cfg["adapter"]["type"]).load(source_path, cfg)
    trial = apply_marker_map_file(trial, load_yaml(cfg["paths"]["marker_map"]))
    trc = out / names["trc"]
    write_trc(trial, trc, cfg["units"]["trc_output"])
    if trial.forces:
        grf = out / names["grf_mot"]
        ext = out / names["external_loads"]
        write_grf_mot(trial, grf)
        write_external_loads_xml(trial, str(grf), ext, cfg["opensim"]["ground_body"])
    if not cfg.get("opensim", {}).get("enabled"):
        return out
    _opensim(cfg, out, names, trc)
    return out


def _opensim(cfg: dict, out: Path, names: dict, trc: Path) -> None:
    o = cfg["opensim"]
    for key in ("generic_model", "scale_setup", "ik_setup", "id_setup"):
        if not Path(o[key]).exists():
            raise FileNotFoundError(f"OpenSim asset missing: {o[key]}")
    scaled = out / names["scaled_model"]
    run_scale(
        o["generic_model"],
        o["scale_setup"],
        str(scaled),
        str(trc),
        float(cfg["subject"]["mass_kg"]),
        o.get("marker_set"),
        o.get("scale_measurements"),
        cfg["subject"].get("height_m"),
    )
    ik = out / names["ik_mot"]
    run_ik(str(scaled), o["ik_setup"], str(ik), str(trc))
    ext = out / names["external_loads"]
    if not ext.exists():
        raise ValueError("GRF/ExternalLoads missing; cannot run ID")
    run_id(str(scaled), o["id_setup"], str(out / names["id_sto"]), str(ik), str(ext))
