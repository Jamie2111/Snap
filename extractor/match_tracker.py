"""Segment a session into individual matches.

A single Snap session (one --live capture, one --video pass) may contain
multiple OW2 matches: queue, play, victory/defeat, queue again, play again.
MatchTracker watches the GameState stream and the screen-state detectors and
segments the session into per-match Match records. Each match owns its own
EventDetector, MatchContext, and vision rollups.

Boundary rules:
  - Match opens when the pick screen is visible (CHOOSE YOUR HERO) and no
    match is currently open.
  - Match closes when victory / defeat is detected, OR when 60+ seconds pass
    without any in-game state changes (idle timeout fallback).
  - Hysteresis: once opened, a match must run for at least 10 seconds before
    a close signal counts. Prevents flicker on transient pick-screen reads.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from extractor.events import EventDetector, SessionEvents
from extractor.game_state import (
    GameState,
    detect_defeat_screen,
    detect_pick_screen_visible,
    detect_pregame_splash,
    detect_victory_screen,
)
from extractor.match_context import MatchContext, MatchContextTracker

log = logging.getLogger(__name__)


MATCH_MIN_DURATION_S = 10.0
MATCH_IDLE_TIMEOUT_S = 60.0


@dataclass
class Match:
    """All data Snap collected about a single match within a session."""

    match_index: int
    started_at: float
    ended_at: Optional[float] = None
    result: str = "unknown"  # win | loss | draw | abandoned | unknown
    map_name: Optional[str] = None
    events: SessionEvents = field(default_factory=SessionEvents)
    match_context: MatchContext = field(default_factory=MatchContext)

    @property
    def duration_seconds(self) -> float:
        if self.ended_at is None:
            return 0.0
        return self.ended_at - self.started_at


class MatchTracker:
    """Drives multi-match segmentation. The capture pipeline calls
    ingest_frame() per frame; ingest_state() per GameState; observe_frame_for_hero()
    when scoreboard or pick-screen OCR is wanted. At end of session, finalize()
    returns the list of completed Match records."""

    def __init__(self, initial_hero: Optional[str] = None) -> None:
        self.matches: list[Match] = []
        self._initial_hero = initial_hero
        self._current_match: Optional[Match] = None
        self._current_detector: Optional[EventDetector] = None
        self._current_context_tracker: Optional[MatchContextTracker] = None
        self._last_event_at: Optional[float] = None
        self._session_initial_hero = initial_hero

    def _start_match(self, ts: float) -> None:
        idx = len(self.matches) + 1
        log.info("Match %d started at t=%.1f", idx, ts)
        ctx_tracker = MatchContextTracker()
        if self._session_initial_hero and not self.matches:
            # Carry the session-start hero into the first match only.
            ctx_tracker.set_initial_hero(self._session_initial_hero)
        elif self._current_context_tracker and self._current_context_tracker.context.your_hero:
            # Carry the hero from previous match (player tends to keep heroes).
            ctx_tracker.set_initial_hero(self._current_context_tracker.context.your_hero)
        match = Match(
            match_index=idx,
            started_at=ts,
            events=SessionEvents(),
            match_context=ctx_tracker.context,
        )
        self.matches.append(match)
        self._current_match = match
        self._current_detector = EventDetector()
        self._current_context_tracker = ctx_tracker
        self._last_event_at = ts

    def _close_current_match(self, ts: float, result: str) -> None:
        if self._current_match is None or self._current_detector is None:
            return
        if (ts - self._current_match.started_at) < MATCH_MIN_DURATION_S:
            log.debug("Ignoring close signal: match too young (%.1fs)", ts - self._current_match.started_at)
            return
        self._current_match.ended_at = ts
        self._current_match.result = result
        self._current_match.events = self._current_detector.finalize()
        if self._current_context_tracker is not None:
            self._current_match.match_context = self._current_context_tracker.context
        log.info(
            "Match %d closed: result=%s duration=%.1fs",
            self._current_match.match_index, result, self._current_match.duration_seconds,
        )
        self._current_match = None
        self._current_detector = None
        self._current_context_tracker = None

    def ingest_state(self, state: GameState) -> None:
        """Forward a GameState into the current match's event detector. If no
        match is open yet, open one (treat first state as match start)."""

        ts = state.timestamp
        if self._current_match is None:
            self._start_match(ts)
        if self._current_detector is not None:
            self._current_detector.ingest(state)
        self._last_event_at = ts

    def ingest_frame(self, frame: np.ndarray, ts: float) -> None:
        """Run the screen-state detectors on a frame to update match boundaries."""

        try:
            if detect_victory_screen(frame):
                self._close_current_match(ts, "win")
                return
            if detect_defeat_screen(frame):
                self._close_current_match(ts, "loss")
                return
        except Exception:
            log.exception("victory/defeat detect failed")

        try:
            if detect_pick_screen_visible(frame) or detect_pregame_splash(frame):
                if self._current_match is None:
                    self._start_match(ts)
        except Exception:
            log.exception("pick/pregame detect failed")

        # Idle-timeout fallback: if no state changes for a while, close as abandoned.
        if (
            self._current_match is not None
            and self._last_event_at is not None
            and (ts - self._last_event_at) > MATCH_IDLE_TIMEOUT_S
        ):
            self._close_current_match(ts, "abandoned")

    def observe_frame_for_hero(self, frame: np.ndarray) -> Optional[str]:
        """Delegate hero observation to the current match's context tracker."""
        if self._current_context_tracker is None:
            return None
        try:
            return self._current_context_tracker.observe_frame(frame)
        except Exception:
            log.exception("hero observation failed")
            return None

    def finalize(self) -> list[Match]:
        """Close any open match (treat as abandoned) and return all matches."""
        if self._current_match is not None and self._current_detector is not None:
            ts = self._last_event_at or self._current_match.started_at
            # Use a lenient close: even short final matches are valid if the
            # session ended naturally.
            self._current_match.ended_at = ts
            self._current_match.events = self._current_detector.finalize()
            if self._current_context_tracker is not None:
                self._current_match.match_context = self._current_context_tracker.context
            if self._current_match.result == "unknown":
                self._current_match.result = "abandoned"
            log.info(
                "Session finalize: match %d closed (result=%s, duration=%.1fs)",
                self._current_match.match_index,
                self._current_match.result,
                self._current_match.duration_seconds,
            )
            self._current_match = None
            self._current_detector = None
            self._current_context_tracker = None
        return list(self.matches)


