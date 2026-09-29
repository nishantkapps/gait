"""Unit test: discover static + dynamic C3Ds from globs."""

from __future__ import annotations

from pathlib import Path

from gait.discover import discover_c3ds


def main() -> None:
    root = Path(__file__).resolve().parents[1] / "data" / "tmp_discover"
    root.mkdir(parents=True, exist_ok=True)
    (root / "TVC-4 Cal 03.c3d").write_bytes(b"")
    (root / "BWA_6.c3d").write_bytes(b"")
    (root / "BWA_7.c3d").write_bytes(b"")
    (root / "notes.txt").write_text("ignore", encoding="utf-8")
    cfg = {
        "subject_dir": {
            "static_glob": "*Cal*.c3d",
            "dynamic_glob": "BWA_*.c3d",
        }
    }
    static, dynamic = discover_c3ds(root, cfg)
    assert static.name == "TVC-4 Cal 03.c3d"
    assert [p.name for p in dynamic] == ["BWA_6.c3d", "BWA_7.c3d"]
    print("OK", static.name, [p.name for p in dynamic])


if __name__ == "__main__":
    main()
