"""Write OpenSim .trc marker files."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from gait.schema import TrialRecord


def write_trc(trial: TrialRecord, out_path: str | Path, units: str) -> None:
    names = sorted(trial.markers)
    n_frames = len(trial.times)
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(f"PathFileType\t4\t(X/Y/Z)\t{path.name}\n")
        f.write(
            "DataRate\tCameraRate\tNumFrames\tNumMarkers\tUnits\t"
            "OrigDataRate\tOrigDataStartFrame\tOrigNumFrames\n"
        )
        f.write(
            f"{trial.marker_rate_hz}\t{trial.marker_rate_hz}\t{n_frames}\t"
            f"{len(names)}\t{units}\t{trial.marker_rate_hz}\t1\t{n_frames}\n"
        )
        f.write("Frame#\tTime\t" + "\t\t\t".join(names) + "\t\t\n")
        f.write(
            "\t\t"
            + "\t".join(f"X{i+1}\tY{i+1}\tZ{i+1}" for i in range(len(names)))
            + "\n"
        )
        for fi in range(n_frames):
            cols = [str(fi + 1), f"{trial.times[fi]:.6f}"]
            for name in names:
                x, y, z = trial.markers[name][fi]
                cols.extend([f"{x:.6f}", f"{y:.6f}", f"{z:.6f}"])
            f.write("\t".join(cols) + "\n")
