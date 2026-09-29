"""CSV file → TrialRecord (column layout from config)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from gait.schema import ForcePlateSeries, SubjectMeta, TrialRecord
from gait.transforms import apply_rotation, length_scale


class CsvAdapter:
    def load(self, source_path: str, config: dict) -> TrialRecord:
        csv_cfg = config["csv"]
        df = pd.read_csv(source_path, delimiter=csv_cfg.get("delimiter", ","))
        axes = config["lab_axes"]["from_lab_to_opensim"]
        scale = length_scale(config["units"]["marker_input"])
        times, rate = self._times(df, csv_cfg)
        markers = self._markers(df, csv_cfg, scale, axes)
        forces = self._forces(df, csv_cfg, axes)
        meta = self._meta(source_path, config)
        return TrialRecord(meta, times, markers, forces, rate, rate)

    def _meta(self, source_path: str, config: dict) -> SubjectMeta:
        subj = config["subject"]
        return SubjectMeta(
            subject_id=str(subj.get("subject_id", Path(source_path).stem)),
            mass_kg=float(subj["mass_kg"]),
            height_m=subj.get("height_m"),
            hemiplegic_side=subj.get("hemiplegic_side"),
            trial_id=subj.get("trial_id"),
        )

    def _times(self, df, csv_cfg: dict):
        col = csv_cfg.get("time_column")
        if col:
            times = df[col].to_numpy(dtype=float)
            rate = float(1.0 / np.median(np.diff(times))) if len(times) > 1 else 1.0
            return times, rate
        rate = float(csv_cfg["sample_rate_hz"])
        times = np.arange(len(df), dtype=float) / rate
        return times, rate

    def _markers(self, df, csv_cfg: dict, scale: float, axes):
        sx, sy, sz = csv_cfg["axis_suffixes"]
        bases = _marker_bases(df.columns, sx, sy, sz)
        markers = {}
        for base in bases:
            xyz = df[[base + sx, base + sy, base + sz]].to_numpy(dtype=float)
            markers[base] = apply_rotation(xyz * scale, axes)
        if not markers:
            raise ValueError("No marker columns found; check csv.axis_suffixes")
        return markers

    def _forces(self, df, csv_cfg: dict, axes) -> list:
        plates = []
        for plate in csv_cfg.get("force_plates") or []:
            plates.append(_plate_from_df(df, plate, axes))
        return plates


def _plate_from_df(df, plate: dict, axes) -> ForcePlateSeries:
    force = apply_rotation(df[plate["force_columns"]].to_numpy(dtype=float), axes)
    cop = apply_rotation(df[plate["cop_columns"]].to_numpy(dtype=float), axes)
    moment = apply_rotation(df[plate["moment_columns"]].to_numpy(dtype=float), axes)
    return ForcePlateSeries(
        name=plate["name"],
        force=force,
        cop=cop,
        moment=moment,
        applied_to_body=plate["applied_to_body"],
    )


def _marker_bases(columns, sx: str, sy: str, sz: str) -> list[str]:
    cols = set(columns)
    bases = []
    for c in columns:
        if not str(c).endswith(sx):
            continue
        base = str(c)[: -len(sx)]
        if base + sy in cols and base + sz in cols:
            bases.append(base)
    return bases
