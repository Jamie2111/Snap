"""OCR wrappers for hero name detection and killfeed parsing.

Skin-independent. Reads UI text only.

Two main entry points:
  read_scoreboard(frame) -> ScoreboardRead
  read_killfeed(frame, timestamp) -> list[KillFeedEvent]
"""

from __future__ import annotations

import difflib
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np

try:
    import pytesseract
except ImportError:  # pragma: no cover
    pytesseract = None  # type: ignore[assignment]

import config
from capture import regions
from extractor.game_state import KillFeedEvent

log = logging.getLogger(__name__)

if pytesseract is not None and config.TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD


def _check_tesseract_available() -> bool:
    """Check once whether tesseract is installed and on PATH.

    Without tesseract, no OCR is possible. We detect this at import time
    so subsequent calls return early without raising or spamming logs."""
    if pytesseract is None:
        return False
    import shutil
    if shutil.which(config.TESSERACT_CMD) is None:
        return False
    return True


TESSERACT_AVAILABLE = _check_tesseract_available()
if not TESSERACT_AVAILABLE:
    log.warning(
        "Tesseract not installed or not on PATH. Hero/scoreboard/killfeed OCR is "
        "disabled for this session. Install with: brew install tesseract (macOS) "
        "or from https://github.com/UB-Mannheim/tesseract/wiki (Windows). "
        "Snap will continue without OCR; vision and HUD extraction still work."
    )


HERO_ALIASES = {
    "soldier": "soldier76",
    "soldier 76": "soldier76",
    "junker queen": "junkerqueen",
    "wrecking ball": "wreckingball",
    "d.va": "dva",
    "dva": "dva",
    "lúcio": "lucio",
    "torbjörn": "torbjorn",
}


@dataclass
class ScoreboardRead:
    your_hero: Optional[str] = None
    allies: list[str] = field(default_factory=list)
    enemies: list[str] = field(default_factory=list)
    raw_texts: dict[str, list[str]] = field(default_factory=dict)


