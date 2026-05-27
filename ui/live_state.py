"""Shared live state for all Snap UI surfaces.

The capture loop publishes here. Terminal, menu bar, and overlay all read
from the same instance. Thread-safe: a single RLock guards every mutation.
Reads return small snapshot dataclasses so consumers never see torn state.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class LiveSnapshot:
    """A point-in-time read of LiveState. Safe to pass between threads."""
    recording: bool
    started_at: float
    elapsed_seconds: float
    frames_seen: int
    hero: Optional[str]
    allies: tuple[str, ...]
    enemies: tuple[str, ...]
    deaths: int
    ults_used: int
    ults_wasted: int
    last_event: str
    recent_events: tuple[tuple[float, str], ...]
    player_state: str = "playing"
    tip_text: str = ""
    tip_detail: str = ""
    tip_urgency: str = "info"
    match_index: int = 0
    match_result_last: str = ""


class LiveState:
    """Thread-safe live publisher. Updated by the capture loop, read by every
    UI surface. Holding the lock is cheap: every operation is O(1) or small."""

    def __init__(self, recent_event_limit: int = 8) -> None:
        self._lock = threading.RLock()
        self._recording = False
        self._started_at = 0.0
        self._frames_seen = 0
        self._hero: Optional[str] = None
        self._allies: list[str] = []
        self._enemies: list[str] = []
        self._deaths = 0
        self._ults_used = 0
        self._ults_wasted = 0
        self._last_event = ""
        self._recent_events: deque[tuple[float, str]] = deque(maxlen=recent_event_limit)
        self._player_state = "playing"
        self._tip_text = ""
        self._tip_detail = ""
        self._tip_urgency = "info"
        self._match_index = 0
        self._match_result_last = ""

    def start(self) -> None:
        with self._lock:
            self._recording = True
            self._started_at = time.time()

    def stop(self) -> None:
        with self._lock:
            self._recording = False

    def tick_frame(self) -> None:
        with self._lock:
            self._frames_seen += 1

    def set_hero(self, hero: Optional[str]) -> None:
        with self._lock:
            self._hero = hero

    def set_allies(self, allies: list[str]) -> None:
        with self._lock:
            self._allies = list(allies)

    def set_enemies(self, enemies: list[str]) -> None:
        with self._lock:
            self._enemies = list(enemies)

    def record_event(self, label: str, *, death: bool = False, ult_used: bool = False, ult_wasted: bool = False) -> None:
        with self._lock:
            now = time.time() - self._started_at if self._started_at else 0.0
            self._last_event = label
            self._recent_events.append((now, label))
            if death:
                self._deaths += 1
            if ult_used:
                self._ults_used += 1
            if ult_wasted:
                self._ults_wasted += 1

    def set_player_state(self, state: str) -> None:
        with self._lock:
            self._player_state = state

    def set_tip(self, text: str, detail: str = "", urgency: str = "info") -> None:
        with self._lock:
            self._tip_text = text
            self._tip_detail = detail
            self._tip_urgency = urgency

    def set_match_progress(self, match_index: int, last_result: str = "") -> None:
        with self._lock:
            self._match_index = match_index
            if last_result:
                self._match_result_last = last_result

    def snapshot(self) -> LiveSnapshot:
        with self._lock:
            elapsed = (time.time() - self._started_at) if (self._recording and self._started_at) else 0.0
            return LiveSnapshot(
                recording=self._recording,
                started_at=self._started_at,
                elapsed_seconds=elapsed,
                frames_seen=self._frames_seen,
                hero=self._hero,
                allies=tuple(self._allies),
                enemies=tuple(self._enemies),
                deaths=self._deaths,
                ults_used=self._ults_used,
                ults_wasted=self._ults_wasted,
                last_event=self._last_event,
                recent_events=tuple(self._recent_events),
                player_state=self._player_state,
                tip_text=self._tip_text,
                tip_detail=self._tip_detail,
                tip_urgency=self._tip_urgency,
                match_index=self._match_index,
                match_result_last=self._match_result_last,
            )


_GLOBAL: Optional[LiveState] = None


def get() -> LiveState:
    """Process-wide singleton. UIs in different threads share the same state."""
    global _GLOBAL
    if _GLOBAL is None:
        _GLOBAL = LiveState()
    return _GLOBAL
