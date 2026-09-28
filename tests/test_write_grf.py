"""Test: write GRF .mot and ExternalLoads .xml."""

from __future__ import annotations

from gait.adapters.c3d_adapter import C3dAdapter
from gait.writers.grf import write_external_loads_xml, write_grf_mot
from tests.common import out_dir, parse_config_source


def main() -> None:
    cfg, source = parse_config_source("Test GRF writers")
    trial = C3dAdapter().load(str(source), cfg)
    if not trial.forces:
        raise SystemExit("No force_plates in config/trial; set channels first")
    out = out_dir(cfg)
    names = cfg["opensim"]["outputs"]
    grf = out / names["grf_mot"]
    ext = out / names["external_loads"]
    write_grf_mot(trial, grf)
    write_external_loads_xml(trial, str(grf), ext, cfg["opensim"]["ground_body"])
    print("wrote", grf, "and", ext)
    print("OK")


if __name__ == "__main__":
    main()
