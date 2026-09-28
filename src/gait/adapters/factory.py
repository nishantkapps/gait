"""Resolve adapter class from config type string."""

from __future__ import annotations

from gait.adapters.c3d_adapter import C3dAdapter
from gait.adapters.csv_adapter import CsvAdapter

_ADAPTERS = {
    "c3d": C3dAdapter,
    "csv": CsvAdapter,
}


def get_adapter(type_name: str):
    try:
        return _ADAPTERS[type_name]()
    except KeyError as exc:
        raise ValueError(f"Unknown adapter type: {type_name}") from exc
