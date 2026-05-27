"""Global configuration. Paths, thresholds, HUD region coords, platform detection."""

from __future__ import annotations

import logging
import os
import platform
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SESSIONS_DIR = DATA_DIR / "sessions"
PROFILES_DIR = DATA_DIR / "profiles"
REPORTS_DIR = DATA_DIR / "reports"
DB_PATH = PROFILES_DIR / "snap.db"

for d in (SESSIONS_DIR, PROFILES_DIR, REPORTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

SYSTEM = platform.system()
IS_WINDOWS = SYSTEM == "Windows"
IS_MAC = SYSTEM == "Darwin"

TESSERACT_CMD = os.environ.get("TESSERACT_CMD", "tesseract")

CAPTURE_FPS = 2
CAPTURE_FPS_FIGHT = 4
FIGHT_DETECTION_HEALTH_DROP = 0.30
PIXEL_DIFF_SKIP_THRESHOLD = 0.005

HERO_DETECTION_CONFIDENCE_THRESHOLD = 0.8
OCR_HERO_MATCH_THRESHOLD = 0.7

OW2_WINDOW_TITLE_FRAGMENTS = ("Overwatch",)

# Best-guess 1080p HUD region coords. Tune if the player runs custom HUD scale.
# Format: (x, y, w, h) in pixels for a 1920x1080 capture.
CAPTURE_REGIONS_1080P: dict[str, tuple[int, int, int, int]] = {
    "health_bar": (760, 985, 400, 25),
    "ultimate_charge": (920, 935, 80, 80),
    "ability_slot_1": (1080, 970, 50, 50),
    "ability_slot_2": (1140, 970, 50, 50),
    "ability_slot_3": (1200, 970, 50, 50),
    "ability_slot_4": (1260, 970, 50, 50),
    "kill_feed": (1500, 100, 420, 220),
    "hero_portrait": (40, 935, 100, 100),
    "death_overlay": (760, 480, 400, 120),
    "respawn_timer": (900, 540, 120, 60),

    # Scoreboard rows when Tab held. Hero name column per team.
    "scoreboard_ally_names": (385, 340, 270, 360),
    "scoreboard_enemy_names": (1265, 340, 270, 360),
    "scoreboard_signature": (860, 110, 200, 60),

    # Hero pick screen, swap notification, spawn room. Skin-independent text reads.
    # "CHOOSE YOUR HERO" / "SELECT YOUR HERO" banner across the top of the pick screen.
    "pick_screen_signature": (760, 40, 400, 60),
    # Large card on the right side of the pick screen showing the currently
    # selected hero portrait (default skin) with name underneath.
    "pick_screen_selected_name": (1480, 780, 400, 70),
    # Center-top transient banner shown briefly when you confirm / swap heroes
    # ("YOU ARE PLAYING X" or the new hero's name + role).
    "hero_swap_banner": (660, 140, 600, 80),
    # Spawn-room card. Visible during the seconds before you exit spawn.
    "spawn_room_hero_name": (60, 880, 380, 60),
    "spawn_room_signature": (1700, 60, 200, 80),

    "minimap": (40, 40, 220, 220),
    "map_name_pregame": (760, 200, 400, 120),
}

SCOREBOARD_ROW_HEIGHT_1080P = 72

ABILITY_SLOTS = ("ability_1", "ability_2", "ability_3", "ability_4")

DEATH_OVERLAY_GREY_THRESHOLD = 0.55
HEALTH_BAR_FILLED_HSV = ((0, 0, 180), (180, 60, 255))
ULT_BAR_FILLED_HSV = ((20, 90, 180), (40, 255, 255))
COOLDOWN_GREY_SATURATION_MAX = 50

KNOWN_HEROES = (
    "ana", "ashe", "baptiste", "bastion", "brigitte", "cassidy",
    "doomfist", "dva", "echo", "freja", "genji", "hanzo",
    "illari", "junkerqueen", "junkrat", "juno", "kiriko", "lifeweaver",
    "lucio", "mauga", "mei", "mercy", "moira", "orisa",
    "pharah", "ramattra", "reaper", "reinhardt", "roadhog", "sigma",
    "sojourn", "soldier76", "sombra", "symmetra", "torbjorn", "tracer",
    "venture", "widowmaker", "winston", "wreckingball", "zarya", "zenyatta",
)

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
LOG_DATEFMT = "%H:%M:%S"


def configure_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format=LOG_FORMAT, datefmt=LOG_DATEFMT)
