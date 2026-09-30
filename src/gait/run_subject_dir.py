"""Process one subject directory: static Scale once, then each dynamic trial."""

from __future__ import annotations

from pathlib import Path

from gait.adapters.factory import get_adapter
from gait.anthro import anthro_from_subject_dir
from gait.config import load_yaml
from gait.discover import discover_c3ds
from gait.mapping import apply_marker_map_file
from gait.opensim_scale_ik_id import run_id, run_ik, run_scale
from gait.scale_measurements import measurements_from_trc
from gait.writers.grf import write_external_loads_xml, write_grf_mot
from gait.writers.trc import write_trc


def run_subject_dir(config_path: str, input_dir: str, out_dir: str) -> Path:
    cfg = load_yaml(config_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    static_c3d, dynamic_c3ds = discover_c3ds(input_dir, cfg)
    _apply_file_anthro(cfg, [static_c3d, *dynamic_c3ds])
    marker_cfg = load_yaml(cfg["paths"]["marker_map"])
    names = cfg["opensim"]["outputs"]
    scaled = _scale_static(cfg, static_c3d, marker_cfg, out, names)
    lines = [
        f"static: {static_c3d.name}",
        f"mass_kg: {cfg['subject']['mass_kg']}",
        f"height_m: {cfg['subject'].get('height_m')}",
        f"scaled: {scaled}",
    ]
    for c3d_path in dynamic_c3ds:
        trial_out = out / c3d_path.stem
        status = _process_dynamic(cfg, c3d_path, marker_cfg, scaled, trial_out, names)
        lines.append(f"{c3d_path.name}:")
        lines.extend(f"  {k}: {v}" for k, v in status.items())
    (out / "subject_manifest.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def _apply_file_anthro(cfg: dict, c3d_paths: list[Path]) -> None:
    info = anthro_from_subject_dir(c3d_paths)
    if "mass_kg" in info:
        cfg["subject"]["mass_kg"] = info["mass_kg"]
    if "height_m" in info:
        cfg["subject"]["height_m"] = info["height_m"]


def _load_trial(cfg: dict, source: Path, marker_cfg: dict, trial_id: str):
    cfg = {**cfg, "subject": {**cfg["subject"], "trial_id": trial_id}}
    trial = get_adapter(cfg["adapter"]["type"]).load(str(source), cfg)
    return apply_marker_map_file(trial, marker_cfg)


def _scale_static(cfg, static_c3d: Path, marker_cfg, out: Path, names: dict) -> Path:
    scale_dir = out / "scale"
    scale_dir.mkdir(parents=True, exist_ok=True)
    trial = _load_trial(cfg, static_c3d, marker_cfg, "static")
    trc = scale_dir / "static.trc"
    write_trc(trial, trc, cfg["units"]["trc_output"])
    o = cfg["opensim"]
    # Prefer code-derived measurements from markers present in the static TRC.
    # YAML opensim.scale_measurements remains an explicit override when provided.
    yaml_meas = o.get("scale_measurements")
    if yaml_meas:
        measurements = list(yaml_meas)
    else:
        measurements = measurements_from_trc(trc)
    (scale_dir / "scale_measurements_used.txt").write_text(
        "\n".join(
            f"{m['name']}: {m['markers'][0]}-{m['markers'][1]} -> {','.join(m['bodies'])}"
            + (f" axes={m['axes']}" if m.get("axes") else "")
            for m in measurements
        )
        + "\n",
        encoding="utf-8",
    )
    scaled = scale_dir / names["scaled_model"]
    run_scale(
        o["generic_model"],
        o["scale_setup"],
        str(scaled),
        str(trc),
        float(cfg["subject"]["mass_kg"]),
        o.get("marker_set"),
        measurements,
        cfg["subject"].get("height_m"),
    )
    return scaled


def _process_dynamic(cfg, c3d_path: Path, marker_cfg, scaled: Path, trial_out: Path, names):
    trial_out.mkdir(parents=True, exist_ok=True)
    status = {k: "pending" for k in names.values()}
    trial = _load_trial(cfg, c3d_path, marker_cfg, c3d_path.stem)
    trc = trial_out / names["trc"]
    write_trc(trial, trc, cfg["units"]["trc_output"])
    status[names["trc"]] = "ok"
    grf = trial_out / names["grf_mot"]
    ext = trial_out / names["external_loads"]
    if not trial.forces:
        raise ValueError(f"No force plates in {c3d_path.name}; cannot write GRF/ID")
    write_grf_mot(trial, grf)
    write_external_loads_xml(trial, str(grf), ext, cfg["opensim"]["ground_body"])
    status[names["grf_mot"]] = "ok"
    status[names["external_loads"]] = "ok"
    ik = trial_out / names["ik_mot"]
    run_ik(str(scaled), cfg["opensim"]["ik_setup"], str(ik), str(trc))
    status[names["ik_mot"]] = "ok"
    id_sto = trial_out / names["id_sto"]
    run_id(
        str(scaled),
        cfg["opensim"]["id_setup"],
        str(id_sto),
        str(ik),
        str(ext),
    )
    status[names["id_sto"]] = "ok"
    status[names["scaled_model"]] = f"shared:{scaled.name}"
    return status
