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


def _run_offline_pipeline(
    frame_source,
    source_label: str,
    initial_hero: Optional[str] = None,
) -> None:
    """Common pipeline for offline modes (--replay, --video). Iterates frames,
    extracts state per frame, runs the hero observer (pick screen / spawn room
    / scoreboard OCR), detects events, generates feedback, renders + saves the
    report."""

    from extractor.events import EventDetector
    from extractor.game_state import extract_state
    from extractor.match_context import MatchContextTracker
    from feedback.engine import generate
    from memory import database, player_profile
    from ui.report import render, write_markdown

    console.print(f"[bold cyan]Snap[/]: {source_label}")

    tracker = MatchContextTracker()
    if initial_hero:
        tracker.set_initial_hero(initial_hero)

    det = EventDetector()
    health_history: list[float] = []
    frames_processed = 0
    for cf in frame_source:
        try:
            state = extract_state(cf.frame, cf.timestamp, health_history)
        except Exception:
            log.exception("extract_state failed on frame %d", frames_processed)
            continue
        health_history.append(state.health_pct)
        det.ingest(state)
        try:
            tracker.observe_frame(cf.frame)
        except Exception:
            log.exception("hero-observation pass failed on frame %d", frames_processed)
        frames_processed += 1
    events = det.finalize()
    match = tracker.context

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
        raw_event={"frames": frames_processed},
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
    console.print(f"\n[dim]Processed {frames_processed} frames. Markdown report: {md_path}[/]")


def run_replay(replay_dir: Path, initial_hero: Optional[str] = None) -> None:
    from capture.screen import replay_iter

    _run_offline_pipeline(
        replay_iter(replay_dir),
        f"replaying frames from {replay_dir}",
        initial_hero=initial_hero or _prompt_initial_hero(),
    )


def run_video(video_path: Path, initial_hero: Optional[str] = None) -> None:
    from capture.screen import video_iter

    _run_offline_pipeline(
        video_iter(video_path),
        f"processing video {video_path}",
        initial_hero=initial_hero or _prompt_initial_hero(),
    )


def _looks_like_url(arg: str) -> bool:
    return arg.startswith("http://") or arg.startswith("https://")