def _preprocess_for_text(crop: np.ndarray, upscale: int = 2, invert: bool = False) -> np.ndarray:
    if crop.size == 0:
        return crop
    h, w = crop.shape[:2]
    if upscale > 1:
        crop = cv2.resize(crop, (w * upscale, h * upscale), interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    if invert:
        thresh = 255 - thresh
    return thresh


_ocr_warning_logged = False


def _ocr(crop: np.ndarray, psm: int = 6, char_whitelist: Optional[str] = None) -> str:
    global _ocr_warning_logged
    if not TESSERACT_AVAILABLE or pytesseract is None:
        return ""
    if crop.size == 0:
        return ""
    cfg = f"--psm {psm}"
    if char_whitelist:
        cfg += f" -c tessedit_char_whitelist={char_whitelist}"
    try:
        return pytesseract.image_to_string(crop, config=cfg)
    except Exception as exc:
        # Log at debug level after first occurrence to avoid log spam.
        if not _ocr_warning_logged:
            log.warning("OCR call failed (%s). Subsequent OCR failures suppressed.", exc)
            _ocr_warning_logged = True
        else:
            log.debug("OCR call failed: %s", exc)
        return ""


def _normalize_hero_name(raw: str) -> Optional[str]:
    if not raw:
        return None
    cleaned = re.sub(r"[^a-zA-Zúö ]", "", raw).strip().lower()
    if not cleaned:
        return None
    if cleaned in HERO_ALIASES:
        return HERO_ALIASES[cleaned]
    no_space = cleaned.replace(" ", "")
    if no_space in HERO_ALIASES:
        return HERO_ALIASES[no_space]
    if no_space in config.KNOWN_HEROES:
        return no_space
    candidates = difflib.get_close_matches(
        no_space, config.KNOWN_HEROES, n=1, cutoff=config.OCR_HERO_MATCH_THRESHOLD
    )
    if candidates:
        return candidates[0]
    return None


def _extract_lines(text: str) -> list[str]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return [ln for ln in lines if len(ln) >= 2]


def read_hero_column(frame: np.ndarray, region_name: str) -> list[str]:
    """OCR a vertical hero-name column from the scoreboard.

    Returns up to 5 normalized hero names in row order. Names that fail to
    match the KNOWN_HEROES list are dropped (silent fail; better to lose a
    noisy read than fabricate a wrong hero)."""

    crop = regions.crop_named(frame, region_name)
    if crop.size == 0:
        return []
    pre = _preprocess_for_text(crop)
    raw = _ocr(pre, psm=6)
    lines = _extract_lines(raw)
    heroes: list[str] = []
    for ln in lines[:6]:
        normalized = _normalize_hero_name(ln)
        if normalized:
            heroes.append(normalized)
    return heroes[:5]


def read_scoreboard(frame: np.ndarray) -> ScoreboardRead:
    """Read both team hero-name columns. Your hero is the first ally row
    (typically your own row, highlighted, at the top of your team)."""

    allies = read_hero_column(frame, "scoreboard_ally_names")
    enemies = read_hero_column(frame, "scoreboard_enemy_names")
    your_hero = allies[0] if allies else None
    other_allies = allies[1:] if len(allies) > 1 else []
    return ScoreboardRead(
        your_hero=your_hero,
        allies=other_allies,
        enemies=enemies,
        raw_texts={"allies": allies, "enemies": enemies},
    )


def read_pick_screen_hero(frame: np.ndarray) -> Optional[str]:
    """OCR the currently-selected hero name from the pick screen.

    The pick screen always shows the default skin and the hero name in plain
    text. This is the single most reliable hero-detection signal in the game:
    no skin variation, no Tab requirement, no scoreboard noise."""

    crop = regions.crop_named(frame, "pick_screen_selected_name")
    pre = _preprocess_for_text(crop, upscale=3)
    raw = _ocr(pre, psm=7)
    for ln in _extract_lines(raw):
        normalized = _normalize_hero_name(ln)
        if normalized:
            return normalized
    return None


def read_swap_banner_hero(frame: np.ndarray) -> Optional[str]:
    """OCR the transient swap banner ('YOU ARE PLAYING X')."""

    crop = regions.crop_named(frame, "hero_swap_banner")
    pre = _preprocess_for_text(crop, upscale=3, invert=True)
    raw = _ocr(pre, psm=7)
    for ln in _extract_lines(raw):
        # Banner text often has prefix words. Strip the prefix and try each
        # whitespace-separated token until one matches a known hero.
        for token in ln.split():
            normalized = _normalize_hero_name(token)
            if normalized:
                return normalized
        # Last resort: try the whole line.
        normalized = _normalize_hero_name(ln)
        if normalized:
            return normalized
    return None


def read_spawn_room_hero(frame: np.ndarray) -> Optional[str]:
    """OCR the hero name from the spawn-room card.

    Visible during the seconds between respawn and exiting spawn."""

    crop = regions.crop_named(frame, "spawn_room_hero_name")
    pre = _preprocess_for_text(crop, upscale=3)
    raw = _ocr(pre, psm=7)
    for ln in _extract_lines(raw):
        normalized = _normalize_hero_name(ln)
        if normalized:
            return normalized
    return None


_KILLFEED_LINE_RE = re.compile(r"^(?P<killer>[\w\-_.]{2,16})\s+(?P<victim>[\w\-_.]{2,16})$")


def read_killfeed(frame: np.ndarray, timestamp: float) -> list[KillFeedEvent]:
    """OCR the killfeed region and parse out (killer, victim) name pairs.

    The ability icon between names is skinned, so we do not try to extract it
    here. v2 work."""

    crop = regions.crop_named(frame, "kill_feed")
    pre = _preprocess_for_text(crop)
    raw = _ocr(pre, psm=6)
    events: list[KillFeedEvent] = []
    for line in _extract_lines(raw):
        m = _KILLFEED_LINE_RE.match(line)
        if not m:
            continue
        events.append(KillFeedEvent(
            timestamp=timestamp,
            killer=m.group("killer"),
            victim=m.group("victim"),
            ability="",
        ))
    return events