def aggregate_session_stats(matches: list[Match]) -> SessionEvents:
    """Roll per-match SessionEvents up to a single session-level SessionEvents.

    Used for the session-overview panel and for backwards-compat with the
    single-match feedback engine."""

    agg = SessionEvents()
    for m in matches:
        s = m.events.stats
        agg.deaths.extend(m.events.deaths)
        agg.ults_used.extend(m.events.ults_used)
        agg.cooldowns_held.extend(m.events.cooldowns_held)
        agg.fights_engaged.extend(m.events.fights_engaged)
        agg.fights_resolved.extend(m.events.fights_resolved)
        agg.ults_wasted.extend(m.events.ults_wasted)
        agg.stats.deaths_total += s.deaths_total
        agg.stats.deaths_with_ult_above_80pct += s.deaths_with_ult_above_80pct
        agg.stats.deaths_with_available_cooldowns += s.deaths_with_available_cooldowns
        agg.stats.fights_engaged_total += s.fights_engaged_total
        agg.stats.fights_engaged_low_health += s.fights_engaged_low_health
        agg.stats.fight_survival_count += s.fight_survival_count
        agg.stats.ults_used += s.ults_used
        agg.stats.ults_wasted += s.ults_wasted
        agg.stats.ult_hold_durations.extend(s.ult_hold_durations)
        agg.stats.fight_durations.extend(s.fight_durations)
        for ab, holds in s.cooldown_hold_durations.items():
            agg.stats.cooldown_hold_durations.setdefault(ab, []).extend(holds)
        # Vision-derived sums
        agg.stats.aim_frames_with_enemy += s.aim_frames_with_enemy
        agg.stats.aim_frames_on_target += s.aim_frames_on_target
        agg.stats.aim_near_misses += s.aim_near_misses
        agg.stats.screen_flash_count += s.screen_flash_count
        for k, v in s.ability_glow_counts.items():
            agg.stats.ability_glow_counts[k] = agg.stats.ability_glow_counts.get(k, 0) + v
    # Weighted average for aim_avg_miss_px across matches.
    sample_total = sum(m.events.stats.aim_frames_with_enemy for m in matches)
    if sample_total:
        weighted = sum(
            m.events.stats.aim_avg_miss_px * m.events.stats.aim_frames_with_enemy
            for m in matches
        )
        agg.stats.aim_avg_miss_px = round(weighted / sample_total, 1)
    return agg
