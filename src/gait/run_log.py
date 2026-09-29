"""Capture Python and native (OpenSim) stdout/stderr into a run log file."""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def capture_run_log(log_path: Path):
    """Send all process output to log_path; restore console when done."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log_f:
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout = log_f
        sys.stderr = log_f
        saved_out = os.dup(1)
        saved_err = os.dup(2)
        os.dup2(log_f.fileno(), 1)
        os.dup2(log_f.fileno(), 2)
        _opensim_file_sink(str(log_path), add=True)
        try:
            yield log_path
            log_f.flush()
            os.fsync(log_f.fileno())
        finally:
            _opensim_file_sink(str(log_path), add=False)
            os.dup2(saved_out, 1)
            os.dup2(saved_err, 2)
            os.close(saved_out)
            os.close(saved_err)
            sys.stdout, sys.stderr = old_out, old_err


def _opensim_file_sink(path: str, add: bool) -> None:
    try:
        import opensim as osim
    except ImportError:
        return
    try:
        if add:
            osim.Logger.addFileSink(path)
            osim.Logger.setLevel(osim.Logger.Level_Info)
        else:
            osim.Logger.removeFileSink(path)
    except Exception:
        pass
