"""Test: apply marker-map YAML to a loaded trial."""

from __future__ import annotations

from gait.adapters.c3d_adapter import C3dAdapter
from gait.config import load_yaml
from gait.mapping import apply_marker_map
from tests.common import parse_config_source


def main() -> None:
    cfg, source = parse_config_source("Test marker mapping")
    trial = C3dAdapter().load(str(source), cfg)
    before = set(trial.markers)
    name_map = load_yaml(cfg["paths"]["marker_map"])["markers"]
    trial = apply_marker_map(trial, name_map)
    after = set(trial.markers)
    renamed = {s: d for s, d in name_map.items() if s in before and d in after}
    print("map entries used:", len(renamed))
    for s, d in list(renamed.items())[:20]:
        print(f"  {s} -> {d}")
    print("markers after:", len(after))
    print("OK")


if __name__ == "__main__":
    main()
