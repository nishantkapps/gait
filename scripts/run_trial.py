"""Run one trial through adapters → writers → Scale/IK/ID."""

from __future__ import annotations

import argparse
from pathlib import Path

from gait.run_job import run_job
from gait.run_subject_dir import run_subject_dir


def main() -> None:
    args = _parse()
    if args.input_dir:
        out = args.out_dir
        if out is None:
            from gait.config import load_yaml

            cfg = load_yaml(args.config)
            out = str(Path(cfg["paths"]["processed_dir"]) / cfg["subject"]["subject_id"])
        path = run_subject_dir(args.config, args.input_dir, out)
    else:
        if not args.source:
            raise SystemExit("Provide --input-dir (subject folder) or --source (one file)")
        from gait.config import load_yaml

        cfg = load_yaml(args.config)
        out = args.out_dir or str(
            Path(cfg["paths"]["processed_dir"]) / cfg["subject"]["subject_id"]
        )
        path = run_job(args.config, args.source, out)
    print("wrote", path)


def _parse():
    p = argparse.ArgumentParser(description="Gait → OpenSim Scale/IK/ID")
    p.add_argument("--config", required=True)
    p.add_argument("--input-dir", help="Patient folder (Cal + BWA_*.c3d)")
    p.add_argument("--source", help="Single trial file (legacy)")
    p.add_argument("--out-dir", default=None)
    return p.parse_args()


if __name__ == "__main__":
    main()
