"""Snap desktop launcher: pywebview WebKit window with HTML/CSS UI.

Single-page app: every Snap feature is available inside the window. Long
operations run in background threads and stream progress back into JS via
window.evaluate_js. No terminal interaction required.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import shutil
import subprocess
import sys
import threading
import uuid
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Optional

import config

log = logging.getLogger(__name__)


def _python_exec() -> str:
    return sys.executable


class _NoFramesError(Exception):
    """Raised by _run_live_inproc when zero frames were captured."""
    pass


class _NoHUDError(Exception):
    """Raised when frames were captured but the OW2 HUD was never confidently
    detected. The session was likely random non-OW2 content (Netflix, a
    different game, the desktop) and we refuse to fabricate a report."""
    pass


def _to_jsonable(obj: Any) -> Any:
    """Convert dataclasses / dicts / lists recursively to JSON-safe values."""
    if is_dataclass(obj):
        return _to_jsonable(asdict(obj))
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(x) for x in obj]
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    return str(obj)


class Api:
    """JS-callable bridge. Exposed as window.pywebview.api in the launcher HTML."""

    def __init__(self) -> None:
        self._window = None
        self._active_subprocs: list[subprocess.Popen] = []

    def set_window(self, window) -> None:
        self._window = window

    # ============ Status ============

    def get_status(self) -> dict:
        whisper_cache = Path.home() / ".cache" / "huggingface" / "hub"
        whisper_installed = (
            whisper_cache.exists()
            and any(whisper_cache.glob("**/Systran--faster-whisper-base*"))
        )
        return {
            "tesseract": shutil.which(config.TESSERACT_CMD) is not None,
            "ffmpeg": shutil.which("ffmpeg") is not None,
            "ytdlp": shutil.which("yt-dlp") is not None,
            "whisper": whisper_installed,
            "reports_path": str(config.REPORTS_DIR),
            "db_path": str(config.DB_PATH),
        }

    # ============ File pickers ============

    def pick_video(self) -> Optional[str]:
        if not self._window:
            return None
        try:
            import webview
            result = self._window.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                directory=str(config.SESSIONS_DIR),
                file_types=("Video files (*.mp4;*.mov;*.mkv;*.webm)", "All files (*.*)"),
            )
        except Exception:
            return None
        return (result[0] if isinstance(result, (list, tuple)) else result) if result else None

    def pick_replay_dir(self) -> Optional[str]:
        if not self._window:
            return None
        try:
            import webview
            result = self._window.create_file_dialog(
                webview.FOLDER_DIALOG,
                directory=str(config.SESSIONS_DIR),
            )
        except Exception:
            return None
        return (result[0] if isinstance(result, (list, tuple)) else result) if result else None

    # ============ Background ops ============

    def run_live(self, hero: str = "") -> dict:
        """Live capture runs IN this launcher process (in a background thread),
        not a subprocess. Reason: macOS Screen Recording permission is per
        process and doesn't inherit through Popen. The launcher was started
        from Terminal so it has the grant; a subprocess wouldn't.

        The overlay is still a subprocess (needs its own NSWindow across
        Spaces) but it doesn't capture the screen, so no permission issue."""

        job_id = uuid.uuid4().hex[:12]
        Api._jobs[job_id] = {"status": "running", "result": None, "error": None, "mode": "live"}
        h = (hero or "").strip().lower().replace(" ", "")

        def runner():
            try:
                Api._jobs[job_id]["result"] = self._run_live_inproc(h)
                Api._jobs[job_id]["status"] = "done"
            except _NoFramesError:
                Api._jobs[job_id]["status"] = "error"
                Api._jobs[job_id]["error"] = "no_frames"
            except _NoHUDError as e:
                Api._jobs[job_id]["status"] = "error"
                Api._jobs[job_id]["error"] = f"no_hud: {e}"
            except Exception as e:
                log.exception("Live capture job failed")
                Api._jobs[job_id]["status"] = "error"
                Api._jobs[job_id]["error"] = str(e)

        threading.Thread(target=runner, daemon=True).start()
        return {"job_id": job_id}

    def _run_live_inproc(self, hero: str) -> dict:
        """Run the live capture pipeline in this thread. Spawns the overlay
        subprocess for the UI, but does screen capture + extraction here so
        Screen Recording permission inherits correctly from the parent process."""

        import json as _json
        import time as _time
        from collections import Counter

        # Reuse helpers from main.py
        from main import _start_overlay_subprocess, _start_overlay_control_reader
        from capture.screen import live_capture, write_session_manifest
        from extractor.aim import AimTracker
        from extractor.game_state import extract_state
        from extractor.hud_confidence import HUDConfidenceTracker
        from extractor.match_tracker import MatchTracker, aggregate_session_stats
        from extractor.player_state import PlayerStateClassifier
        from extractor.vision import VisionPipeline
        from feedback import realtime as realtime_tips
        from feedback.engine import generate_for_matches
        from memory import database, player_profile
        from ui import live_state

        state = live_state.get()
        if hero:
            state.set_hero(hero)
        state.start()

        overlay_proc = _start_overlay_subprocess()
        stop_event = threading.Event()
        pause_flag = {"paused": False}
        if overlay_proc is not None:
            _start_overlay_control_reader(overlay_proc, stop_event, pause_flag, live_state=state)

        tracker = MatchTracker(initial_hero=hero or None)
        player_state_clf = PlayerStateClassifier()
        hud_tracker = HUDConfidenceTracker()
        vision = VisionPipeline()
        aim = AimTracker()
        ability_glow_counts: Counter = Counter()
        screen_flash_count = 0
        health_history: list[float] = []
        session_dir = None
        record = None
        stopped_reason = "completed"
        prev_d, prev_uu, prev_uw = 0, 0, 0
        frames_with_hud = 0
        frames_total = 0

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
                if pause_flag.get("paused"):
                    state.tick_frame()
                    push_overlay()
                    continue
                state.tick_frame()
                frames_total += 1

                # HUD presence gate. If the frame doesn't look like Overwatch
                # 2 (e.g. the user is watching something else, switched apps,
                # or there's a cinematic playing), do NOT feed it to the event
                # detectors. This is the single most important defense against
                # fabricated deaths / ults / cooldowns from random pixel noise.
                try:
                    hud_conf = hud_tracker.ingest(cf.frame)
                except Exception:
                    log.exception("HUD confidence measurement failed")
                    hud_conf = None
                hud_present = hud_tracker.is_capturing_ow2()
                if hud_present:
                    frames_with_hud += 1
                else:
                    # Frame is not OW2 gameplay. Update the overlay state so
                    # the player sees "WAITING FOR OW2" instead of confident
                    # nonsense, but don't ingest into trackers.
                    try:
                        state.set_player_state("playing")
                        state.set_tip(
                            "Waiting for Overwatch 2",
                            (
                                "Snap can't see the HUD. Make sure OW2 is in "
                                "Borderless Windowed at 1920x1080 with default UI scale."
                            ),
                            "info",
                        )
                    except Exception:
                        pass
                    push_overlay()
                    continue

                try:
                    tracker.ingest_frame(cf.frame, cf.timestamp)
                except Exception:
                    log.exception("match-tracker ingest failed")
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
                    log.exception("hero-observation failed")
                try:
                    bundle = vision.process(cf.frame)
                    aim.ingest(bundle)
                    for d in bundle.ability_glows:
                        ability_glow_counts[d.kind.split(":", 1)[-1]] += 1
                    if bundle.screen_flash is not None:
                        screen_flash_count += 1
                except Exception:
                    log.exception("vision failed")
                cur_match = tracker._current_match
                if cur_match is not None:
                    if cur_match.match_context.your_hero:
                        state.set_hero(cur_match.match_context.your_hero)
                    if cur_match.match_context.allies:
                        state.set_allies(list(cur_match.match_context.allies))
                    if cur_match.match_context.enemies:
                        state.set_enemies(list(cur_match.match_context.enemies))
                if tracker._current_detector is not None:
                    s = tracker._current_detector.events.stats
                    if s.deaths_total > prev_d:
                        state.record_event("Death", death=True); prev_d = s.deaths_total
                    if s.ults_used > prev_uu:
                        state.record_event("Ult used", ult_used=True); prev_uu = s.ults_used
                    if s.ults_wasted > prev_uw:
                        state.record_event("Ult wasted", ult_wasted=True); prev_uw = s.ults_wasted
                try:
                    cls = player_state_clf.classify(cf.frame, gs, cf.timestamp)
                    state.set_player_state(cls.state.value)
                    last_death = (cur_match.events.deaths[-1] if cur_match and cur_match.events.deaths else None)
                    tip = realtime_tips.generate(
                        state=cls.state,
                        hero=state.snapshot().hero,
                        enemies=list(state.snapshot().enemies),
                        last_death=last_death,
                        last_match_focus=None,
                    )
                    if tip:
                        state.set_tip(tip.text, tip.detail, tip.urgency)
                    else:
                        state.set_tip("", "", "info")
                    state.set_match_progress(len(tracker.matches))
                except Exception:
                    log.exception("tip generation failed")
                push_overlay()
        except Exception:
            log.exception("Capture loop crashed")
            stopped_reason = "error"
        finally:
            state.stop()
            push_overlay()
            if overlay_proc:
                try:
                    overlay_proc.terminate()
                except Exception:
                    pass

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

        frames_seen = state.snapshot().frames_seen
        if frames_seen == 0:
            raise _NoFramesError()

        # Data-integrity gate: if we never saw a confident OW2 HUD, the entire
        # capture was random content (YouTube non-OW2 video, screensaver, the
        # player's desktop). Refuse to produce a report rather than fabricating
        # one from noise.
        hud_ratio = (frames_with_hud / frames_total) if frames_total else 0.0
        if frames_total >= 6 and hud_ratio < 0.15:
            log.warning(
                "Aborting report: HUD detected in %d / %d frames (%.0f%%)",
                frames_with_hud, frames_total, hud_ratio * 100,
            )
            raise _NoHUDError(
                f"HUD detected in only {int(hud_ratio * 100)}% of frames. "
                f"Snap captured the screen but never saw Overwatch 2's HUD. "
                f"Make sure OW2 is running, in Borderless Windowed at 1920x1080, "
                f"and on the active desktop space."
            )

        conn = database.connect()
        fb = generate_for_matches(matches, db_conn=conn)
        ctx = fb.match_context
        session_id = uuid.uuid4().hex[:12]
        try:
            player_profile.write_session(
                session_id=session_id, timestamp=_time.time(),
                hero=ctx.your_hero if ctx else None,
                duration_minutes=sum(m.duration_seconds for m in matches) / 60.0 if matches else 0.0,
                deaths=fb.session_summary.deaths,
                ult_efficiency_score=fb.session_summary.ult_efficiency_score,
                raw_event={"frames": frames_seen, "stopped_reason": stopped_reason},
                feedback_given={"critical": [c.issue for c in fb.critical]},
                allies=ctx.allies if ctx else [], enemies=ctx.enemies if ctx else [],
                your_comp=ctx.your_comp if ctx else None,
                enemy_comp=ctx.enemy_comp if ctx else None,
                conn=conn,
            )
            for m, mfb in zip(matches, fb.matches):
                player_profile.write_match(
                    session_id=session_id, match_index=m.match_index,
                    started_at=m.started_at, ended_at=m.ended_at,
                    duration_seconds=m.duration_seconds, map_name=m.map_name,
                    result=m.result, hero=m.match_context.your_hero,
                    allies=list(m.match_context.allies), enemies=list(m.match_context.enemies),
                    your_comp=m.match_context.your_comp, enemy_comp=m.match_context.enemy_comp,
                    deaths=m.events.stats.deaths_total,
                    ult_efficiency_score=mfb.session_summary.ult_efficiency_score,
                    aim_on_target_pct=(
                        m.events.stats.aim_frames_on_target / m.events.stats.aim_frames_with_enemy
                        if m.events.stats.aim_frames_with_enemy else 0.0
                    ),
                    raw_event={"events": m.events.stats.deaths_total},
                    feedback_given={"critical": [c.issue for c in mfb.critical]},
                    conn=conn,
                )
            agg = aggregate_session_stats(matches)
            player_profile.write_mistakes_from_events(session_id, agg, conn=conn)
            player_profile.update_player_model(session_id, conn=conn)
        except Exception:
            log.exception("Saving session failed (non-fatal)")
        if session_dir is not None and record is not None:
            try:
                write_session_manifest(session_dir, record)
            except Exception:
                pass

        return _to_jsonable(fb)

    def run_video(self, path: str, hero: str = "") -> dict:
        """Run --video as a background thread inside the launcher process,
        capturing the resulting Feedback. Returns a job_id that JS polls."""
        return self._dispatch_analysis(path=path, hero=hero, mode="video")

    def run_replay(self, path: str) -> dict:
        return self._dispatch_analysis(path=path, hero="", mode="replay")

    def run_demo(self) -> dict:
        return self._dispatch_analysis(path="", hero="", mode="demo")

    def ingest_vod(self, src: str, title: str = "") -> dict:
        return self._dispatch_analysis(path=src, hero=title, mode="vod")

    _jobs: dict = {}

    def _dispatch_analysis(self, *, path: str, hero: str, mode: str) -> dict:
        job_id = uuid.uuid4().hex[:12]
        Api._jobs[job_id] = {"status": "running", "result": None, "error": None, "mode": mode}

        def worker():
            try:
                if mode == "demo":
                    Api._jobs[job_id]["result"] = self._run_demo_inproc()
                elif mode == "video":
                    Api._jobs[job_id]["result"] = self._run_video_inproc(path, hero)
                elif mode == "replay":
                    Api._jobs[job_id]["result"] = self._run_replay_inproc(path)
                elif mode == "vod":
                    Api._jobs[job_id]["result"] = self._run_vod_inproc(path, hero)
                Api._jobs[job_id]["status"] = "done"
            except Exception as e:
                log.exception("Job %s failed", job_id)
                Api._jobs[job_id]["status"] = "error"
                Api._jobs[job_id]["error"] = str(e)

        threading.Thread(target=worker, daemon=True).start()
        return {"job_id": job_id}

    def poll_job(self, job_id: str) -> dict:
        """JS polls this to check job status / fetch result."""
        return Api._jobs.get(job_id, {"status": "unknown"})

    # ---- In-process runners ----

    def _run_demo_inproc(self) -> dict:
        from extractor.events import EventDetector
        from extractor.game_state import GameState
        from extractor.match_context import MatchContext
        from extractor.match_tracker import Match
        from feedback.engine import generate_for_matches
        from memory import database, player_profile

        def build(idx, *, map_name, hero, enemies, comp, result, with_ult_death=False,
                  aim_on_target=0, aim_total=0):
            det = EventDetector()
            ts = 0.0
            states: list[GameState] = []
            for _ in range(30):
                states.append(GameState(timestamp=ts, health_pct=1.0, ult_pct=0.5,
                                        cooldowns={a: "ready" for a in config.ABILITY_SLOTS}))
                ts += 1
            if with_ult_death:
                for _ in range(6):
                    states.append(GameState(timestamp=ts, health_pct=0.6, ult_pct=1.0,
                                            fight_intensity=0.25,
                                            cooldowns={a: "ready" for a in config.ABILITY_SLOTS}))
                    ts += 1
                states.append(GameState(timestamp=ts, health_pct=0.0, ult_pct=1.0, in_death_screen=True,
                                        cooldowns={a: "ready" for a in config.ABILITY_SLOTS}))
                ts += 5
            else:
                for _ in range(15):
                    states.append(GameState(timestamp=ts, health_pct=0.8, ult_pct=0.4,
                                            fight_intensity=0.10,
                                            cooldowns={a: "ready" for a in config.ABILITY_SLOTS}))
                    ts += 1
            for s in states:
                det.ingest(s)
            events = det.finalize()
            events.stats.aim_frames_with_enemy = aim_total
            events.stats.aim_frames_on_target = aim_on_target
            events.stats.aim_avg_miss_px = 67.0 if aim_total else 0.0
            events.stats.ability_glow_counts = {"dragonblade": 4} if with_ult_death else {}
            return Match(
                match_index=idx, started_at=0.0, ended_at=ts,
                map_name=map_name, result=result, events=events,
                match_context=MatchContext(
                    your_hero=hero, allies=["ana", "lucio", "reinhardt", "zarya"],
                    enemies=enemies, your_comp=comp, enemy_comp="brawl",
                ),
            )

        matches = [
            build(1, map_name="Ilios", hero="tracer",
                  enemies=["mercy", "kiriko", "reinhardt", "zarya", "brigitte"],
                  comp="hybrid", result="loss", with_ult_death=True,
                  aim_on_target=58, aim_total=240),
            build(2, map_name="King's Row", hero="tracer",
                  enemies=["mercy", "ana", "reinhardt", "zarya", "soldier76"],
                  comp="hybrid", result="win",
                  aim_on_target=92, aim_total=210),
            build(3, map_name="Numbani", hero="ana",
                  enemies=["winston", "kiriko", "tracer", "reaper", "lucio"],
                  comp="brawl", result="loss", with_ult_death=True,
                  aim_on_target=33, aim_total=180),
        ]
        conn = database.connect()
        fb = generate_for_matches(matches, db_conn=conn)
        return _to_jsonable(fb)

    def _run_video_inproc(self, video_path: str, hero: str) -> dict:
        from capture.screen import video_iter
        from extractor.aim import AimTracker
        from extractor.game_state import extract_state
        from extractor.match_tracker import MatchTracker
        from extractor.vision import VisionPipeline
        from feedback.engine import generate_for_matches
        from memory import database
        from collections import Counter

        tracker = MatchTracker(initial_hero=(hero or None))
        vision = VisionPipeline()
        aim = AimTracker()
        ability_glow_counts: Counter = Counter()
        screen_flash_count = 0
        health_history: list[float] = []
        frames = 0
        for cf in video_iter(Path(video_path)):
            try:
                tracker.ingest_frame(cf.frame, cf.timestamp)
            except Exception:
                pass
            try:
                gs = extract_state(cf.frame, cf.timestamp, health_history)
            except Exception:
                continue
            health_history.append(gs.health_pct)
            tracker.ingest_state(gs)
            try:
                tracker.observe_frame_for_hero(cf.frame)
            except Exception:
                pass
            try:
                bundle = vision.process(cf.frame)
                aim.ingest(bundle)
                for d in bundle.ability_glows:
                    ability_glow_counts[d.kind.split(":", 1)[-1]] += 1
                if bundle.screen_flash is not None:
                    screen_flash_count += 1
            except Exception:
                pass
            frames += 1
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
        fb = generate_for_matches(matches, db_conn=conn)
        return _to_jsonable(fb)

    def _run_replay_inproc(self, replay_dir: str) -> dict:
        from capture.screen import replay_iter
        from extractor.aim import AimTracker
        from extractor.game_state import extract_state
        from extractor.match_tracker import MatchTracker
        from extractor.vision import VisionPipeline
        from feedback.engine import generate_for_matches
        from memory import database
        from collections import Counter

        tracker = MatchTracker()
        vision = VisionPipeline()
        aim = AimTracker()
        ability_glow_counts: Counter = Counter()
        screen_flash_count = 0
        health_history: list[float] = []
        for cf in replay_iter(Path(replay_dir)):
            try:
                tracker.ingest_frame(cf.frame, cf.timestamp)
            except Exception:
                pass
            try:
                gs = extract_state(cf.frame, cf.timestamp, health_history)
            except Exception:
                continue
            health_history.append(gs.health_pct)
            tracker.ingest_state(gs)
            try:
                bundle = vision.process(cf.frame)
                aim.ingest(bundle)
                for d in bundle.ability_glows:
                    ability_glow_counts[d.kind.split(":", 1)[-1]] += 1
                if bundle.screen_flash is not None:
                    screen_flash_count += 1
            except Exception:
                pass
        matches = tracker.finalize()
        aim_m = aim.snapshot()
        if matches:
            last = matches[-1]
            last.events.stats.aim_frames_with_enemy = aim_m.frames_with_enemy_in_sight
            last.events.stats.aim_frames_on_target = aim_m.frames_on_target
            last.events.stats.aim_avg_miss_px = round(aim_m.avg_miss_distance, 1)
        conn = database.connect()
        fb = generate_for_matches(matches, db_conn=conn)
        return _to_jsonable(fb)

    def _run_vod_inproc(self, src: str, title: str) -> dict:
        """Ingest a VOD (download if URL, transcribe, tag). Returns summary."""
        import re as _re

        # If URL, download via yt-dlp first
        video_path: Path
        if src.startswith("http://") or src.startswith("https://"):
            if shutil.which("yt-dlp") is None:
                raise RuntimeError("yt-dlp is not installed")
            match = _re.search(r"(?:v=|youtu\.be/|/shorts/|/embed/)([\w-]{11})", src)
            video_id = match.group(1) if match else uuid.uuid4().hex[:11]
            out_template = str(config.SESSIONS_DIR / f"snap_vod_{video_id}.%(ext)s")
            subprocess.run(
                ["yt-dlp", "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
                 "-o", out_template, "--no-warnings", src],
                check=True,
            )
            candidates = sorted(
                (p for p in config.SESSIONS_DIR.glob(f"snap_vod_{video_id}.*")
                 if p.suffix.lower() in {".mp4", ".mkv", ".webm", ".mov"}),
                key=lambda p: p.stat().st_mtime, reverse=True,
            )
            if not candidates:
                raise RuntimeError(f"Downloaded but no video file found for {video_id}")
            video_path = candidates[0]
        else:
            video_path = Path(src)
            if not video_path.exists():
                raise FileNotFoundError(f"Not found: {video_path}")

        # Pass 1: visual pipeline events
        from capture.screen import video_iter
        from extractor.events import EventDetector
        from extractor.game_state import extract_state
        from extractor.vod import ingest_vod
        from memory import database

        det = EventDetector()
        health_history: list[float] = []
        for cf in video_iter(video_path):
            try:
                state = extract_state(cf.frame, cf.timestamp, health_history)
            except Exception:
                continue
            health_history.append(state.health_pct)
            det.ingest(state)
        events = det.finalize()

        # Pass 2: transcribe + tag + correlate
        conn = database.connect()
        summary = ingest_vod(video_path, events, conn=conn,
                             source_url=src if src.startswith("http") else None,
                             title=title or None)
        return {"summary": summary, "video_path": str(video_path)}

    # ============ Data queries (instant) ============

    def list_vods_data(self) -> list[dict]:
        from memory import database
        from collections import Counter as _Counter

        conn = database.connect()
        rows = conn.execute(
            """
            SELECT v.id, v.title, v.source, v.ingested_at, v.duration_seconds,
                   COUNT(DISTINCT q.id) AS quote_count,
                   COUNT(DISTINCT c.id) AS correlation_count
              FROM vod_reviews v
              LEFT JOIN vod_quotes q ON q.review_id = v.id
              LEFT JOIN vod_correlations c ON c.review_id = v.id
             GROUP BY v.id ORDER BY v.ingested_at DESC
            """
        ).fetchall()
        concept_rows = conn.execute("SELECT concepts_json, heroes_json FROM vod_quotes").fetchall()
        concept_counts: _Counter = _Counter()
        hero_counts: _Counter = _Counter()
        for r in concept_rows:
            for c in json.loads(r["concepts_json"] or "[]"):
                concept_counts[c] += 1
            for h in json.loads(r["heroes_json"] or "[]"):
                hero_counts[h] += 1
        return {
            "vods": [
                {
                    "id": r["id"],
                    "title": r["title"] or "",
                    "source": r["source"] or "",
                    "ingested_at": dt.datetime.fromtimestamp(r["ingested_at"]).strftime("%Y-%m-%d %H:%M"),
                    "duration_minutes": round((r["duration_seconds"] or 0) / 60.0, 1),
                    "quotes": r["quote_count"],
                    "correlations": r["correlation_count"],
                }
                for r in rows
            ],
            "top_concepts": concept_counts.most_common(10),
            "top_heroes": hero_counts.most_common(10),
        }

    def inspect_vod_data(self, review_id_prefix: str) -> dict:
        from memory import database

        conn = database.connect()
        review = conn.execute(
            "SELECT * FROM vod_reviews WHERE id LIKE ? LIMIT 1",
            (review_id_prefix + "%",),
        ).fetchone()
        if not review:
            return {"error": f"No VOD found matching '{review_id_prefix}'"}
        quotes = conn.execute(
            "SELECT * FROM vod_quotes WHERE review_id = ? ORDER BY start_seconds",
            (review["id"],),
        ).fetchall()
        return {
            "review": {
                "id": review["id"],
                "title": review["title"] or "(untitled)",
                "source": review["source"] or "",
                "duration_minutes": round((review["duration_seconds"] or 0) / 60.0, 1),
                "ingested_at": dt.datetime.fromtimestamp(review["ingested_at"]).strftime("%Y-%m-%d %H:%M"),
            },
            "quotes": [
                {
                    "start_seconds": q["start_seconds"],
                    "text": q["text"],
                    "heroes": json.loads(q["heroes_json"] or "[]"),
                    "abilities": json.loads(q["abilities_json"] or "[]"),
                    "concepts": json.loads(q["concepts_json"] or "[]"),
                }
                for q in quotes
            ],
        }

    def list_reports(self) -> list[dict]:
        reports = []
        for path in sorted(config.REPORTS_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                stat = path.stat()
                reports.append({
                    "filename": path.name,
                    "size_bytes": stat.st_size,
                    "modified": dt.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                })
            except Exception:
                continue
        return reports

    def read_report(self, filename: str) -> dict:
        path = config.REPORTS_DIR / filename
        if not path.exists() or not path.is_file():
            return {"error": "Report not found"}
        try:
            return {"markdown": path.read_text()}
        except Exception as e:
            return {"error": str(e)}

    def list_sessions(self) -> list[dict]:
        from memory import database

        conn = database.connect()
        rows = conn.execute(
            "SELECT id, timestamp, hero, duration_minutes, deaths, ult_efficiency_score, "
            "       map, your_comp, enemy_comp "
            "FROM sessions ORDER BY timestamp DESC"
        ).fetchall()
        return [
            {
                "id": r["id"],
                "when": dt.datetime.fromtimestamp(r["timestamp"]).strftime("%Y-%m-%d %H:%M"),
                "hero": r["hero"] or "—",
                "duration_minutes": round(r["duration_minutes"] or 0, 1),
                "deaths": r["deaths"] or 0,
                "ult_score": r["ult_efficiency_score"] or 0,
                "map": r["map"] or "",
                "comp": r["your_comp"] or "",
                "enemy_comp": r["enemy_comp"] or "",
            }
            for r in rows
        ]

    # ============ Finder helpers ============

    def open_reports(self) -> None:
        try:
            subprocess.run(["open", str(config.REPORTS_DIR)])
        except Exception:
            pass

    def open_db(self) -> None:
        try:
            subprocess.run(["open", str(config.PROFILES_DIR)])
        except Exception:
            pass

    def open_screen_recording_settings(self) -> None:
        """Open macOS Screen Recording privacy pane directly."""
        try:
            subprocess.run([
                "open",
                "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture",
            ])
        except Exception:
            pass


def run_app() -> None:
    try:
        import webview
    except ImportError:
        sys.stderr.write(
            "Snap launcher: pywebview not installed. "
            "Run: pip install -r requirements.txt\n"
        )
        return
    html_url = (Path(__file__).resolve().parent / "templates" / "launcher.html").as_uri()
    api = Api()
    window = webview.create_window(
        title="Snap",
        url=html_url,
        width=920,
        height=720,
        min_size=(720, 600),
        js_api=api,
        background_color="#0a0b0e",
    )
    api.set_window(window)
    try:
        webview.start()
    except SystemExit:
        pass


if __name__ == "__main__":
    run_app()
