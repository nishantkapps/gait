"""Tee stdout/stderr into a log file while still printing to the console."""

from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path


class _Tee:
    def __init__(self, *streams):
        self._streams = streams

    def write(self, data: str) -> int:
        for s in self._streams:
            s.write(data)
            s.flush()
        return len(data)

    def flush(self) -> None:
        for s in self._streams:
            s.flush()


@contextmanager
def capture_run_log(log_path: Path):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log_f:
        tee_out = _Tee(sys.__stdout__, log_f)
        tee_err = _Tee(sys.__stderr__, log_f)
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = tee_out, tee_err
        try:
            yield log_path
        finally:
            sys.stdout, sys.stderr = old_out, old_err
