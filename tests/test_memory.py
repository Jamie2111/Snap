"""Memory layer round-trip tests."""

from __future__ import annotations

import time

from memory import database, player_profile


def test_session_round_trip() -> None:
    conn = database.connect_in_memory()
    player_profile.write_session(
        session_id="abc",
        timestamp=time.time(),
        hero="tracer",
        duration_minutes=10.0,
        deaths=3,
        ult_efficiency_score=80,
        raw_event={},
        feedback_given={},
        allies=["ana", "lucio"],
        enemies=["brigitte", "kiriko"],
        your_comp="hybrid",
        enemy_comp="brawl",
        conn=conn,
    )
    cur = conn.execute("SELECT hero, deaths, ult_efficiency_score FROM sessions WHERE id = ?", ("abc",))
    row = cur.fetchone()
    assert row["hero"] == "tracer"
    assert row["deaths"] == 3
    assert row["ult_efficiency_score"] == 80


def test_matchup_history_counts() -> None:
    conn = database.connect_in_memory()
    for sid in ("a", "b"):
        player_profile.write_session(
            session_id=sid, timestamp=time.time(), hero="tracer", duration_minutes=10.0,
            deaths=2, ult_efficiency_score=70, raw_event={}, feedback_given={},
            allies=["ana"], enemies=["brigitte"], your_comp="hybrid", enemy_comp="brawl",
            conn=conn,
        )
    h = player_profile.get_matchup_history("tracer", "brigitte", conn=conn)
    assert h["sessions_against"] == 2
    assert h["deaths_against"] == 4
