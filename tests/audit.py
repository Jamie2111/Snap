"""End-to-end audit: prove Snap's coaching is hero-specific.

Walks through canonical scenarios for several heroes and prints what Snap
actually says. Run this whenever you want to see the real text the user
will see, with no synthetic mechanics fakes (vision metrics are skipped).

Usage:
    python -m tests.audit
"""

from __future__ import annotations

import sys

import config
from extractor.events import EventDetector
from extractor.game_state import GameState
from extractor.match_context import MatchContext
from extractor.match_tracker import Match
from feedback.engine import generate_for_matches
from feedback.realtime import generate as realtime_generate
from extractor.player_state import PlayerState
from memory import database


def _build_match(idx, *, hero, allies, enemies, comp, enemy_comp, map_name,
                 result, with_ult_death=False, slot_uses=None):
    det = EventDetector()
    ts = 0.0
    slot_uses = slot_uses or {}

    # Burn 3 minutes of session (so benchmark thresholds activate)
    for _ in range(180):
        det.ingest(GameState(timestamp=ts, health_pct=1.0, ult_pct=min(1.0, ts/100),
                             cooldowns={a: "ready" for a in config.ABILITY_SLOTS}))
        ts += 1
    # Force ability cooldown transitions to count slot uses
    for slot, n in slot_uses.items():
        for _ in range(n):
            det.ingest(GameState(timestamp=ts, health_pct=1.0, ult_pct=0.9,
                                 cooldowns={a: ("cooldown" if a == slot else "ready") for a in config.ABILITY_SLOTS}))
            ts += 1
            det.ingest(GameState(timestamp=ts, health_pct=1.0, ult_pct=0.9,
                                 cooldowns={a: "ready" for a in config.ABILITY_SLOTS}))
            ts += 1
    if with_ult_death:
        for _ in range(5):
            det.ingest(GameState(timestamp=ts, health_pct=0.6, ult_pct=1.0,
                                 fight_intensity=0.25,
                                 cooldowns={a: "ready" for a in config.ABILITY_SLOTS}))
            ts += 1
        det.ingest(GameState(timestamp=ts, health_pct=0.0, ult_pct=1.0,
                             in_death_screen=True,
                             cooldowns={a: "ready" for a in config.ABILITY_SLOTS}))
        ts += 5
    return Match(
        match_index=idx, started_at=0.0, ended_at=ts,
        map_name=map_name, result=result,
        events=det.finalize(),
        match_context=MatchContext(
            your_hero=hero, allies=allies, enemies=enemies,
            your_comp=comp, enemy_comp=enemy_comp,
        ),
    )