def _download_youtube(url: str) -> Path:
    """Download a YouTube video via yt-dlp into data/sessions/. Returns the
    final merged file path. Requires yt-dlp installed (brew install yt-dlp)."""

    import re
    import shutil
    import subprocess

    if shutil.which("yt-dlp") is None:
        raise RuntimeError("yt-dlp is not installed. Run: brew install yt-dlp")

    match = re.search(r"(?:v=|youtu\.be/|/shorts/|/embed/)([\w-]{11})", url)
    video_id = match.group(1) if match else uuid.uuid4().hex[:11]
    out_template = str(config.SESSIONS_DIR / f"snap_vod_{video_id}.%(ext)s")
    console.print(f"[bold cyan]Snap[/]: downloading {url} via yt-dlp")
    proc = subprocess.run(
        [
            "yt-dlp",
            "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
            "-o", out_template,
            "--no-warnings",
            url,
        ],
    )
    if proc.returncode != 0:
        raise RuntimeError(f"yt-dlp download failed with exit code {proc.returncode}")
    video_exts = {".mp4", ".mkv", ".webm", ".mov"}
    candidates = sorted(
        (p for p in config.SESSIONS_DIR.glob(f"snap_vod_{video_id}.*") if p.suffix.lower() in video_exts),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise RuntimeError(f"yt-dlp completed but no video file found for {video_id}")
    log.info("Downloaded to %s", candidates[0])
    return candidates[0]


def run_vod(video_path_or_url: str, title: Optional[str] = None) -> None:
    """Ingest a VOD review: run the visual pipeline on the video to extract
    in-video events, transcribe the audio with Whisper, tag hero/ability/concept
    mentions, correlate quotes to events, persist everything to SQLite.

    Accepts either a local file path OR a YouTube URL (downloads first via
    yt-dlp). Once ingested, the Coach Said tier in future session reports
    surfaces relevant quotes whenever the player's session matches a topic a
    coach has previously discussed."""

    from capture.screen import video_iter
    from extractor.events import EventDetector
    from extractor.game_state import extract_state
    from extractor.vod import ingest_vod
    from memory import database

    source_url: Optional[str] = None
    if _looks_like_url(str(video_path_or_url)):
        source_url = str(video_path_or_url)
        try:
            video_path = _download_youtube(source_url)
        except RuntimeError as e:
            console.print(f"[bold red]{e}[/]")
            return
    else:
        video_path = Path(video_path_or_url)

    console.print(f"[bold cyan]Snap[/]: ingesting VOD {video_path}")
    if not video_path.exists():
        console.print(f"[bold red]Not found:[/] {video_path}")
        return

    # Pass 1: run the visual pipeline to extract in-video events.
    console.print("[dim]Pass 1/2: extracting in-video game events...[/]")
    det = EventDetector()
    health_history: list[float] = []
    frames_processed = 0
    for cf in video_iter(video_path):
        try:
            state = extract_state(cf.frame, cf.timestamp, health_history)
        except Exception:
            log.exception("extract_state failed on frame %d", frames_processed)
            continue
        health_history.append(state.health_pct)
        det.ingest(state)
        frames_processed += 1
    events = det.finalize()
    console.print(
        f"[dim]  {frames_processed} frames, "
        f"{events.stats.deaths_total} death(s), "
        f"{events.stats.ults_wasted} wasted ult(s)[/]"
    )

    # Pass 2: transcribe + tag + correlate.
    console.print("[dim]Pass 2/2: transcribing audio and tagging quotes (first run downloads ~150MB)...[/]")
    conn = database.connect()
    try:
        summary = ingest_vod(video_path, events, conn=conn, source_url=source_url, title=title)
    except ImportError as e:
        console.print(f"[bold red]{e}[/]\nRun: [cyan]pip install faster-whisper[/]")
        return
    except FileNotFoundError as e:
        console.print(f"[bold red]Audio extraction failed.[/] Install ffmpeg:\n  brew install ffmpeg\n({e})")
        return

    console.print(
        f"\n[green]VOD ingested.[/] "
        f"review_id={summary['review_id']}, "
        f"transcript={summary['segments']} segs, "
        f"tagged={summary['tagged_quotes']} quotes, "
        f"correlations={summary['correlations']}, "
        f"duration={summary['duration_seconds']:.1f}s"
    )
    console.print(
        "[dim]Future session reports will surface relevant quotes in the 'Coach Said' panel.[/]"
    )


def _start_overlay_subprocess() -> Optional["subprocess.Popen"]:
    """Spawn ui/overlay.py as a child process. We pipe JSON snapshots to its
    stdin so it can run its own Tk loop without fighting rumps for the main
    thread."""
    import subprocess
    import sys as _sys
    try:
        proc = subprocess.Popen(
            [_sys.executable, "-m", "ui.overlay"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=str(config.BASE_DIR),
        )
        return proc
    except Exception:
        log.exception("Failed to launch overlay subprocess")
        return None


def _capture_worker(
    state,  # LiveState
    duration_seconds: Optional[int],
    stop_event,  # threading.Event
    result: dict,
    overlay_proc=None,
) -> None:
    """Background thread: runs the capture loop, publishes to LiveState, and
    stores final events / context in `result` for the main thread to consume
    after the worker finishes."""

    import json as _json
    from capture.screen import live_capture, write_session_manifest
    from extractor.events import EventDetector
    from extractor.game_state import extract_state
    from extractor.match_context import MatchContextTracker

    tracker = MatchContextTracker()
    if result.get("initial_hero"):
        tracker.set_initial_hero(result["initial_hero"])
        state.set_hero(result["initial_hero"])
    det = EventDetector()
    health_history: list[float] = []
    session_dir: Optional[Path] = None
    record = None
    start_time = time.monotonic()
    stopped_reason = "completed"
    prev_death_count = 0
    prev_ults_used = 0
    prev_ults_wasted = 0
    state.start()

    def push_overlay():
        if not overlay_proc or not overlay_proc.stdin:
            return
        try:
            snap = state.snapshot()
            payload = {
                "recording": snap.recording,
                "elapsed_seconds": snap.elapsed_seconds,
                "hero": snap.hero,
                "last_event": snap.last_event,
            }
            overlay_proc.stdin.write((_json.dumps(payload) + "\n").encode())
            overlay_proc.stdin.flush()
        except Exception:
            pass

    try:
        for cf, rec, sdir in live_capture(save_frames=False):
            if stop_event.is_set():
                stopped_reason = "ui_stop"
                break
            session_dir = sdir
            record = rec
            state.tick_frame()
            try:
                gs = extract_state(cf.frame, cf.timestamp, health_history)
            except Exception:
                log.exception("extract_state failed")
                continue
            health_history.append(gs.health_pct)
            det.ingest(gs)
            try:
                observed = tracker.observe_frame(cf.frame)
                if observed:
                    state.record_event(f"hero confirmed: {observed}")
            except Exception:
                log.exception("hero-observation pass failed")
            ctx = tracker.context
            if ctx.your_hero:
                state.set_hero(ctx.your_hero)
            if ctx.allies:
                state.set_allies(list(ctx.allies))
            if ctx.enemies:
                state.set_enemies(list(ctx.enemies))
            stats = det.events.stats
            if stats.deaths_total > prev_death_count:
                state.record_event("Death", death=True)
                prev_death_count = stats.deaths_total
            if stats.ults_used > prev_ults_used:
                state.record_event("Ult used", ult_used=True)
                prev_ults_used = stats.ults_used
            if stats.ults_wasted > prev_ults_wasted:
                state.record_event("Ult wasted", ult_wasted=True)
                prev_ults_wasted = stats.ults_wasted
            push_overlay()
            if duration_seconds and (time.monotonic() - start_time) >= duration_seconds:
                stopped_reason = "duration_reached"
                break
    except Exception:
        log.exception("capture loop crashed")
        stopped_reason = "error"
    finally:
        state.stop()
        push_overlay()
        result["events"] = det.finalize()
        result["match"] = tracker.context
        result["session_dir"] = session_dir
        result["record"] = record
        result["stopped_reason"] = stopped_reason


def run_live(
    duration_seconds: Optional[int] = None,
    initial_hero: Optional[str] = None,
    menubar: bool = True,
    overlay: bool = True,
) -> None:
    import threading

    from feedback.engine import generate
    from memory import database, player_profile
    from ui import live_state
    from ui.display import live_panel
    from ui.report import render, write_markdown

    state = live_state.get()

    console.rule("[bold]SNAP")
    if config.IS_WINDOWS:
        console.print(
            "[dim]Snap captures OW2 and auto-stops when it loses focus. "
            "Hero is auto-detected from pick screen / swap banner / spawn room / scoreboard.[/]"
        )
    else:
        console.print(
            "[dim]Mac live mode. Fullscreen the OW2 footage for best results. "
            "Press [bold]Ctrl+C[/] (or Stop in the menu bar) to end the session. "
            "macOS will prompt for Screen Recording permission the first time.[/]"
        )
        if duration_seconds:
            console.print(f"[dim]Auto-stop after {duration_seconds}s.[/]")

    initial = initial_hero or _prompt_initial_hero()

    overlay_proc = _start_overlay_subprocess() if overlay else None

    stop_event = threading.Event()
    result: dict = {"initial_hero": initial}

    worker = threading.Thread(
        target=_capture_worker,
        args=(state, duration_seconds, stop_event, result, overlay_proc),
        daemon=True,
    )
    worker.start()

    run_menubar = menubar and config.IS_MAC
    try:
        if run_menubar:
            try:
                from ui import menubar as menubar_mod
                menubar_mod.run(state, on_stop=lambda: stop_event.set())
            except Exception:
                log.exception("menu bar UI failed; falling back to terminal-only")
                _await_with_terminal(state, worker, stop_event)
        else:
            _await_with_terminal(state, worker, stop_event)
    except KeyboardInterrupt:
        stop_event.set()
        console.print("\n[yellow]Stopping capture (Ctrl+C). Finalizing report...[/]")
    finally:
        worker.join(timeout=10.0)
        if overlay_proc:
            try:
                overlay_proc.terminate()
            except Exception:
                pass

    events = result.get("events")
    match = result.get("match")
    if events is None or match is None:
        console.print(
            "[bold red]No frames captured.[/] "
            "If you're on macOS, grant Screen Recording permission in "
            "System Settings > Privacy & Security > Screen Recording, then restart your terminal."
        )
        return
    if state.snapshot().frames_seen == 0:
        console.print(
            "[bold red]No frames captured.[/] "
            "If you're on macOS, grant Screen Recording permission in "
            "System Settings > Privacy & Security > Screen Recording, then restart your terminal."
        )
        return

    if initial and not match.your_hero:
        match.your_hero = initial

    conn = database.connect()
    feedback = generate(events, match, db_conn=conn)
    record = result.get("record")
    session_id = record.session_id if record else uuid.uuid4().hex[:12]
    player_profile.write_session(
        session_id=session_id,
        timestamp=time.time(),
        hero=match.your_hero,
        duration_minutes=(record.end_time - record.start_time) / 60.0 if record and record.end_time else 0.0,
        deaths=events.stats.deaths_total,
        ult_efficiency_score=feedback.session_summary.ult_efficiency_score,
        raw_event={"frames": state.snapshot().frames_seen, "stopped_reason": result.get("stopped_reason")},
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
    console.print(
        f"\n[dim]Processed {state.snapshot().frames_seen} frames "
        f"({result.get('stopped_reason')}). Markdown report: {md_path}[/]"
    )
    if result.get("session_dir") is not None and record is not None:
        from capture.screen import write_session_manifest
        write_session_manifest(result["session_dir"], record)


def _await_with_terminal(state, worker, stop_event) -> None:
    """Main thread: show the live Rich panel until the capture worker exits
    or the user hits Ctrl+C."""
    from ui.display import live_panel
    try:
        with live_panel(state, console=console):
            while worker.is_alive():
                worker.join(timeout=0.5)
    except KeyboardInterrupt:
        stop_event.set()
        raise


def run_list_vods() -> None:
    """List every ingested VOD review with quote / correlation counts, plus
    a concept-distribution rollup across the whole library."""

    import datetime as dt
    import json as _json
    from collections import Counter

    from rich.box import ROUNDED as _ROUNDED
    from rich.table import Table

    from memory import database

    conn = database.connect()
    rows = conn.execute(
        """
        SELECT v.id, v.title, v.source, v.ingested_at, v.duration_seconds,
               COUNT(DISTINCT q.id) AS quote_count,
               COUNT(DISTINCT c.id) AS correlation_count
          FROM vod_reviews v
          LEFT JOIN vod_quotes q ON q.review_id = v.id
          LEFT JOIN vod_correlations c ON c.review_id = v.id
         GROUP BY v.id
         ORDER BY v.ingested_at DESC
        """
    ).fetchall()

    if not rows:
        console.print(
            "[yellow]No VODs ingested yet.[/] "
            "Run [cyan]python main.py --vod <file-or-url>[/] to add one."
        )
        return

    table = Table(title=f"Ingested VOD Reviews ({len(rows)})", box=_ROUNDED, show_lines=False)
    table.add_column("Review ID", style="cyan")
    table.add_column("Title")
    table.add_column("Duration", justify="right")
    table.add_column("Quotes", justify="right", style="green")
    table.add_column("Correlations", justify="right", style="magenta")
    table.add_column("Ingested")
    for r in rows:
        ingested = dt.datetime.fromtimestamp(r["ingested_at"]).strftime("%Y-%m-%d %H:%M")
        dur_min = (r["duration_seconds"] or 0) / 60.0
        table.add_row(
            r["id"][:8],
            (r["title"] or r["source"] or "")[:50] or "(untitled)",
            f"{dur_min:.0f} min",
            str(r["quote_count"]),
            str(r["correlation_count"]),
            ingested,
        )
    console.print(table)

    concept_rows = conn.execute("SELECT concepts_json, heroes_json FROM vod_quotes").fetchall()
    concept_counts: Counter = Counter()
    hero_counts: Counter = Counter()
    for r in concept_rows:
        for c in _json.loads(r["concepts_json"] or "[]"):
            concept_counts[c] += 1
        for h in _json.loads(r["heroes_json"] or "[]"):
            hero_counts[h] += 1

    if concept_counts:
        console.print("\n[bold]Top concepts across the library:[/]")
        for concept, count in concept_counts.most_common(10):
            console.print(f"  [magenta]@{concept}[/] {count} mention(s)")
    if hero_counts:
        console.print("\n[bold]Most-discussed heroes:[/]")
        for hero, count in hero_counts.most_common(10):
            console.print(f"  [cyan]#{hero}[/] {count} mention(s)")


def run_inspect_vod(review_id_prefix: str) -> None:
    """Show every tagged quote from a single VOD by review_id (prefix match).
    Use this to audit what the keyword library caught and what it missed."""

    import datetime as dt
    import json as _json

    from memory import database

    conn = database.connect()
    review = conn.execute(
        "SELECT * FROM vod_reviews WHERE id LIKE ? LIMIT 1",
        (review_id_prefix + "%",),
    ).fetchone()
    if not review:
        console.print(f"[red]No VOD found matching ID prefix '{review_id_prefix}'.[/]")
        console.print("Run [cyan]python main.py --list-vods[/] to see what is ingested.")
        return

    quotes = conn.execute(
        "SELECT * FROM vod_quotes WHERE review_id = ? ORDER BY start_seconds",
        (review["id"],),
    ).fetchall()
    correlations = conn.execute(
        "SELECT event_type, COUNT(*) c FROM vod_correlations WHERE review_id = ? GROUP BY event_type",
        (review["id"],),
    ).fetchall()

    ingested = dt.datetime.fromtimestamp(review["ingested_at"]).strftime("%Y-%m-%d %H:%M")
    console.print(f"\n[bold cyan]{review['title'] or '(untitled)'}[/]")
    console.print(f"  [dim]ID:[/] {review['id']}")
    console.print(f"  [dim]Source:[/] {review['source']}")
    console.print(f"  [dim]Duration:[/] {(review['duration_seconds'] or 0) / 60:.1f} min")
    console.print(f"  [dim]Ingested:[/] {ingested}")
    console.print(f"  [dim]Tagged quotes:[/] {len(quotes)}")
    if correlations:
        rollup = ", ".join(f"{r['event_type']}:{r['c']}" for r in correlations)
        console.print(f"  [dim]Correlations:[/] {rollup}")
    console.print()

    if not quotes:
        console.print("[yellow]No tagged quotes. Either the VOD has no coaching speech, "
                      "or the keyword vocabulary did not catch what was said.[/]")
        return

    for q in quotes:
        mm, ss = divmod(int(q["start_seconds"]), 60)
        heroes = _json.loads(q["heroes_json"] or "[]")
        abilities = _json.loads(q["abilities_json"] or "[]")
        concepts = _json.loads(q["concepts_json"] or "[]")
        tag_bits = (
            [f"[cyan]#{h}[/]" for h in heroes]
            + [f"[yellow]*{a}[/]" for a in abilities]
            + [f"[magenta]@{c}[/]" for c in concepts]
        )
        console.print(f"[dim]{mm:>3}:{ss:02d}[/] {q['text']}")
        if tag_bits:
            console.print("       " + " ".join(tag_bits))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="snap")
    parser.add_argument("--live", action="store_true",
                        help="Live screen capture. Windows auto-stops on OW2 unfocus. macOS runs until Ctrl+C.")
    parser.add_argument("--replay", type=Path, help="Replay a session directory of PNG frames")
    parser.add_argument("--video", type=Path, help="Process a saved video as if it were live gameplay")
    parser.add_argument("--vod", type=str,
                        help="Ingest a VOD review. Accepts a local file path OR a YouTube URL "
                             "(auto-downloads via yt-dlp).")
    parser.add_argument("--vod-title", type=str, help="Friendly title for the VOD review (for reports)")
    parser.add_argument("--list-vods", action="store_true",
                        help="List every ingested VOD with quote counts and concept distribution")
    parser.add_argument("--inspect-vod", type=str, metavar="REVIEW_ID",
                        help="Show every tagged quote from a specific VOD (use ID prefix from --list-vods)")
    parser.add_argument("--demo", action="store_true", help="Run a canned synthetic session")
    parser.add_argument("--hero", type=str, help="Pre-set initial hero (skip the prompt)")
    parser.add_argument("--duration", type=int, help="Auto-stop --live after N seconds")
    parser.add_argument("--no-menubar", action="store_true", help="Disable the macOS menu bar status icon")
    parser.add_argument("--no-overlay", action="store_true", help="Disable the floating overlay window")
    parser.add_argument("--debug", action="store_true", help="Verbose logging")
    args = parser.parse_args(argv)

    config.configure_logging(debug=args.debug)

    if args.demo:
        run_demo()
        return 0
    if args.list_vods:
        run_list_vods()
        return 0
    if args.inspect_vod:
        run_inspect_vod(args.inspect_vod)
        return 0
    if args.replay:
        run_replay(args.replay, initial_hero=args.hero)
        return 0
    if args.video:
        run_video(args.video, initial_hero=args.hero)
        return 0
    if args.vod:
        run_vod(args.vod, title=args.vod_title)
        return 0
    if args.live:
        run_live(
            duration_seconds=args.duration,
            initial_hero=args.hero,
            menubar=not args.no_menubar,
            overlay=not args.no_overlay,
        )
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
