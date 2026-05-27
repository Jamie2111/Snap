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

    def run_live(self, hero: str = "") -> None:
        """Live capture is special: it spawns a subprocess so the overlay
        can live in its own window across all Spaces. The launcher does
        not lock up waiting for it."""
        cwd = config.BASE_DIR
        args = [_python_exec(), str(cwd / "main.py"), "--live"]
        h = (hero or "").strip().lower().replace(" ", "")
        if h:
            args.extend(["--hero", h])
        try:
            proc = subprocess.Popen(args, cwd=str(cwd))
            self._active_subprocs.append(proc)
        except Exception:
            log.exception("Failed to launch live capture")

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
