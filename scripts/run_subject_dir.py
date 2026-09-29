"""CLI: process one subject directory (static Cal + all dynamic BWA C3Ds)."""

from __future__ import annotations

import argparse
from pathlib import Path

from gait.run_subject_dir import run_subject_dir


def main() -> None:
    p = argparse.ArgumentParser(
        description="Subject folder → Scale once + IK/ID per dynamic trial"
    )
    p.add_argument("--config", required=True)
    p.add_argument(
        "--input-dir",
        required=True,
        help="Patient folder with Cal + BWA_*.c3d files",
    )
    p.add_argument(
        "--out-dir",
        default=None,
        help="Output directory (default: data/processed/<subject_id>)",
    )
    args = p.parse_args()
    out = args.out_dir
    if out is None:
        from gait.config import load_yaml

        cfg = load_yaml(args.config)
        out = str(
            Path(cfg["paths"]["processed_dir"]) / cfg["subject"]["subject_id"]
        )
    path = run_subject_dir(args.config, args.input_dir, out)
    print("wrote", path)


if __name__ == "__main__":
    main()
