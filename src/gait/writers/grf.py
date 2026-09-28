"""Write GRF .mot and ExternalLoads .xml."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from gait.schema import TrialRecord


def write_grf_mot(trial: TrialRecord, out_path: str | Path) -> None:
    if not trial.forces:
        raise ValueError("No force plates in trial; cannot write GRF .mot")
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    n = trial.forces[0].force.shape[0]
    times = np.arange(n, dtype=float) / trial.force_rate_hz
    headers, cols = _grf_columns(trial, times)
    with path.open("w", encoding="utf-8") as f:
        f.write(f"{path.name}\nversion=1\nnRows={n}\nnColumns={len(headers)}\n")
        f.write("inDegrees=no\nendheader\n")
        f.write("\t".join(headers) + "\n")
        for row in cols:
            f.write("\t".join(f"{v:.6f}" for v in row) + "\n")


def _grf_columns(trial: TrialRecord, times: np.ndarray):
    headers = ["time"]
    blocks = [times.reshape(-1, 1)]
    for fp in trial.forces:
        headers += [f"{fp.name}_v{a}" for a in "xyz"]
        blocks.append(fp.force)
        headers += [f"{fp.name}_p{a}" for a in "xyz"]
        blocks.append(fp.cop)
        headers += [f"{fp.name}_m{a}" for a in "xyz"]
        blocks.append(fp.moment)
    return headers, np.hstack(blocks)


def write_external_loads_xml(
    trial: TrialRecord,
    grf_mot_path: str,
    out_path: str | Path,
    ground_body: str,
) -> None:
    forces_xml = "\n".join(_force_xml(fp, ground_body) for fp in trial.forces)
    text = (
        '<?xml version="1.0"?>\n'
        '<OpenSimDocument Version="40000">\n'
        '  <ExternalLoads name="ExternalLoads">\n'
        f"    <objects>\n{forces_xml}\n    </objects>\n"
        f"    <datafile>{grf_mot_path}</datafile>\n"
        "  </ExternalLoads>\n"
        "</OpenSimDocument>\n"
    )
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _force_xml(fp, ground_body: str) -> str:
    return (
        f'      <ExternalForce name="{fp.name}">\n'
        f"        <applied_to_body>{fp.applied_to_body}</applied_to_body>\n"
        f"        <force_expressed_in_body>{ground_body}</force_expressed_in_body>\n"
        f"        <point_expressed_in_body>{ground_body}</point_expressed_in_body>\n"
        f"        <force_identifier>{fp.name}_v</force_identifier>\n"
        f"        <point_identifier>{fp.name}_p</point_identifier>\n"
        f"        <torque_identifier>{fp.name}_m</torque_identifier>\n"
        "      </ExternalForce>"
    )
