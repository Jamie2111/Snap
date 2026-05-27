"""Skin-independent game state extraction from a single frame.

Every extractor reads either UI overlays (cooldown grey-out, death overlay) or
pixel fill of UI bars (health, ult). Nothing here depends on character art, so
skins do not change extractor output.

The only output that depends on hero identity is `hero`, which is filled in by
the OCR module and the match_context module, not here.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np

import config
from capture import regions

log = logging.getLogger(__name__)


@dataclass
class KillFeedEvent:
    timestamp: float
    killer: str = ""
    victim: str = ""
    ability: str = ""


@dataclass
class GameState:
    timestamp: float
    health_pct: float = 1.0
    ult_pct: float = 0.0
    cooldowns: dict[str, str] = field(default_factory=dict)
    hero: Optional[str] = None
    in_death_screen: bool = False
    scoreboard_visible: bool = False
    kill_feed_events: list[KillFeedEvent] = field(default_factory=list)
    fight_intensity: float = 0.0


def _pct_filled_by_value(crop: np.ndarray, value_min: int = 180) -> float:
    """Fraction of pixels in `crop` whose grayscale value is at least `value_min`.

    The OW2 health bar is light/white when filled and dark/black when empty.
    Counting bright pixels gives a robust pct-filled measurement that does not
    depend on the exact bar geometry."""

    if crop.size == 0:
        return 0.0
    gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
    bright = np.count_nonzero(gray >= value_min)
    return float(bright) / float(gray.size)


def _pct_filled_by_hsv(crop: np.ndarray, lower: tuple[int, int, int], upper: tuple[int, int, int]) -> float:
    """Fraction of pixels in `crop` whose HSV value falls inside the range.

    Used for the ult charge bar, which is yellow/gold when charged."""

    if crop.size == 0:
        return 0.0
    hsv = cv2.cvtColor(crop, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
    return float(np.count_nonzero(mask)) / float(mask.size)


def extract_health_pct(frame: np.ndarray) -> float:
    crop = regions.crop_named(frame, "health_bar")
    return _pct_filled_by_value(crop, value_min=180)


def extract_ult_pct(frame: np.ndarray) -> float:
    crop = regions.crop_named(frame, "ultimate_charge")
    lo, hi = config.ULT_BAR_FILLED_HSV
    return _pct_filled_by_hsv(crop, lo, hi)


def _is_icon_on_cooldown(crop: np.ndarray) -> str:
    """Universal cooldown detection.

    The OW2 cooldown overlay desaturates the icon (low S in HSV) and may darken
    it (low V). We classify by mean saturation: low = on cooldown, high = ready.
    A bright highlight (very high V across most pixels) indicates the ability
    is actively being used."""

    if crop.size == 0:
        return "ready"
    hsv = cv2.cvtColor(crop, cv2.COLOR_RGB2HSV)
    mean_s = float(hsv[..., 1].mean())
    mean_v = float(hsv[..., 2].mean())
    if mean_v > 220 and mean_s > 60:
        return "active"
    if mean_s < config.COOLDOWN_GREY_SATURATION_MAX:
        return "cooldown"
    return "ready"


def extract_cooldowns(frame: np.ndarray) -> dict[str, str]:
    out: dict[str, str] = {}
    for i, slot in enumerate(config.ABILITY_SLOTS, start=1):
        crop = regions.crop_named(frame, f"ability_slot_{i}")
        out[slot] = _is_icon_on_cooldown(crop)
    return out


def detect_death_screen(frame: np.ndarray) -> bool:
    """The death overlay covers a large center region with a grey/dark hue.

    We crop the central death-overlay region and check the fraction of pixels
    that are low-saturation mid-value (the death overlay's signature)."""

    crop = regions.crop_named(frame, "death_overlay")
    if crop.size == 0:
        return False
    hsv = cv2.cvtColor(crop, cv2.COLOR_RGB2HSV)
    low_sat = hsv[..., 1] < 40
    mid_val = (hsv[..., 2] > 30) & (hsv[..., 2] < 180)
    grey_mask = low_sat & mid_val
    grey_fraction = float(np.count_nonzero(grey_mask)) / float(grey_mask.size)
    return grey_fraction > config.DEATH_OVERLAY_GREY_THRESHOLD


def detect_scoreboard_visible(frame: np.ndarray) -> bool:
    """Scoreboard (Tab held) renders a dark overlay with column headers near
    the top center. We check the scoreboard_signature region for the
    characteristic dark-with-bright-text pattern."""

    crop = regions.crop_named(frame, "scoreboard_signature")
    if crop.size == 0:
        return False
    gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
    very_dark = np.count_nonzero(gray < 60) / gray.size
    bright_text = np.count_nonzero(gray > 200) / gray.size
    return very_dark > 0.40 and bright_text > 0.02


def detect_pick_screen_visible(frame: np.ndarray) -> bool:
    """Hero pick screen has a wide dark overlay with bright header text and a
    large character card on the right. The pick_screen_signature region is the
    top-center 'CHOOSE YOUR HERO' banner band."""

    crop = regions.crop_named(frame, "pick_screen_signature")
    if crop.size == 0:
        return False
    gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
    dark_bg = np.count_nonzero(gray < 60) / gray.size
    bright_text = np.count_nonzero(gray > 200) / gray.size
    return bool(dark_bg > 0.50 and bright_text > 0.03)


def detect_swap_banner_visible(frame: np.ndarray) -> bool:
    """The transient 'YOU ARE PLAYING X' banner that appears top-center after
    you confirm a hero swap. Bright text on a slightly tinted background."""

    crop = regions.crop_named(frame, "hero_swap_banner")
    if crop.size == 0:
        return False
    gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
    bright_text = np.count_nonzero(gray > 210) / gray.size
    mid_bg = np.count_nonzero((gray > 30) & (gray < 120)) / gray.size
    return bool(bright_text > 0.04 and mid_bg > 0.30)


def detect_spawn_room_visible(frame: np.ndarray) -> bool:
    """Spawn room renders a hero card in the bottom-left and a distinctive
    bright banner / icon in the top-right (objective marker)."""

    crop = regions.crop_named(frame, "spawn_room_signature")
    if crop.size == 0:
        return False
    gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
    bright = np.count_nonzero(gray > 180) / gray.size
    return bool(bright > 0.10)


def fight_intensity_from_history(health_history: list[float], window: int = 4) -> float:
    if len(health_history) < 2:
        return 0.0
    recent = health_history[-window:]
    return float(np.std(recent) * 2.0)


def extract_state(frame: np.ndarray, timestamp: float, health_history: Optional[list[float]] = None) -> GameState:
    """One-shot extractor: pull every signal we can from a single frame."""

    health_history = health_history or []
    state = GameState(
        timestamp=timestamp,
        health_pct=extract_health_pct(frame),
        ult_pct=extract_ult_pct(frame),
        cooldowns=extract_cooldowns(frame),
        in_death_screen=detect_death_screen(frame),
        scoreboard_visible=detect_scoreboard_visible(frame),
        fight_intensity=fight_intensity_from_history(health_history),
    )
    return state


def frame_diff_below_threshold(a: np.ndarray, b: np.ndarray, threshold: float = config.PIXEL_DIFF_SKIP_THRESHOLD) -> bool:
    """Cheap interpolation gate. If two consecutive frames differ by less than
    `threshold` in mean absolute pixel difference, the caller may skip extraction
    on the second one and reuse the first one's GameState."""

    if a.shape != b.shape:
        return False
    diff = np.mean(np.abs(a.astype(np.int16) - b.astype(np.int16))) / 255.0
    return diff < threshold
