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
        rate = float(raw["parameters"]["ANALOG"]["RATE"]["value"][0])
        plates_cfg = config.get("force_plates") or []
        if plates_cfg:
            analog = raw["data"]["analogs"]
            plates = [self._one_plate(analog, p, axes) for p in plates_cfg]
            return plates, rate
        plates = self._forces_from_platforms(raw, config, axes)
        if plates:
            return plates, rate
        return self._forces_from_fp_group(raw, config, axes), rate

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

    def _forces_from_platforms(self, raw, config: dict, axes) -> list:
        platforms = raw["data"].get("platform") or []
        bodies = config.get("force_platform_bodies") or []
        plates = []
        for i, plat in enumerate(platforms):
            if "force" not in plat or "center_of_pressure" not in plat:
                continue
            body = _plate_body(bodies, i)
            force = apply_rotation(np.asarray(plat["force"], dtype=float).T, axes)
            cop = apply_rotation(
                np.asarray(plat["center_of_pressure"], dtype=float).T, axes
            )
            moment = (
                apply_rotation(np.asarray(plat["moment"], dtype=float).T, axes)
                if "moment" in plat
                else np.zeros_like(force)
            )
            plates.append(
                ForcePlateSeries(
                    name=f"FP{i + 1}",
                    force=force,
                    cop=cop,
                    moment=moment,
                    applied_to_body=body,
                )
            )
        return plates

    def _forces_from_fp_group(self, raw, config: dict, axes) -> list:
        fp = raw["parameters"].get("FORCE_PLATFORM")
        if fp is None or int(fp["USED"]["value"][0]) < 1:
            return []
        n = int(fp["USED"]["value"][0])
        channel = np.asarray(fp["CHANNEL"]["value"], dtype=int)
        corners = np.asarray(fp["CORNERS"]["value"], dtype=float)
        analog = raw["data"]["analogs"][0]
        units = [str(u).lower() for u in raw["parameters"]["ANALOG"]["UNITS"]["value"]]
        bodies = config.get("force_platform_bodies") or []
        threshold = float(config.get("force_threshold_n", 20.0))
        plates = []
        for i in range(n):
            idxs = channel[:, i] - 1
            force = analog[idxs[0:3], :].T.astype(float)
            moment = analog[idxs[3:6], :].T.astype(float)
            for j, idx in enumerate(idxs[3:6]):
                if idx < len(units) and units[idx] == "nmm":
                    moment[:, j] /= 1000.0
            center = corners[:, :, i].mean(axis=1) * length_scale("mm")
            cop = _cop_from_fm(force, moment, center, threshold)
            plates.append(
                ForcePlateSeries(
                    name=f"FP{i + 1}",
                    force=apply_rotation(force, axes),
                    cop=apply_rotation(cop, axes),
                    moment=apply_rotation(moment, axes),
                    applied_to_body=_plate_body(bodies, i),
                )
            )
        return plates


def _plate_body(bodies: list, i: int) -> str:
    if i < len(bodies):
        return bodies[i]
    return "calcn_r" if i % 2 == 0 else "calcn_l"


def _cop_from_fm(force, moment, center_m: np.ndarray, threshold: float) -> np.ndarray:
    cop = np.tile(center_m, (force.shape[0], 1))
    fz = force[:, 2]
    active = np.abs(fz) > threshold
    cop[active, 0] = center_m[0] + (-moment[active, 1] / fz[active])
    cop[active, 1] = center_m[1] + (moment[active, 0] / fz[active])
    cop[active, 2] = center_m[2]
    return cop
