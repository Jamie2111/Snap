"""Feedback engine integration tests."""

from __future__ import annotations

import config
from extractor.events import EventDetector
from extractor.game_state import GameState
from extractor.match_context import MatchContext
from feedback.engine import generate
from memory import database


def _ready() -> dict[str, str]:
    return {a: "ready" for a in config.ABILITY_SLOTS}


def _synth_session_with_ult_death() -> EventDetector:
    det = EventDetector()
    det.ingest(GameState(timestamp=0.0, health_pct=1.0, ult_pct=1.0, cooldowns=_ready()))
    det.ingest(GameState(timestamp=1.0, health_pct=0.0, ult_pct=1.0, in_death_screen=True, cooldowns=_ready()))
    return det


def test_feedback_includes_critical_for_ult_death() -> None:
    det = _synth_session_with_ult_death()
    events = det.finalize()
    match = MatchContext(your_hero="tracer", allies=["ana"], enemies=["mercy"], your_comp="hybrid", enemy_comp="hybrid")
    conn = database.connect_in_memory()
    fb = generate(events, match, db_conn=conn)
    assert len(fb.critical) >= 1
    assert "ult" in fb.critical[0].issue.lower()
    assert fb.session_summary.estimated_avoidable_deaths >= 1


def test_feedback_surfaces_hard_counter_warning() -> None:
    det = _synth_session_with_ult_death()
    events = det.finalize()
    match = MatchContext(
        your_hero="tracer",
        allies=["ana"],
        enemies=["brigitte", "mercy"],
        your_comp="hybrid",
        enemy_comp="hybrid",
    )
    conn = database.connect_in_memory()
    fb = generate(events, match, db_conn=conn)
    has_brig_critical = any("brigitte" in c.issue.lower() for c in fb.critical)
    assert has_brig_critical
