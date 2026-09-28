"""Canonical gait trial types shared by adapters and writers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass
class SubjectMeta:
    subject_id: str
    mass_kg: float
    height_m: Optional[float] = None
    hemiplegic_side: Optional[str] = None
    trial_id: Optional[str] = None


@dataclass
class ForcePlateSeries:
    name: str
    force: np.ndarray  # (T, 3) N
    cop: np.ndarray  # (T, 3) m
    moment: np.ndarray  # (T, 3) N·m
    applied_to_body: str


@dataclass
class FramePacket:
    time: float
    markers: dict[str, np.ndarray]  # name -> (3,)
    forces: dict[str, dict[str, np.ndarray]] = field(default_factory=dict)


@dataclass
class TrialRecord:
    meta: SubjectMeta
    times: np.ndarray  # (T,)
    markers: dict[str, np.ndarray]  # name -> (T, 3) in OpenSim meters
    forces: list[ForcePlateSeries]
    marker_rate_hz: float
    force_rate_hz: float
