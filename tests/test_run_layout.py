"""Test run number allocation from existing folders."""

from __future__ import annotations

from pathlib import Path

from gait.run_layout import allocate_run, latest_run_number, next_run_number


def main() -> None:
    root = Path(__file__).resolve().parents[1] / "data" / "tmp_runs"
    outputs = root / "outputs"
    logs = root / "logs"
    if root.exists():
        import shutil

        shutil.rmtree(root)
    outputs.mkdir(parents=True)
    logs.mkdir(parents=True)
    assert next_run_number(outputs, logs) == 1
    (outputs / "run_001").mkdir()
    (logs / "run_001").mkdir()
    (outputs / "run_003").mkdir()
    assert latest_run_number(outputs, logs) == 3
    assert next_run_number(outputs, logs) == 4
    n, out_dir, log_dir = allocate_run(outputs, logs)
    assert n == 4
    assert out_dir.name == "run_004"
    assert log_dir.name == "run_004"
    print("OK", n, out_dir, log_dir)


if __name__ == "__main__":
    main()
