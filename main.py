"""Snap entry point.

Modes:
    --live        Live capture (requires Windows + OW2 running). Plays a session,
                  extracts events, asks for initial hero, OCRs scoreboard on Tab,
                  and prints a post-game report when OW2 loses focus.
    --replay DIR  Replay a previously recorded session of PNG frames through the
                  same pipeline. Useful for dev/test on a Mac.
    --demo        Run a canned synthetic session end to end. Verifies the full
                  pipeline without needing OW2 frames.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Optional

import config
from rich.console import Console

log = logging.getLogger("snap.main")

console = Console()


def _prompt_initial_hero() -> Optional[str]:
    try:
        from prompt_hero import prompt  # noqa: F401  optional
    except Exception:
        pass
    console.print("[bold cyan]Snap[/]: what hero are you starting on? (blank to detect via scoreboard)")
    line = sys.stdin.readline().strip().lower().replace(" ", "")
    if not line:
        return None
    if line in config.KNOWN_HEROES:
        return line
    from extractor.ocr import _normalize_hero_name
    return _normalize_hero_name(line)


def run_demo() -> None:
    from extractor.events import EventDetector
    from extractor.game_state import GameState
    from extractor.match_context import MatchContext
    from feedback.engine import generate
    from memory import database, player_profile
    from ui.report import render, write_markdown

    console.print("[bold cyan]Snap[/]: running demo session")

    states: list[GameState] = []
    ts = 0.0
    # Setup: walking around, ult charging
    for _ in range(60):
        states.append(GameState(timestamp=ts, health_pct=1.0, ult_pct=min(0.95, ts / 80.0), cooldowns={a: "ready" for a in config.ABILITY_SLOTS}))
        ts += 1
    # First fight: engage at full hp, ult almost full, abilities ready
    fight_start = ts
    for _ in range(8):
        states.append(GameState(timestamp=ts, health_pct=0.80 - (ts - fight_start) / 20.0, ult_pct=0.95, fight_intensity=0.25, cooldowns={a: "ready" for a in config.ABILITY_SLOTS}))
        ts += 1
    # Death with ult still 95 percent
    states.append(GameState(timestamp=ts, health_pct=0.0, ult_pct=0.95, in_death_screen=True, cooldowns={a: "ready" for a in config.ABILITY_SLOTS}))
    ts += 5
    # Respawn, fight again later
    for _ in range(40):
        states.append(GameState(timestamp=ts, health_pct=1.0, ult_pct=0.30, cooldowns={a: "ready" for a in config.ABILITY_SLOTS}))
        ts += 1
    fight2 = ts
    for _ in range(6):
        states.append(GameState(timestamp=ts, health_pct=0.45, ult_pct=0.40, fight_intensity=0.30, cooldowns={"ability_1": "ready", "ability_2": "cooldown", "ability_3": "ready", "ability_4": "ready"}))
        ts += 1
    # Survive this one
    for _ in range(10):
        states.append(GameState(timestamp=ts, health_pct=0.80, ult_pct=0.45, fight_intensity=0.05))
        ts += 1

    det = EventDetector()
    for s in states:
        det.ingest(s)
    events = det.finalize()

    match = MatchContext(
        your_hero="tracer",
        allies=["ana", "lucio", "reinhardt", "zarya"],
        enemies=["mercy", "kiriko", "reinhardt", "zarya", "brigitte"],
        your_comp="hybrid",
        enemy_comp="brawl",
        map_name="Ilios",
    )

    conn = database.connect()
    feedback = generate(events, match, db_conn=conn)
    session_id = uuid.uuid4().hex[:12]
    player_profile.write_session(
        session_id=session_id,
        timestamp=time.time(),
        hero=match.your_hero,
        duration_minutes=ts / 60.0,
        deaths=events.stats.deaths_total,
        ult_efficiency_score=feedback.session_summary.ult_efficiency_score,
        raw_event={"deaths": events.stats.deaths_total},
        feedback_given={"critical": [c.issue for c in feedback.critical]},
        allies=match.allies,
        enemies=match.enemies,
        your_comp=match.your_comp,
        enemy_comp=match.enemy_comp,
        map_name=match.map_name,
        conn=conn,
    )
    player_profile.write_mistakes_from_events(session_id, events, conn=conn)
    player_profile.update_player_model(session_id, conn=conn)

    render(feedback, console=console)
    md_path = write_markdown(feedback, session_id)
    console.print(f"\n[dim]Markdown report saved to {md_path}[/]")


def run_replay(replay_dir: Path) -> None:
    from capture.screen import replay_iter
    from extractor.events import EventDetector
    from extractor.game_state import extract_state
    from extractor.match_context import MatchContext
    from feedback.engine import generate
    from memory import database, player_profile
    from ui.report import render, write_markdown

    console.print(f"[bold cyan]Snap[/]: replaying frames from {replay_dir}")

    det = EventDetector()
    health_history: list[float] = []
    for cf in replay_iter(replay_dir):
        state = extract_state(cf.frame, cf.timestamp, health_history)
        health_history.append(state.health_pct)
        det.ingest(state)
    events = det.finalize()

    match = MatchContext()
    initial = _prompt_initial_hero()
    if initial:
        match.your_hero = initial

    conn = database.connect()
    feedback = generate(events, match, db_conn=conn)
    session_id = uuid.uuid4().hex[:12]
    player_profile.write_session(
        session_id=session_id,
        timestamp=time.time(),
        hero=match.your_hero,
        duration_minutes=0.0,
        deaths=events.stats.deaths_total,
        ult_efficiency_score=feedback.session_summary.ult_efficiency_score,
        raw_event={"frames": len(health_history)},
        feedback_given={},
        allies=match.allies,
        enemies=match.enemies,
        your_comp=match.your_comp,
        enemy_comp=match.enemy_comp,
        conn=conn,
    )
    player_profile.write_mistakes_from_events(session_id, events, conn=conn)
    player_profile.update_player_model(session_id, conn=conn)

    render(feedback, console=console)
    md_path = write_markdown(feedback, session_id)
    console.print(f"\n[dim]Markdown report saved to {md_path}[/]")


def run_live() -> None:
    if not config.IS_WINDOWS:
        console.print(
            "[bold red]Live mode requires Windows.[/] "
            "You are on a non-Windows platform. Use [bold]--replay[/] or [bold]--demo[/] instead."
        )
        sys.exit(2)

    from capture.screen import live_capture, write_session_manifest
    from extractor.events import EventDetector
    from extractor.game_state import extract_state
    from extractor.match_context import MatchContextTracker
    from feedback.engine import generate
    from memory import database, player_profile
    from ui.display import banner, render_live_status
    from ui.report import render, write_markdown

    banner(console, "SNAP")
    console.print(
        "[dim]Snap will auto-detect your hero from the pick screen, swap banner, or spawn room. "
        "If detection fails, you can set an initial hero now (blank to skip).[/]"
    )
    initial = _prompt_initial_hero()
    tracker = MatchContextTracker()
    if initial:
        tracker.set_initial_hero(initial)
    det = EventDetector()
    health_history: list[float] = []
    frames_seen = 0
    last_event = ""

    session_dir: Optional[Path] = None
    record = None

    for cf, rec, sdir in live_capture(save_frames=False):
        session_dir = sdir
        record = rec
        frames_seen += 1
        try:
            state = extract_state(cf.frame, cf.timestamp, health_history)
        except Exception:
            log.exception("extract_state failed")
            continue
        health_history.append(state.health_pct)
        det.ingest(state)
        try:
            observed = tracker.observe_frame(cf.frame)
            if observed:
                last_event = f"hero observed: {observed}"
        except Exception:
            log.exception("hero-observation pass failed")
        if frames_seen % 20 == 0:
            render_live_status(console, tracker.context, frames_seen, last_event)

    events = det.finalize()
    match = tracker.context
    if initial and not match.your_hero:
        match.your_hero = initial

    conn = database.connect()
    feedback = generate(events, match, db_conn=conn)
    session_id = record.session_id if record else uuid.uuid4().hex[:12]
    player_profile.write_session(
        session_id=session_id,
        timestamp=time.time(),
        hero=match.your_hero,
        duration_minutes=(record.end_time - record.start_time) / 60.0 if record and record.end_time else 0.0,
        deaths=events.stats.deaths_total,
        ult_efficiency_score=feedback.session_summary.ult_efficiency_score,
        raw_event={"frames": frames_seen},
        feedback_given={"critical": [c.issue for c in feedback.critical]},
        allies=match.allies,
        enemies=match.enemies,
        your_comp=match.your_comp,
        enemy_comp=match.enemy_comp,
        conn=conn,
    )
    player_profile.write_mistakes_from_events(session_id, events, conn=conn)
    player_profile.update_player_model(session_id, conn=conn)
    render(feedback, console=console)
    md_path = write_markdown(feedback, session_id)
    console.print(f"\n[dim]Markdown report saved to {md_path}[/]")
    if session_dir is not None and record is not None:
        write_session_manifest(session_dir, record)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="snap")
    parser.add_argument("--live", action="store_true", help="Live capture (Windows + OW2 required)")
    parser.add_argument("--replay", type=Path, help="Replay a session directory of PNG frames")
    parser.add_argument("--demo", action="store_true", help="Run a canned synthetic session")
    parser.add_argument("--debug", action="store_true", help="Verbose logging")
    args = parser.parse_args(argv)

    config.configure_logging(debug=args.debug)

    if args.demo:
        run_demo()
        return 0
    if args.replay:
        run_replay(args.replay)
        return 0
    if args.live:
        run_live()
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
