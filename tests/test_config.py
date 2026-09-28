"""Test: load pipeline YAML config."""

from __future__ import annotations

import argparse

from gait.config import load_yaml


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    args = p.parse_args()
    cfg = load_yaml(args.config)
    print("adapter:", cfg["adapter"]["type"])
    print("subject:", cfg["subject"]["subject_id"], "mass_kg=", cfg["subject"]["mass_kg"])
    print("marker_map:", cfg["paths"]["marker_map"])
    print("force_plates:", len(cfg.get("force_plates") or []))
    print("OK")


if __name__ == "__main__":
    main()
