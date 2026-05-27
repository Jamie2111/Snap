"""HUD region coords and a small crop helper.

The actual coordinate values live in config.CAPTURE_REGIONS_1080P so they can be
swapped per resolution without touching the rest of the code.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np

import config

Region = tuple[int, int, int, int]


def get_region(name: str) -> Region:
    region = config.CAPTURE_REGIONS_1080P.get(name)
    if region is None:
        raise KeyError(f"Unknown HUD region: {name}")
    return region


def crop(frame: np.ndarray, region: Region) -> np.ndarray:
    x, y, w, h = region
    return frame[y : y + h, x : x + w].copy()


def crop_named(frame: np.ndarray, name: str) -> np.ndarray:
    return crop(frame, get_region(name))


def scoreboard_row_regions(column_name: str, rows: int = 5) -> list[Region]:
    """Split a scoreboard hero-name column into per-player row regions."""
    x, y, w, h = get_region(column_name)
    row_h = config.SCOREBOARD_ROW_HEIGHT_1080P
    return [(x, y + i * row_h, w, row_h) for i in range(rows)]


def all_region_names() -> Iterable[str]:
    return config.CAPTURE_REGIONS_1080P.keys()
