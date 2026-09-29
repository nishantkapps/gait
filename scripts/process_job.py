"""CLI: source + YAML → TRC/GRF (OpenSim optional)."""

from __future__ import annotations

import argparse

from gait.run_job import run_job


def main() -> None:
    args = _parse()
    run_job(args.config, args.source, args.out_dir)


def _parse():
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--out-dir", required=True)
    return p.parse_args()


if __name__ == "__main__":
    main()
