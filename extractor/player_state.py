"""Infer the player's current high-level state from a GameState + screen-state
detectors. This drives the adaptive overlay: how prominent should Snap be
right now, and what kind of tip is appropriate.

States (in priority order, highest wins on the same frame):

    LOBBY         No match active (between matches / pick screen / pregame splash)
    DYING         Death overlay visible OR very recent death event
    SPAWN         In spawn room (post-respawn, pre-engagement)
    FIGHT         High fight intensity (active combat)
    PLAYING       Walking / repositioning, none of the above
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np

from extractor.game_state import (
    GameState,
    detect_pick_screen_visible,
    detect_pregame_splash,
    detect_spawn_room_visible,
)

log = logging.getLogger(__name__)


class PlayerState(str, Enum):
    LOBBY = "lobby"
    DYING = "dying"
    SPAWN = "spawn"
    FIGHT = "fight"
    PLAYING = "playing"


@dataclass
class StateClassification:
    state: PlayerState
    confidence: float = 1.0
    note: str = ""


# How long after a death we keep showing the DYING state, even if the overlay
# goes away (player viewing killcam, etc.).
DYING_TRAILING_SECONDS = 8.0


class PlayerStateClassifier:
    """Stateful classifier: feed it (frame, GameState) each tick, get back the
    inferred player state. Tracks recent transitions to smooth flapping."""

    def __init__(self) -> None:
        self._last_death_at: Optional[float] = None
        self._last_state: PlayerState = PlayerState.PLAYING

    def classify(self, frame: Optional["np.ndarray"], state: GameState, ts: float) -> StateClassification:
        # 1. LOBBY: no match (pick screen or pregame splash)
        if frame is not None:
            try:
                if detect_pick_screen_visible(frame) or detect_pregame_splash(frame):
                    self._last_state = PlayerState.LOBBY
                    return StateClassification(PlayerState.LOBBY, 1.0, "pick_screen or splash")
            except Exception:
                pass

        # 2. DYING: death overlay or recent death (trailing window)
        if state.in_death_screen:
            self._last_death_at = ts
            self._last_state = PlayerState.DYING
            return StateClassification(PlayerState.DYING, 1.0, "death_overlay")
        if self._last_death_at is not None and (ts - self._last_death_at) < DYING_TRAILING_SECONDS:
            self._last_state = PlayerState.DYING
            return StateClassification(PlayerState.DYING, 0.7, "trailing_after_death")

        # 3. SPAWN: spawn room signature
        if frame is not None:
            try:
                if detect_spawn_room_visible(frame):
                    self._last_state = PlayerState.SPAWN
                    return StateClassification(PlayerState.SPAWN, 0.8, "spawn_room")
            except Exception:
                pass

        # 4. FIGHT: high health volatility
        if state.fight_intensity >= 0.18:
            self._last_state = PlayerState.FIGHT
            return StateClassification(PlayerState.FIGHT, min(1.0, state.fight_intensity * 2), "fight_intensity")

        # 5. Default: PLAYING
        self._last_state = PlayerState.PLAYING
        return StateClassification(PlayerState.PLAYING, 0.6, "default")
