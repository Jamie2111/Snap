"""Event detection from a GameState stream.

Consumes a sequence of GameStates (one per frame) and emits typed events.
Stateful: the detector remembers the previous frame so it can detect transitions
(health drops, ult usage, death screen onset).

Also maintains rolling session stats that the feedback engine reads at the end.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import config
from extractor.game_state import GameState

log = logging.getLogger(__name__)


@dataclass
class PlayerDeath:
    timestamp: float
    ult_pct_at_death: float
    cooldowns_available: list[str]
    seconds_since_last_ability: float
    seconds_since_last_ult: float
    fight_duration_before_death: float
    death_count_this_game: int
    killed_by: Optional[str] = None


@dataclass
class UltimateUsed:
    timestamp: float
    charge_at_use: float
    held_duration: float
    game_time: float


@dataclass
class CooldownHeld:
    ability: str
    held_ready_duration: float
    context: str


@dataclass
class FightEngaged:
    timestamp: float
    health_at_engage: float
    ult_available: bool
    outcome: str = "pending"


@dataclass
class FightResult:
    timestamp: float
    player_survived: bool
    ult_used_in_fight: bool
    abilities_used: list[str]
    fight_duration: float


@dataclass
class UltWasted:
    timestamp: float
    context: str
    ult_pct: float


@dataclass
class SessionStats:
    deaths_total: int = 0
    deaths_with_ult_above_80pct: int = 0
    deaths_with_available_cooldowns: int = 0
    ult_hold_durations: list[float] = field(default_factory=list)
    cooldown_hold_durations: dict[str, list[float]] = field(default_factory=lambda: {a: [] for a in config.ABILITY_SLOTS})
    fights_engaged_total: int = 0
    fights_engaged_low_health: int = 0
    fight_survival_count: int = 0
    fight_durations: list[float] = field(default_factory=list)
    ults_used: int = 0
    ults_wasted: int = 0

    @property
    def avg_ult_hold_time_after_full(self) -> float:
        if not self.ult_hold_durations:
            return 0.0
        return sum(self.ult_hold_durations) / len(self.ult_hold_durations)

    @property
    def most_held_cooldown(self) -> str:
        best = ("", 0.0)
        for ab, holds in self.cooldown_hold_durations.items():
            avg = sum(holds) / len(holds) if holds else 0.0
            if avg > best[1]:
                best = (ab, avg)
        return best[0]

    @property
    def fight_survival_rate(self) -> float:
        if not self.fights_engaged_total:
            return 0.0
        return self.fight_survival_count / self.fights_engaged_total

    @property
    def avg_fight_duration(self) -> float:
        if not self.fight_durations:
            return 0.0
        return sum(self.fight_durations) / len(self.fight_durations)


@dataclass
class SessionEvents:
    deaths: list[PlayerDeath] = field(default_factory=list)
    ults_used: list[UltimateUsed] = field(default_factory=list)
    cooldowns_held: list[CooldownHeld] = field(default_factory=list)
    fights_engaged: list[FightEngaged] = field(default_factory=list)
    fights_resolved: list[FightResult] = field(default_factory=list)
    ults_wasted: list[UltWasted] = field(default_factory=list)
    stats: SessionStats = field(default_factory=SessionStats)


class EventDetector:
    """Streaming event detector. Feed it GameStates in order; query .events
    when the session ends."""

    DEATH_THRESHOLD = 0.05
    ULT_USE_DROP = 0.40
    ULT_WASTE_THRESHOLD = 0.80
    HELD_COOLDOWN_THRESHOLD_S = 6.0
    FIGHT_ENGAGE_INTENSITY = 0.15
    FIGHT_END_QUIET_S = 4.0
    LOW_HEALTH_ENGAGE = 0.50

    def __init__(self) -> None:
        self.events = SessionEvents()
        self._prev: Optional[GameState] = None
        self._prev_alive_state: Optional[GameState] = None
        self._cooldown_ready_since: dict[str, Optional[float]] = {a: None for a in config.ABILITY_SLOTS}
        self._last_ability_use_at: float = 0.0
        self._last_ult_use_at: float = 0.0
        self._ult_full_since: Optional[float] = None
        self._in_fight: bool = False
        self._fight_started_at: Optional[float] = None
        self._fight_health_at_engage: Optional[float] = None
        self._fight_ult_available: bool = False
        self._fight_abilities_used: list[str] = []
        self._fight_ult_used: bool = False
        self._last_active_at: float = 0.0

    def ingest(self, state: GameState) -> None:
        if self._prev is None:
            self._prev = state
            self._init_baselines(state)
            return

        self._detect_death(state)
        self._detect_ult_used(state)
        self._track_cooldowns(state)
        self._track_fight_state(state)

        self._prev = state
        if not state.in_death_screen:
            self._prev_alive_state = state

    def finalize(self) -> SessionEvents:
        # Close any open fight with a draw outcome.
        if self._in_fight and self._prev is not None:
            self._close_fight(self._prev.timestamp, survived=not self._prev.in_death_screen)
        return self.events

    def _init_baselines(self, state: GameState) -> None:
        now = state.timestamp
        for ab, status in state.cooldowns.items():
            if status == "ready":
                self._cooldown_ready_since[ab] = now
        if state.ult_pct >= 0.95:
            self._ult_full_since = now
        self._prev_alive_state = state if not state.in_death_screen else None
        self._last_active_at = now

    def _detect_death(self, state: GameState) -> None:
        assert self._prev is not None
        if state.in_death_screen and not self._prev.in_death_screen:
            ref = self._prev_alive_state or self._prev
            cds_available = [ab for ab, status in ref.cooldowns.items() if status == "ready"]
            ult_pct = ref.ult_pct
            fight_duration = (
                state.timestamp - self._fight_started_at if self._fight_started_at else 0.0
            )
            self.events.stats.deaths_total += 1
            if ult_pct >= self.ULT_WASTE_THRESHOLD:
                self.events.stats.deaths_with_ult_above_80pct += 1
                self.events.ults_wasted.append(
                    UltWasted(timestamp=state.timestamp, context="died_at_full", ult_pct=ult_pct)
                )
            if cds_available:
                self.events.stats.deaths_with_available_cooldowns += 1
                for ab in cds_available:
                    held_for = (
                        state.timestamp - (self._cooldown_ready_since.get(ab) or state.timestamp)
                    )
                    self.events.cooldowns_held.append(
                        CooldownHeld(ability=ab, held_ready_duration=held_for, context="died_holding")
                    )
            self.events.deaths.append(
                PlayerDeath(
                    timestamp=state.timestamp,
                    ult_pct_at_death=ult_pct,
                    cooldowns_available=cds_available,
                    seconds_since_last_ability=state.timestamp - self._last_ability_use_at if self._last_ability_use_at else 0.0,
                    seconds_since_last_ult=state.timestamp - self._last_ult_use_at if self._last_ult_use_at else 0.0,
                    fight_duration_before_death=fight_duration,
                    death_count_this_game=self.events.stats.deaths_total,
                )
            )
            if self._in_fight:
                self._close_fight(state.timestamp, survived=False)

    def _detect_ult_used(self, state: GameState) -> None:
        assert self._prev is not None
        prev_ult = self._prev.ult_pct
        if prev_ult >= 0.95 and self._ult_full_since is None:
            self._ult_full_since = self._prev.timestamp
        if prev_ult - state.ult_pct >= self.ULT_USE_DROP and prev_ult >= 0.85:
            held = (state.timestamp - self._ult_full_since) if self._ult_full_since else 0.0
            self.events.ults_used.append(
                UltimateUsed(
                    timestamp=state.timestamp,
                    charge_at_use=prev_ult,
                    held_duration=held,
                    game_time=state.timestamp,
                )
            )
            self.events.stats.ults_used += 1
            self.events.stats.ult_hold_durations.append(held)
            self._last_ult_use_at = state.timestamp
            self._ult_full_since = None
            self._fight_ult_used = True

    def _track_cooldowns(self, state: GameState) -> None:
        assert self._prev is not None
        for ab, status in state.cooldowns.items():
            prev_status = self._prev.cooldowns.get(ab, "ready")
            if status == "ready" and self._cooldown_ready_since.get(ab) is None:
                self._cooldown_ready_since[ab] = state.timestamp
            if status != "ready" and prev_status == "ready":
                ready_since = self._cooldown_ready_since.get(ab)
                if ready_since is not None:
                    held = state.timestamp - ready_since
                    self.events.stats.cooldown_hold_durations[ab].append(held)
                    if held >= self.HELD_COOLDOWN_THRESHOLD_S:
                        context = "used_late" if held >= 10.0 else "fight_ended_holding"
                        self.events.cooldowns_held.append(
                            CooldownHeld(ability=ab, held_ready_duration=held, context=context)
                        )
                    self._last_ability_use_at = state.timestamp
                    if self._in_fight:
                        self._fight_abilities_used.append(ab)
                self._cooldown_ready_since[ab] = None

    def _track_fight_state(self, state: GameState) -> None:
        if state.fight_intensity >= self.FIGHT_ENGAGE_INTENSITY:
            self._last_active_at = state.timestamp
            if not self._in_fight:
                self._open_fight(state)
        elif self._in_fight:
            quiet_for = state.timestamp - self._last_active_at
            if quiet_for >= self.FIGHT_END_QUIET_S:
                self._close_fight(state.timestamp, survived=not state.in_death_screen)

    def _open_fight(self, state: GameState) -> None:
        self._in_fight = True
        self._fight_started_at = state.timestamp
        self._fight_health_at_engage = state.health_pct
        self._fight_ult_available = state.ult_pct >= 0.95
        self._fight_abilities_used = []
        self._fight_ult_used = False
        self.events.stats.fights_engaged_total += 1
        if state.health_pct < self.LOW_HEALTH_ENGAGE:
            self.events.stats.fights_engaged_low_health += 1
        self.events.fights_engaged.append(
            FightEngaged(
                timestamp=state.timestamp,
                health_at_engage=state.health_pct,
                ult_available=self._fight_ult_available,
            )
        )

    def _close_fight(self, ts: float, survived: bool) -> None:
        if self._fight_started_at is None:
            self._in_fight = False
            return
        duration = ts - self._fight_started_at
        self.events.fights_resolved.append(
            FightResult(
                timestamp=ts,
                player_survived=survived,
                ult_used_in_fight=self._fight_ult_used,
                abilities_used=list(self._fight_abilities_used),
                fight_duration=duration,
            )
        )
        self.events.stats.fight_durations.append(duration)
        if survived:
            self.events.stats.fight_survival_count += 1
        # Update last engaged fight's outcome retrospectively
        if self.events.fights_engaged:
            self.events.fights_engaged[-1].outcome = "won" if survived else "lost"
        self._in_fight = False
        self._fight_started_at = None
        self._fight_health_at_engage = None
        self._fight_ult_available = False
        self._fight_abilities_used = []
        self._fight_ult_used = False


def detect_events_from_stream(states: list[GameState]) -> SessionEvents:
    """Convenience for tests: drive the detector with a finite list."""

    det = EventDetector()
    for s in states:
        det.ingest(s)
    return det.finalize()
