"""Adapter interface: any source → TrialRecord."""

from __future__ import annotations

from typing import Protocol

from gait.schema import TrialRecord


class TrialAdapter(Protocol):
    def load(self, source_path: str, config: dict) -> TrialRecord:
        """Parse one trial file into a canonical TrialRecord."""
