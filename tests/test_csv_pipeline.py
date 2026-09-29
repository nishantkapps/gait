"""CI test: CSV fixture → TRC via run_job (no OpenSim)."""

from __future__ import annotations

from pathlib import Path

from gait.run_job import run_job

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures"


def main() -> None:
    out = ROOT / "data" / "processed" / "ci_sample"
    run_job(str(FIX / "sample_trial.yaml"), str(FIX / "sample.csv"), str(out))
    trc = out / "markers.trc"
    assert trc.exists(), f"missing {trc}"
    text = trc.read_text(encoding="utf-8")
    assert "LASI" in text or "L.ASIS" in text
    print("OK", trc)


if __name__ == "__main__":
    main()
