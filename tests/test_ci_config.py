"""CI test: load example pipeline config."""

from __future__ import annotations

from pathlib import Path

from gait.config import load_yaml

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    cfg = load_yaml(ROOT / "config" / "pipeline.example.yaml")
    assert cfg["adapter"]["type"]
    assert "subject" in cfg
    assert cfg["subject"]["mass_kg"] > 0
    print("OK config")


if __name__ == "__main__":
    main()
