"""Smoke tests for the extractor layer."""

from __future__ import annotations

import numpy as np

import config
from capture import regions
from extractor import game_state


def test_region_crop_shape() -> None:
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    hb = regions.crop_named(frame, "health_bar")
    assert hb.shape[2] == 3
    assert hb.shape[0] > 0
    assert hb.shape[1] > 0


def test_health_full_when_bright() -> None:
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    x, y, w, h = config.CAPTURE_REGIONS_1080P["health_bar"]
    frame[y : y + h, x : x + w] = 255
    state = game_state.extract_state(frame, timestamp=0.0)
    assert state.health_pct > 0.9


def test_health_zero_when_dark() -> None:
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    state = game_state.extract_state(frame, timestamp=0.0)
    assert state.health_pct < 0.1


def test_death_overlay_grey() -> None:
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    x, y, w, h = config.CAPTURE_REGIONS_1080P["death_overlay"]
    frame[y : y + h, x : x + w] = 100
    state = game_state.extract_state(frame, timestamp=0.0)
    assert state.in_death_screen is True


def test_pick_screen_detector_fires_on_dark_bg_with_bright_text() -> None:
    """Synthetic frame: pick_screen_signature region has dark bg with bright text speckles."""
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    x, y, w, h = config.CAPTURE_REGIONS_1080P["pick_screen_signature"]
    frame[y : y + h, x : x + w] = 20  # dark bg
    # Speckle bright text pixels through the region
    for row in range(y + 10, y + h - 10, 4):
        frame[row, x + 50 : x + 200] = 240
    assert game_state.detect_pick_screen_visible(frame) is True


def test_pick_screen_detector_quiet_on_empty_frame() -> None:
    frame = np.full((1080, 1920, 3), 128, dtype=np.uint8)
    assert game_state.detect_pick_screen_visible(frame) is False
