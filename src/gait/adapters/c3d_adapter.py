"""C3D file → TrialRecord (generic; units/axes/channels from config)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from ezc3d import c3d

from gait.schema import ForcePlateSeries, SubjectMeta, TrialRecord
from gait.transforms import apply_rotation, length_scale


class C3dAdapter:
    def load(self, source_path: str, config: dict) -> TrialRecord:
        raw = c3d(source_path)
        axes = config["lab_axes"]["from_lab_to_opensim"]
        meta = self._meta(source_path, config)
        times, markers, mrate = self._markers(raw, config["units"], axes)
        forces, frate = self._forces(raw, config, axes)
        return TrialRecord(meta, times, markers, forces, mrate, frate)

    def _meta(self, source_path: str, config: dict) -> SubjectMeta:
        subj = config["subject"]
        return SubjectMeta(
            subject_id=str(subj.get("subject_id", Path(source_path).stem)),
            mass_kg=float(subj["mass_kg"]),
            height_m=subj.get("height_m"),
            hemiplegic_side=subj.get("hemiplegic_side"),
            trial_id=subj.get("trial_id"),
        )

    def _markers(self, raw, units: dict, axes):
        pts = raw["data"]["points"][:3].transpose(2, 1, 0)
        labels = [str(l) for l in raw["parameters"]["POINT"]["LABELS"]["value"]]
        scale = length_scale(units["marker_input"])
        rate = float(raw["parameters"]["POINT"]["RATE"]["value"][0])
        times = np.arange(pts.shape[0], dtype=float) / rate
        markers = {
            name: apply_rotation(pts[:, i, :] * scale, axes)
            for i, name in enumerate(labels)
        }
        return times, markers, rate

    def _forces(self, raw, config: dict, axes):
        plates_cfg = config.get("force_plates") or []
        analog = raw["data"]["analogs"]  # (1, n_channels, T)
        rate = float(raw["parameters"]["ANALOG"]["RATE"]["value"][0])
        plates = [self._one_plate(analog, p, axes) for p in plates_cfg]
        return plates, rate

    def _one_plate(self, analog, plate_cfg: dict, axes) -> ForcePlateSeries:
        ch = plate_cfg["channels"]
        force = apply_rotation(analog[0, ch["force"], :].T, axes)
        moment = apply_rotation(analog[0, ch["moment"], :].T, axes)
        cop = apply_rotation(analog[0, ch["cop"], :].T, axes)
        return ForcePlateSeries(
            name=plate_cfg["name"],
            force=force,
            cop=cop,
            moment=moment,
            applied_to_body=plate_cfg["applied_to_body"],
        )
