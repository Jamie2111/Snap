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
    """Three synthetic matches across different maps and enemies. Exercises
    the multi-match pipeline end-to-end without needing real OW2 footage."""

    from extractor.game_state import GameState
    from extractor.match_context import MatchContext
    from extractor.match_tracker import Match
    from extractor.events import EventDetector, SessionEvents
    from feedback.engine import generate_for_matches
    from memory import database, player_profile
    from ui.report import render, write_markdown

    console.print("[bold cyan]Snap[/]: running demo session (3 matches)")

    def _build_match(idx: int, *, map_name: str, hero: str, enemies: list[str],
                     comp: str, result: str, with_ult_death: bool = False,
                     aim_on_target: int = 0, aim_total: int = 0) -> Match:
        det = EventDetector()
        ts = 0.0
        states: list[GameState] = []
        for _ in range(30):
            states.append(GameState(timestamp=ts, health_pct=1.0, ult_pct=0.5, cooldowns={a: "ready" for a in config.ABILITY_SLOTS}))
            ts += 1
        if with_ult_death:
            for _ in range(6):
                states.append(GameState(timestamp=ts, health_pct=0.6, ult_pct=1.0, fight_intensity=0.25, cooldowns={a: "ready" for a in config.ABILITY_SLOTS}))
                ts += 1
            states.append(GameState(timestamp=ts, health_pct=0.0, ult_pct=1.0, in_death_screen=True, cooldowns={a: "ready" for a in config.ABILITY_SLOTS}))
            ts += 5
        else:
            for _ in range(15):
                states.append(GameState(timestamp=ts, health_pct=0.8, ult_pct=0.4, fight_intensity=0.10, cooldowns={a: "ready" for a in config.ABILITY_SLOTS}))
                ts += 1
        for s in states:
            det.ingest(s)
        events = det.finalize()
        events.stats.aim_frames_with_enemy = aim_total
        events.stats.aim_frames_on_target = aim_on_target
        events.stats.aim_avg_miss_px = 67.0 if aim_total else 0.0
        events.stats.ability_glow_counts = {"dragonblade": 4} if with_ult_death else {}
        match = Match(
            match_index=idx,
            started_at=0.0,
            ended_at=ts,
            map_name=map_name,
            result=result,
            events=events,
            match_context=MatchContext(
                your_hero=hero,
                allies=["ana", "lucio", "reinhardt", "zarya"],
                enemies=enemies,
                your_comp=comp,
                enemy_comp="brawl",
            ),
        )
        return match

    matches = [
        _build_match(
            1, map_name="Ilios", hero="tracer",
            enemies=["mercy", "kiriko", "reinhardt", "zarya", "brigitte"],
            comp="hybrid", result="loss", with_ult_death=True,
            aim_on_target=58, aim_total=240,
        ),
        _build_match(
            2, map_name="King's Row", hero="tracer",
            enemies=["mercy", "ana", "reinhardt", "zarya", "soldier76"],
            comp="hybrid", result="win",
            aim_on_target=92, aim_total=210,
        ),
        _build_match(
            3, map_name="Numbani", hero="ana",
            enemies=["winston", "kiriko", "tracer", "reaper", "lucio"],
            comp="brawl", result="loss", with_ult_death=True,
            aim_on_target=33, aim_total=180,
        ),
    ]

    conn = database.connect()
    feedback = generate_for_matches(matches, db_conn=conn)
    session_id = uuid.uuid4().hex[:12]
    ctx = feedback.match_context
    player_profile.write_session(
        session_id=session_id,
        timestamp=time.time(),
        hero=ctx.your_hero if ctx else None,
        duration_minutes=sum(m.duration_seconds for m in matches) / 60.0,
        deaths=feedback.session_summary.deaths,
        ult_efficiency_score=feedback.session_summary.ult_efficiency_score,
        raw_event={"matches": len(matches)},
        feedback_given={"critical": [c.issue for c in feedback.critical]},
        allies=ctx.allies if ctx else [],
        enemies=ctx.enemies if ctx else [],
        your_comp=ctx.your_comp if ctx else None,
        enemy_comp=ctx.enemy_comp if ctx else None,
        conn=conn,
    )
    for m, mf in zip(matches, feedback.matches):
        player_profile.write_match(
            session_id=session_id,
            match_index=m.match_index,
            started_at=m.started_at,
            ended_at=m.ended_at,
            duration_seconds=m.duration_seconds,
            map_name=m.map_name,
            result=m.result,
            hero=m.match_context.your_hero,
            allies=list(m.match_context.allies),
            enemies=list(m.match_context.enemies),
            your_comp=m.match_context.your_comp,
            enemy_comp=m.match_context.enemy_comp,
            deaths=m.events.stats.deaths_total,
            ult_efficiency_score=mf.session_summary.ult_efficiency_score,
            aim_on_target_pct=(
                m.events.stats.aim_frames_on_target / m.events.stats.aim_frames_with_enemy
                if m.events.stats.aim_frames_with_enemy else 0.0
            ),
            raw_event={"events": m.events.stats.deaths_total},
            feedback_given={"critical": [c.issue for c in mf.critical]},
            conn=conn,
        )
    from extractor.match_tracker import aggregate_session_stats
    agg = aggregate_session_stats(matches)
    player_profile.write_mistakes_from_events(session_id, agg, conn=conn)
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
    runs match-boundary detectors and per-match event detection, runs the
    vision pipeline for aim + ability outcomes, generates per-match + session
    feedback, renders the report."""

    from collections import Counter

    from extractor.aim import AimTracker
    from extractor.game_state import extract_state
    from extractor.match_tracker import MatchTracker
    from extractor.vision import VisionPipeline
    from feedback.engine import generate_for_matches
    from memory import database, player_profile
    from ui.report import render, write_markdown

    console.print(f"[bold cyan]Snap[/]: {source_label}")

    tracker = MatchTracker(initial_hero=initial_hero)
    vision = VisionPipeline()
    aim = AimTracker()
    ability_glow_counts: Counter = Counter()
    screen_flash_count = 0
    health_history: list[float] = []
    frames_processed = 0
    for cf in frame_source:
        try:
            tracker.ingest_frame(cf.frame, cf.timestamp)
        except Exception:
            log.exception("match-tracker frame ingest failed")
        try:
            state = extract_state(cf.frame, cf.timestamp, health_history)
        except Exception:
            log.exception("extract_state failed on frame %d", frames_processed)
            continue
        health_history.append(state.health_pct)
        tracker.ingest_state(state)
        try:
            tracker.observe_frame_for_hero(cf.frame)
        except Exception:
            log.exception("hero-observation pass failed on frame %d", frames_processed)
        try:
            bundle = vision.process(cf.frame)
            aim.ingest(bundle)
            for d in bundle.ability_glows:
                ability_glow_counts[d.kind.split(":", 1)[-1]] += 1
            if bundle.screen_flash is not None:
                screen_flash_count += 1
        except Exception:
            log.exception("vision pass failed on frame %d", frames_processed)
        frames_processed += 1

    matches = tracker.finalize()
    aim_m = aim.snapshot()
    if matches:
        last = matches[-1]
        last.events.stats.aim_frames_with_enemy = aim_m.frames_with_enemy_in_sight
        last.events.stats.aim_frames_on_target = aim_m.frames_on_target
        last.events.stats.aim_avg_miss_px = round(aim_m.avg_miss_distance, 1)
        last.events.stats.aim_near_misses = aim_m.near_misses
        last.events.stats.ability_glow_counts = dict(ability_glow_counts)
        last.events.stats.screen_flash_count = screen_flash_count

    conn = database.connect()
    feedback = generate_for_matches(matches, db_conn=conn)
    session_id = uuid.uuid4().hex[:12]
    player_profile.write_session(
        session_id=session_id,
        timestamp=time.time(),
        hero=feedback.match_context.your_hero if feedback.match_context else None,
        duration_minutes=sum(m.duration_seconds for m in matches) / 60.0,
        deaths=feedback.session_summary.deaths,
        ult_efficiency_score=feedback.session_summary.ult_efficiency_score,
        raw_event={"frames": frames_processed, "matches": len(matches)},
        feedback_given={"critical": [c.issue for c in feedback.critical]},
        allies=feedback.match_context.allies if feedback.match_context else [],
        enemies=feedback.match_context.enemies if feedback.match_context else [],
        your_comp=feedback.match_context.your_comp if feedback.match_context else None,
        enemy_comp=feedback.match_context.enemy_comp if feedback.match_context else None,
        conn=conn,
    )
    for m, mf in zip(matches, feedback.matches):
        player_profile.write_match(
            session_id=session_id,
            match_index=m.match_index,
            started_at=m.started_at,
            ended_at=m.ended_at,
            duration_seconds=m.duration_seconds,
            map_name=m.map_name,
            result=m.result,
            hero=m.match_context.your_hero,
            allies=list(m.match_context.allies),
            enemies=list(m.match_context.enemies),
            your_comp=m.match_context.your_comp,
            enemy_comp=m.match_context.enemy_comp,
            deaths=m.events.stats.deaths_total,
            ult_efficiency_score=mf.session_summary.ult_efficiency_score,
            aim_on_target_pct=(
                m.events.stats.aim_frames_on_target / m.events.stats.aim_frames_with_enemy
                if m.events.stats.aim_frames_with_enemy else 0.0
            ),
            raw_event={"events": m.events.stats.deaths_total},
            feedback_given={"critical": [c.issue for c in mf.critical]},
            conn=conn,
        )
    from extractor.match_tracker import aggregate_session_stats
    agg = aggregate_session_stats(matches)
    player_profile.write_mistakes_from_events(session_id, agg, conn=conn)
    player_profile.update_player_model(session_id, conn=conn)

    render(feedback, console=console)
    md_path = write_markdown(feedback, session_id)
    console.print(
        f"\n[dim]Processed {frames_processed} frames across {len(matches)} match(es). "
        f"Markdown report: {md_path}[/]"
    )
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


def _kill_stale_overlay_procs() -> None:
    """Kill any zombie overlay processes from previous crashes. macOS leaves
    them around when Python crashes uncleanly and they hold stdin handles
    that confuse new launches."""
    import subprocess as _sp
    try:
        _sp.run(["pkill", "-f", "python -m ui.overlay"], stderr=_sp.DEVNULL, stdout=_sp.DEVNULL)
    except Exception:
        pass


def _start_overlay_subprocess() -> Optional["subprocess.Popen"]:
    """Spawn the pywebview overlay as a child process. stdin receives JSON
    snapshots; stdout emits SNAP_CONTROL:* lines we forward to the worker.

    stderr is written to data/sessions/.overlay.log so silent failures are
    debuggable. We also log immediately if Popen fails. Stale overlays from
    earlier crashes are killed first."""
    import os as _os
    import subprocess
    import sys as _sys
    _kill_stale_overlay_procs()
    log_path = config.SESSIONS_DIR / ".overlay.log"
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        # Append a session-start marker so we can correlate logs to runs.
        with log_path.open("ab") as f:
            f.write(b"\n--- overlay spawn ---\n")
        stderr_f = log_path.open("ab")
        env = _os.environ.copy()
        # Force unbuffered stdout on the child. Without this, SNAP_CONTROL
        # lines sit in Python's block buffer when stdout is a pipe and the
        # parent's readline() blocks forever - which is exactly the "Stop
        # button doesn't work until Pause is pressed" bug.
        env["PYTHONUNBUFFERED"] = "1"
        # Pass the control-file path to the overlay so it can fall back to a
        # filesystem signal when stdout is still buffered for any reason.
        env["SNAP_OVERLAY_CONTROL_FILE"] = str(config.SESSIONS_DIR / ".overlay-control")
        proc = subprocess.Popen(
            [_sys.executable, "-u", "-m", "ui.overlay"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=stderr_f,
            cwd=str(config.BASE_DIR),
            bufsize=0,
            env=env,
        )
        log.info("Overlay subprocess spawned (pid=%s, log=%s)", proc.pid, log_path)
        return proc
    except Exception:
        log.exception("Failed to launch overlay subprocess")
        return None


def _start_overlay_control_reader(proc, stop_event, pause_flag, live_state=None) -> "threading.Thread":
    """Read SNAP_CONTROL lines from the overlay subprocess and translate to
    flag updates on the capture worker. Also polls a filesystem signal file
    (data/sessions/.overlay-control) every 200ms as a redundant channel that
    survives stdout buffering glitches on macOS subprocess pipes.

    Passing the LiveState in lets us freeze its elapsed clock on PAUSE and
    resume it on RESUME, instead of relying on the worker to do the time math."""
    import threading
    import time as _time

    signal_path = config.SESSIONS_DIR / ".overlay-control"
    try:
        signal_path.unlink()
    except FileNotFoundError:
        pass
    except Exception:
        pass

    def _apply(cmd: str) -> bool:
        """Apply a SNAP_CONTROL command. Returns True if the reader should exit
        (STOP) and False otherwise."""
        cmd = cmd.strip().upper()
        if cmd == "STOP":
            log.info("Overlay requested STOP")
            stop_event.set()
            return True
        if cmd == "PAUSE":
            log.info("Overlay requested PAUSE")
            pause_flag["paused"] = True
            if live_state is not None:
                try:
                    live_state.pause()
                except Exception:
                    pass
        if cmd == "RESUME":
            log.info("Overlay requested RESUME")
            pause_flag["paused"] = False
            if live_state is not None:
                try:
                    live_state.resume()
                except Exception:
                    pass
        return False

    def stdout_reader():
        try:
            for raw in iter(proc.stdout.readline, b""):
                if not raw:
                    break
                line = raw.decode(errors="ignore").strip()
                if not line.startswith("SNAP_CONTROL:"):
                    continue
                if _apply(line.split(":", 1)[1]):
                    return
        except Exception:
            log.exception("Overlay control reader (stdout) crashed")

    def signal_reader():
        """Poll for the .overlay-control file. The overlay writes the command
        to this file as a fallback if stdout is buffered. Each command is read
        once and then the file is truncated."""
        try:
            while not stop_event.is_set():
                try:
                    if signal_path.exists():
                        cmd = signal_path.read_text(errors="ignore").strip()
                        try:
                            signal_path.unlink()
                        except FileNotFoundError:
                            pass
                        for piece in cmd.splitlines():
                            piece = piece.strip()
                            if not piece:
                                continue
                            if _apply(piece):
                                return
                except Exception:
                    pass
                _time.sleep(0.2)
        except Exception:
            log.exception("Overlay control reader (signal file) crashed")

    threading.Thread(target=stdout_reader, daemon=True).start()
    threading.Thread(target=signal_reader, daemon=True).start()
    return None


def _capture_worker(
    state,  # LiveState
    duration_seconds: Optional[int],
    stop_event,  # threading.Event
    result: dict,
    overlay_proc=None,
    pause_flag: Optional[dict] = None,  # {"paused": bool} shared with overlay reader
) -> None:
    """Background thread: runs the capture loop, publishes to LiveState, and
    stores final events / context in `result` for the main thread to consume
    after the worker finishes."""

    import json as _json
    from collections import Counter
    from capture.screen import live_capture, write_session_manifest
    from extractor.aim import AimTracker
    from extractor.game_state import extract_state
    from extractor.hud_confidence import HUDConfidenceTracker
    from extractor.match_tracker import MatchTracker
    from extractor.player_state import PlayerStateClassifier
    from extractor.vision import VisionPipeline
    from feedback import realtime as realtime_tips

    tracker = MatchTracker(initial_hero=result.get("initial_hero"))
    player_state_clf = PlayerStateClassifier()
    hud_tracker = HUDConfidenceTracker()
    if result.get("initial_hero"):
        state.set_hero(result["initial_hero"])
    vision = VisionPipeline()
    aim = AimTracker()
    ability_glow_counts: Counter = Counter()
    screen_flash_count = 0
    health_history: list[float] = []
    session_dir: Optional[Path] = None
    record = None
    start_time = time.monotonic()
    stopped_reason = "completed"
    prev_death_count = 0
    prev_ults_used = 0
    prev_ults_wasted = 0
    frames_with_hud = 0
    frames_total = 0
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
                "enemies": list(snap.enemies),
                "last_event": snap.last_event,
                "player_state": snap.player_state,
                "tip_text": snap.tip_text,
                "tip_detail": snap.tip_detail,
                "tip_urgency": snap.tip_urgency,
                "match_index": snap.match_index,
                "deaths": snap.deaths,
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
            # Honor pause command from overlay: keep the capture loop alive
            # (so the elapsed clock still advances) but skip extraction work.
            if pause_flag and pause_flag.get("paused"):
                state.tick_frame()
                push_overlay()
                continue
            state.tick_frame()
            frames_total += 1
            # HUD presence gate. Same logic as the launcher's in-process
            # runner: skip extraction on non-OW2 frames so we never produce
            # fabricated events from random pixels.
            try:
                hud_tracker.ingest(cf.frame)
            except Exception:
                log.exception("HUD confidence measurement failed")
            if not hud_tracker.is_capturing_ow2():
                try:
                    state.set_player_state("playing")
                    state.set_tip(
                        "Waiting for Overwatch 2",
                        "Snap can't see the HUD. Make sure OW2 is in Borderless Windowed at 1920x1080.",
                        "info",
                    )
                except Exception:
                    pass
                push_overlay()
                continue
            frames_with_hud += 1
            try:
                tracker.ingest_frame(cf.frame, cf.timestamp)
            except Exception:
                log.exception("match-tracker frame ingest failed")
            try:
                gs = extract_state(cf.frame, cf.timestamp, health_history)
            except Exception:
                log.exception("extract_state failed")
                continue
            health_history.append(gs.health_pct)
            tracker.ingest_state(gs)
            try:
                observed = tracker.observe_frame_for_hero(cf.frame)
                if observed:
                    state.record_event(f"hero confirmed: {observed}")
            except Exception:
                log.exception("hero-observation pass failed")
            try:
                bundle = vision.process(cf.frame)
                aim.ingest(bundle)
                for d in bundle.ability_glows:
                    ability_glow_counts[d.kind.split(":", 1)[-1]] += 1
                if bundle.screen_flash is not None:
                    screen_flash_count += 1
            except Exception:
                log.exception("vision pass failed")
            cur_match = tracker._current_match
            if cur_match is not None and cur_match.match_context.your_hero:
                state.set_hero(cur_match.match_context.your_hero)
            if cur_match is not None and cur_match.match_context.allies:
                state.set_allies(list(cur_match.match_context.allies))
            if cur_match is not None and cur_match.match_context.enemies:
                state.set_enemies(list(cur_match.match_context.enemies))
            if tracker._current_detector is not None:
                stats = tracker._current_detector.events.stats
                if stats.deaths_total > prev_death_count:
                    state.record_event("Death", death=True)
                    prev_death_count = stats.deaths_total
                if stats.ults_used > prev_ults_used:
                    state.record_event("Ult used", ult_used=True)
                    prev_ults_used = stats.ults_used
                if stats.ults_wasted > prev_ults_wasted:
                    state.record_event("Ult wasted", ult_wasted=True)
                    prev_ults_wasted = stats.ults_wasted

            # Player state + real-time tip
            try:
                cls = player_state_clf.classify(cf.frame, gs, cf.timestamp)
                state.set_player_state(cls.state.value)
                if cur_match is not None:
                    last_death_obj = cur_match.events.deaths[-1] if cur_match.events.deaths else None
                else:
                    last_death_obj = None
                last_match_focus = ""
                if tracker.matches:
                    closed = [m for m in tracker.matches if m.ended_at is not None]
                    if closed:
                        last_match_focus = (
                            "Use ult earlier" if any(d.ult_pct_at_death >= 0.80 for d in closed[-1].events.deaths)
                            else ""
                        )
                tip = realtime_tips.generate(
                    state=cls.state,
                    hero=state.snapshot().hero,
                    enemies=list(state.snapshot().enemies),
                    last_death=last_death_obj,
                    last_match_focus=last_match_focus or None,
                )
                if tip is not None:
                    state.set_tip(tip.text, tip.detail, tip.urgency)
                else:
                    state.set_tip("", "", "info")
                state.set_match_progress(len(tracker.matches))
            except Exception:
                log.exception("player-state / tip generation failed")
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
        matches_final = tracker.finalize()
        aim_m = aim.snapshot()
        if matches_final:
            last = matches_final[-1]
            last.events.stats.aim_frames_with_enemy = aim_m.frames_with_enemy_in_sight
            last.events.stats.aim_frames_on_target = aim_m.frames_on_target
            last.events.stats.aim_avg_miss_px = round(aim_m.avg_miss_distance, 1)
            last.events.stats.aim_near_misses = aim_m.near_misses
            last.events.stats.ability_glow_counts = dict(ability_glow_counts)
            last.events.stats.screen_flash_count = screen_flash_count
        result["matches"] = matches_final
        result["session_dir"] = session_dir
        result["record"] = record
        result["stopped_reason"] = stopped_reason
        result["frames_with_hud"] = frames_with_hud
        result["frames_total"] = frames_total


def run_live(
    duration_seconds: Optional[int] = None,
    initial_hero: Optional[str] = None,
    menubar: bool = False,
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
    # Visible warning if OCR is disabled so the user understands what's missing.
    from extractor.ocr import TESSERACT_AVAILABLE
    if not TESSERACT_AVAILABLE:
        console.print(
            "[bold yellow]Tesseract is not installed.[/] Hero / scoreboard / killfeed OCR is "
            "disabled. Run [cyan]brew install tesseract[/] (macOS) for full functionality. "
            "Vision and HUD extraction still work."
        )

    initial = initial_hero or _prompt_initial_hero()

    overlay_proc = _start_overlay_subprocess() if overlay else None

    stop_event = threading.Event()
    pause_flag = {"paused": False}
    if overlay_proc is not None:
        _start_overlay_control_reader(overlay_proc, stop_event, pause_flag, live_state=state)
    result: dict = {"initial_hero": initial}

    worker = threading.Thread(
        target=_capture_worker,
        args=(state, duration_seconds, stop_event, result, overlay_proc, pause_flag),
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

    matches = result.get("matches") or []
    frames_seen = state.snapshot().frames_seen
    # HUD-detection gate. If the OW2 HUD was never confidently seen, don't
    # render a report - it would be fabricated from non-OW2 content.
    fwh = result.get("frames_with_hud", 0)
    ft = result.get("frames_total", 0)
    if ft >= 6 and fwh / max(1, ft) < 0.15:
        console.print(
            "[bold yellow]No Overwatch 2 HUD detected.[/] "
            f"({fwh}/{ft} frames had a visible HUD). "
            "Snap captured the screen but couldn't see OW2. "
            "Make sure OW2 is in Borderless Windowed at 1920x1080 with default UI scale."
        )
        return
    if frames_seen == 0:
        # Still write a JSON sidecar so the launcher can show a useful error
        # instead of timing out on its watcher.
        import json as _json
        import time as _time
        err_payload = {
            "session_id": "no_frames",
            "completed_at": _time.time(),
            "matches_count": 0,
            "frames": 0,
            "stopped_reason": "no_frames",
            "error": "Zero frames captured. On macOS, grant Screen Recording permission "
                     "to your Python executable in System Settings > Privacy & Security "
                     "> Screen Recording, then restart the app.",
            "feedback": None,
        }
        try:
            (config.REPORTS_DIR / f"{int(_time.time())}-no_frames.json").write_text(_json.dumps(err_payload))
        except Exception:
            log.exception("Failed to write no-frames JSON sidecar")
        console.print(
            "[bold red]No frames captured.[/] "
            "If you're on macOS, grant Screen Recording permission in "
            "System Settings > Privacy & Security > Screen Recording, then restart your terminal."
        )
        return

    from feedback.engine import generate_for_matches
    from extractor.match_tracker import aggregate_session_stats

    conn = database.connect()
    feedback = generate_for_matches(matches, db_conn=conn)
    record = result.get("record")
    session_id = record.session_id if record else uuid.uuid4().hex[:12]
    ctx = feedback.match_context
    player_profile.write_session(
        session_id=session_id,
        timestamp=time.time(),
        hero=ctx.your_hero if ctx else None,
        duration_minutes=(record.end_time - record.start_time) / 60.0 if record and record.end_time else 0.0,
        deaths=feedback.session_summary.deaths,
        ult_efficiency_score=feedback.session_summary.ult_efficiency_score,
        raw_event={
            "frames": state.snapshot().frames_seen,
            "matches": len(matches),
            "stopped_reason": result.get("stopped_reason"),
        },
        feedback_given={"critical": [c.issue for c in feedback.critical]},
        allies=ctx.allies if ctx else [],
        enemies=ctx.enemies if ctx else [],
        your_comp=ctx.your_comp if ctx else None,
        enemy_comp=ctx.enemy_comp if ctx else None,
        conn=conn,
    )
    for m, mf in zip(matches, feedback.matches):
        player_profile.write_match(
            session_id=session_id,
            match_index=m.match_index,
            started_at=m.started_at,
            ended_at=m.ended_at,
            duration_seconds=m.duration_seconds,
            map_name=m.map_name,
            result=m.result,
            hero=m.match_context.your_hero,
            allies=list(m.match_context.allies),
            enemies=list(m.match_context.enemies),
            your_comp=m.match_context.your_comp,
            enemy_comp=m.match_context.enemy_comp,
            deaths=m.events.stats.deaths_total,
            ult_efficiency_score=mf.session_summary.ult_efficiency_score,
            aim_on_target_pct=(
                m.events.stats.aim_frames_on_target / m.events.stats.aim_frames_with_enemy
                if m.events.stats.aim_frames_with_enemy else 0.0
            ),
            raw_event={"events": m.events.stats.deaths_total},
            feedback_given={"critical": [c.issue for c in mf.critical]},
            conn=conn,
        )
    agg = aggregate_session_stats(matches)
    player_profile.write_mistakes_from_events(session_id, agg, conn=conn)
    player_profile.update_player_model(session_id, conn=conn)
    render(feedback, console=console)
    md_path = write_markdown(feedback, session_id)
    # Sidecar JSON so the launcher can pick up the structured feedback after
    # the subprocess exits and auto-navigate to the report view.
    import json as _json
    from dataclasses import asdict as _asdict, is_dataclass as _is_dc

    def _safe(o):
        if _is_dc(o): return {k: _safe(v) for k, v in _asdict(o).items()}
        if isinstance(o, dict): return {k: _safe(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)): return [_safe(x) for x in o]
        if isinstance(o, (str, int, float, bool)) or o is None: return o
        return str(o)

    json_path = md_path.with_suffix(".json")
    json_path.write_text(_json.dumps({
        "session_id": session_id,
        "completed_at": time.time(),
        "matches_count": len(matches),
        "frames": state.snapshot().frames_seen,
        "stopped_reason": result.get("stopped_reason"),
        "feedback": _safe(feedback),
    }, indent=2))
    console.print(
        f"\n[dim]Processed {state.snapshot().frames_seen} frames across {len(matches)} match(es) "
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
    parser.add_argument("--app", action="store_true", help="Launch the Snap desktop GUI (default when run with no args)")
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
    if args.app or len(sys.argv) == 1:
        from ui.app import run_app
        run_app()
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
