"""Test: C3D adapter → TrialRecord."""

from __future__ import annotations

from gait.adapters.c3d_adapter import C3dAdapter
from tests.common import parse_config_source


def main() -> None:
    cfg, source = parse_config_source("Test C3dAdapter")
    trial = C3dAdapter().load(str(source), cfg)
    print("subject:", trial.meta.subject_id, "mass=", trial.meta.mass_kg)
    print("frames:", len(trial.times), "rate=", trial.marker_rate_hz)
    print("markers:", len(trial.markers), list(trial.markers)[:10], "...")
    print("force_plates:", len(trial.forces), [f.name for f in trial.forces])
    if trial.forces:
        fp = trial.forces[0]
        print("first plate force shape:", fp.force.shape, "body=", fp.applied_to_body)
    print("OK")


if __name__ == "__main__":
    main()
