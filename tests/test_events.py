"""Event-detection unit tests."""

from __future__ import annotations

import config
from extractor.events import detect_events_from_stream
from extractor.game_state import GameState


def _ready() -> dict[str, str]:
    return {a: "ready" for a in config.ABILITY_SLOTS}


def test_detects_death_with_full_ult() -> None:
    states = [
        GameState(timestamp=0.0, health_pct=1.0, ult_pct=1.0, cooldowns=_ready()),
        GameState(timestamp=1.0, health_pct=0.0, ult_pct=1.0, in_death_screen=True, cooldowns=_ready()),
    ]
    ev = detect_events_from_stream(states)
    assert len(ev.deaths) == 1
    assert ev.stats.deaths_with_ult_above_80pct == 1
    assert any(u.context == "died_at_full" for u in ev.ults_wasted)


def test_no_death_when_alive() -> None:
    states = [
        GameState(timestamp=t, health_pct=1.0, ult_pct=0.5, cooldowns=_ready())
        for t in range(5)
    ]
    ev = detect_events_from_stream(states)
    assert ev.deaths == []
    assert ev.stats.deaths_total == 0


def test_ult_used_emits_event() -> None:
    states = [
        GameState(timestamp=0.0, health_pct=1.0, ult_pct=1.0, cooldowns=_ready()),
        GameState(timestamp=1.0, health_pct=1.0, ult_pct=0.05, cooldowns=_ready()),
    ]
    ev = detect_events_from_stream(states)
    assert len(ev.ults_used) == 1
