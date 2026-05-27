"""Match context smoothing and comp classification tests."""

from __future__ import annotations

from extractor.match_context import MatchContextTracker, classify_comp
from extractor.ocr import ScoreboardRead


def test_classify_known_comps() -> None:
    assert classify_comp(["reinhardt", "zarya", "brigitte", "lucio", "reaper"]) == "brawl"
    assert classify_comp(["winston", "dva", "tracer", "genji", "ana"]) == "dive"
    assert classify_comp(["sigma", "widowmaker", "ashe", "baptiste", "kiriko"]) == "poke"


def test_tracker_smooths_misreads() -> None:
    tracker = MatchContextTracker(history_size=3)
    tracker.set_initial_hero("tracer")
    reads = [
        ScoreboardRead(your_hero="tracer", allies=["ana"], enemies=["mercy"]),
        ScoreboardRead(your_hero="genji", allies=["ana"], enemies=["mercy"]),
        ScoreboardRead(your_hero="tracer", allies=["ana"], enemies=["mercy"]),
    ]
    for r in reads:
        ctx = tracker.ingest_scoreboard(r)
    assert ctx.your_hero == "tracer"
    assert ctx.allies == ["ana"]
    assert ctx.enemies == ["mercy"]