def _print_section(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def _print_feedback(fb, label):
    print()
    print(f"--- {label} ---")
    print(f"Hero: {fb.match_context.your_hero if fb.match_context else '?'}")
    print(f"Grade: {fb.session_summary.session_grade}  "
          f"Ult: {fb.session_summary.ult_efficiency_score}/100  "
          f"Deaths: {fb.session_summary.deaths}")
    print()
    if fb.critical:
        print("CRITICAL:")
        for c in fb.critical[:3]:
            print(f"  ● {c.render()[:300]}")
        print()
    if fb.matchups:
        print("MATCHUPS (top 5):")
        for m in fb.matchups[:5]:
            tip = (m.advice[0] if m.advice else m.key_threat)[:120]
            print(f"  {m.side[:8]:>8}  {m.enemy:12}  ({m.difficulty:10}) {tip}")
        print()
    if fb.stats:
        print("STATS (those with enough_data):")
        for s in fb.stats:
            if s.enough_data and s.benchmark is not None:
                print(f"  {s.label}: {s.value}{s.unit}  target {s.benchmark}{s.unit}  ({s.status})")
        print()
    if fb.one_thing_to_focus_on:
        print(f"FOCUS: {fb.one_thing_to_focus_on[:250]}")


def _print_realtime(state, hero, enemies, last_death=None, last_match_focus=None, label=""):
    tip = realtime_generate(
        state=state, hero=hero, enemies=enemies,
        last_death=last_death, last_match_focus=last_match_focus,
    )
    hero_str = (hero or "(none)")[:11]
    enemies_str = (','.join(enemies) if enemies else "(none)")[:30]
    print(f"  [{state.value:8}] {hero_str:11} vs {enemies_str:30}  ->  ", end="")
    if tip is None:
        print(f"(silent)")
    else:
        print(f"\"{tip.text}\"")
        if tip.detail:
            print(f"                                                                  detail: {tip.detail[:140]}")


def main():
    conn = database.connect_in_memory()

    _print_section("1. TRACER vs counter comp (Brigitte + Cassidy + Sombra)")
    match = _build_match(
        1, hero="tracer",
        allies=["ana", "lucio", "reinhardt", "zarya"],
        enemies=["brigitte", "cassidy", "sombra", "reinhardt", "zarya"],
        comp="hybrid", enemy_comp="anti_dive", map_name="King's Row",
        result="loss", with_ult_death=True,
        slot_uses={"ability_1": 18, "ability_2": 2},  # 18 blinks, 2 recalls
    )
    fb = generate_for_matches([match], db_conn=conn)
    _print_feedback(fb, "Tracer dies with pulse @ 100% vs Brig/Cass/Sombra")

    _print_section("2. ANA vs dive comp (Winston + Tracer + Genji)")
    match = _build_match(
        1, hero="ana",
        allies=["lucio", "reinhardt", "zarya", "tracer"],
        enemies=["winston", "tracer", "genji", "reinhardt", "kiriko"],
        comp="brawl", enemy_comp="dive", map_name="Numbani",
        result="loss", with_ult_death=True,
        slot_uses={"ability_1": 4, "ability_2": 6},  # 4 sleep darts, 6 nades
    )
    fb = generate_for_matches([match], db_conn=conn)
    _print_feedback(fb, "Ana dies with nano @ 100% vs Winston dive")

    _print_section("3. REINHARDT vs poke comp (Sigma + Ashe + Widow)")
    match = _build_match(
        1, hero="reinhardt",
        allies=["ana", "mercy", "zarya", "tracer"],
        enemies=["sigma", "ashe", "widowmaker", "ana", "lucio"],
        comp="brawl", enemy_comp="poke", map_name="Havana",
        result="loss", with_ult_death=True,
        slot_uses={"ability_1": 12, "ability_2": 3},
    )
    fb = generate_for_matches([match], db_conn=conn)
    _print_feedback(fb, "Rein dies with shatter @ 100% vs Sigma poke")

    _print_section("4. MERCY vs dive comp (Tracer + Genji)")
    match = _build_match(
        1, hero="mercy",
        allies=["ana", "reinhardt", "zarya", "soldier76"],
        enemies=["tracer", "genji", "winston", "kiriko", "ana"],
        comp="hybrid", enemy_comp="dive", map_name="Lijiang",
        result="loss", with_ult_death=False,
        slot_uses={"ability_1": 30},
    )
    fb = generate_for_matches([match], db_conn=conn)
    _print_feedback(fb, "Mercy survives dive comp")

    _print_section("5. WINSTON dive setup")
    match = _build_match(
        1, hero="winston",
        allies=["ana", "kiriko", "tracer", "sojourn"],
        enemies=["reaper", "brigitte", "reinhardt", "zarya", "moira"],
        comp="dive", enemy_comp="brawl", map_name="Junkertown",
        result="loss", with_ult_death=True,
        slot_uses={"ability_1": 8, "ability_2": 6},
    )
    fb = generate_for_matches([match], db_conn=conn)
    _print_feedback(fb, "Winston dies with primal @ 100% vs Reaper/Brig")

    _print_section("6. REAL-TIME TIPS BY STATE (proves no generic strings)")
    print()
    print("  PlayerState.FIGHT  (terse, glanceable):")
    _print_realtime(PlayerState.FIGHT, "tracer", ["brigitte"], label="fight")
    _print_realtime(PlayerState.FIGHT, "ana", ["winston"], label="fight")
    _print_realtime(PlayerState.FIGHT, "genji", ["moira"], label="fight")
    print()
    print("  PlayerState.SPAWN  (one-sentence reminder):")
    _print_realtime(PlayerState.SPAWN, "tracer", ["brigitte", "cassidy"], label="spawn")
    _print_realtime(PlayerState.SPAWN, "ana", ["winston", "tracer"], label="spawn")
    _print_realtime(PlayerState.SPAWN, "widowmaker", ["sombra", "tracer"], label="spawn")
    print()
    print("  PlayerState.LOBBY  (full matchup briefing):")
    _print_realtime(PlayerState.LOBBY, "tracer", ["brigitte", "cassidy", "sombra"], label="lobby")
    _print_realtime(PlayerState.LOBBY, "ana", ["winston", "tracer", "genji"], label="lobby")
    print()
    print("  PlayerState.DYING  (root cause):")
    from extractor.events import PlayerDeath
    d = PlayerDeath(timestamp=300.0, ult_pct_at_death=0.95,
                    cooldowns_available=["ability_1"],
                    seconds_since_last_ability=12, seconds_since_last_ult=30,
                    fight_duration_before_death=8, death_count_this_game=2)
    _print_realtime(PlayerState.DYING, "tracer", ["brigitte"], last_death=d, label="dying")
    _print_realtime(PlayerState.DYING, "ana", ["winston"], last_death=d, label="dying")
    _print_realtime(PlayerState.DYING, "reinhardt", ["sigma"], last_death=d, label="dying")

    _print_section("7. UNKNOWN HERO / MISSING DATA")
    print()
    print("  No hero, no enemies (cold start):")
    _print_realtime(PlayerState.LOBBY, None, [], label="cold")
    _print_realtime(PlayerState.SPAWN, None, [], label="cold")
    _print_realtime(PlayerState.FIGHT, None, [], label="cold")
    print()
    print("  Hero with no matchup data (Symmetra):")
    _print_realtime(PlayerState.LOBBY, "symmetra", ["tracer", "genji"], label="missing")
    _print_realtime(PlayerState.SPAWN, "symmetra", ["tracer", "genji"], label="missing")

    print()
    print("=" * 78)
    print("AUDIT COMPLETE")
    print("=" * 78)


if __name__ == "__main__":
    main()
