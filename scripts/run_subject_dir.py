"""CLI: process one subject directory (static Cal + all dynamic BWA C3Ds)."""

from __future__ import annotations

import argparse
import traceback
from pathlib import Path

from gait.config import load_yaml
from gait.run_layout import allocate_run
from gait.run_log import capture_run_log
from gait.run_subject_dir import run_subject_dir

ROOT = Path(__file__).resolve().parents[1]


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
        help="Override results dir (default: data/outputs/run_XXX/results)",
    )
    args = p.parse_args()
    server = load_yaml(ROOT / "config" / "server.yaml")
    outputs_root = ROOT / server["outputs_dir"]
    logs_root = ROOT / server["logs_dir"]
    run_n, out_dir, log_dir = allocate_run(outputs_root, logs_root)
    results = Path(args.out_dir) if args.out_dir else out_dir / "results"
    log_path = log_dir / "pipeline.log"
    try:
        with capture_run_log(log_path):
            print(f"run_{run_n:03d} output={out_dir} log={log_path}")
            path = run_subject_dir(args.config, args.input_dir, str(results))
            print("wrote", path)
    except Exception:
        with log_path.open("a", encoding="utf-8") as log_f:
            log_f.write("\n" + traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
