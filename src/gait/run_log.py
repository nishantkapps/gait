"""Capture stdout/stderr into a run log file (not the server console)."""

from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def capture_run_log(log_path: Path):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log_f:
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout = log_f
        sys.stderr = log_f
        try:
            yield log_path
        finally:
            sys.stdout, sys.stderr = old_out, old_err
