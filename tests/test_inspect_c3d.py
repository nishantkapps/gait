"""Test: list C3D point and analog labels (use to fill force_plates in YAML)."""

from __future__ import annotations

import argparse

from ezc3d import c3d


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True, help="Path to .c3d")
    args = p.parse_args()
    raw = c3d(args.source)
    points = [str(x) for x in raw["parameters"]["POINT"]["LABELS"]["value"]]
    analogs = [str(x) for x in raw["parameters"]["ANALOG"]["LABELS"]["value"]]
    print("POINT labels (%d):" % len(points))
    for i, name in enumerate(points):
        print(f"  {i:3d}  {name}")
    print("ANALOG labels (%d):" % len(analogs))
    for i, name in enumerate(analogs):
        print(f"  {i:3d}  {name}")
    print("POINT rate:", raw["parameters"]["POINT"]["RATE"]["value"][0])
    print("ANALOG rate:", raw["parameters"]["ANALOG"]["RATE"]["value"][0])


if __name__ == "__main__":
    main()
