"""Shared Workstream A job runner used by CLI and local server."""

from __future__ import annotations

from pathlib import Path

from gait.adapters.factory import get_adapter
from gait.config import load_yaml
from gait.mapping import apply_marker_map
from gait.opensim_scale_ik_id import run_id, run_ik, run_scale
from gait.writers.grf import write_external_loads_xml, write_grf_mot
from gait.writers.trc import write_trc

EXPECTED = [
    "markers.trc",
    "grf.mot",
    "external_loads.xml",
    "scaled.osim",
    "ik.mot",
    "id.sto",
]


def run_job(config_path: str, source_path: str, out_dir: str) -> Path:
    cfg = load_yaml(config_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    names = cfg["opensim"]["outputs"]
    status = {k: "pending" for k in EXPECTED}
    trial = get_adapter(cfg["adapter"]["type"]).load(source_path, cfg)
    trial = apply_marker_map(trial, load_yaml(cfg["paths"]["marker_map"])["markers"])
    write_trc(trial, out / names["trc"], cfg["units"]["trc_output"])
    status[names["trc"]] = "ok"
    _write_forces(trial, cfg, out, names, status)
    _run_opensim_or_skip(cfg, out, names, status)
    _write_manifest(out, status)
    return out


def _write_forces(trial, cfg, out: Path, names: dict, status: dict) -> None:
    if not trial.forces:
        status[names["grf_mot"]] = "missing: no force plates in source/config"
        status[names["external_loads"]] = "missing: no force plates in source/config"
        return
    write_grf_mot(trial, out / names["grf_mot"])
    write_external_loads_xml(
        trial,
        str(out / names["grf_mot"]),
        out / names["external_loads"],
        cfg["opensim"]["ground_body"],
    )
    status[names["grf_mot"]] = "ok"
    status[names["external_loads"]] = "ok"


def _run_opensim_or_skip(cfg, out: Path, names: dict, status: dict) -> None:
    if not cfg.get("opensim", {}).get("enabled"):
        for key in ("scaled_model", "ik_mot", "id_sto"):
            status[names[key]] = "missing: opensim.enabled is false"
        return
    o = cfg["opensim"]
    missing = [
        p
        for p in (o["generic_model"], o["scale_setup"], o["ik_setup"], o["id_setup"])
        if not Path(p).exists()
    ]
    if missing:
        msg = "missing assets: " + ", ".join(missing)
        for key in ("scaled_model", "ik_mot", "id_sto"):
            status[names[key]] = msg
        return
    _opensim(cfg, out, names, status)


def _opensim(cfg: dict, out: Path, names: dict, status: dict) -> None:
    o = cfg["opensim"]
    scaled = out / names["scaled_model"]
    try:
        run_scale(o["generic_model"], o["scale_setup"], str(scaled))
        status[names["scaled_model"]] = "ok"
    except Exception as exc:
        status[names["scaled_model"]] = f"failed: {exc}"
        status[names["ik_mot"]] = "skipped: scale failed"
        status[names["id_sto"]] = "skipped: scale failed"
        return
    try:
        run_ik(str(scaled), o["ik_setup"], str(out / names["ik_mot"]))
        status[names["ik_mot"]] = "ok"
    except Exception as exc:
        status[names["ik_mot"]] = f"failed: {exc}"
        status[names["id_sto"]] = "skipped: ik failed"
        return
    ext = out / names["external_loads"]
    if not ext.exists():
        status[names["id_sto"]] = "missing: need GRF/ExternalLoads for ID"
        return
    try:
        run_id(str(scaled), o["id_setup"], str(out / names["id_sto"]))
        status[names["id_sto"]] = "ok"
    except Exception as exc:
        status[names["id_sto"]] = f"failed: {exc}"


def _write_manifest(out: Path, status: dict) -> None:
    lines = [f"{name}: {msg}" for name, msg in status.items()]
    (out / "outputs_manifest.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
