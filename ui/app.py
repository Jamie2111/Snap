"""Snap desktop launcher: pywebview WebKit window with HTML/CSS UI.

Loads ui/templates/launcher.html in a native macOS window. Every button
click goes through a JS-to-Python bridge that either picks a file, returns
status, or spawns a Snap subprocess for the actual command.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import config


def _python_exec() -> str:
    return sys.executable


def _spawn_snap(args: list[str]) -> None:
    """Spawn `python main.py <args>` as a child process inheriting stdio so
    the launching terminal shows the subprocess output."""
    cwd = config.BASE_DIR
    cmd = [_python_exec(), str(cwd / "main.py"), *args]
    try:
        subprocess.Popen(cmd, cwd=str(cwd))
    except Exception as e:
        sys.stderr.write(f"Snap launcher: failed to spawn {args}: {e}\n")


class Api:
    """JS-callable bridge. Methods here are exposed as window.pywebview.api.*"""

    def __init__(self) -> None:
        self._window = None

    def set_window(self, window) -> None:
        self._window = window

    # ---- Status (chips at top of launcher) ----

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

    # ---- File pickers (native macOS sheets) ----

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
        if not result:
            return None
        return result[0] if isinstance(result, (list, tuple)) else result

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
        if not result:
            return None
        return result[0] if isinstance(result, (list, tuple)) else result

    # ---- Snap mode dispatchers ----

    def run_live(self, hero: str = "") -> None:
        args = ["--live"]
        h = (hero or "").strip().lower().replace(" ", "")
        if h:
            args.extend(["--hero", h])
        _spawn_snap(args)

    def run_video(self, path: str, hero: str = "") -> None:
        if not path:
            return
        args = ["--video", path]
        h = (hero or "").strip().lower().replace(" ", "")
        if h:
            args.extend(["--hero", h])
        _spawn_snap(args)

    def run_replay(self, path: str) -> None:
        if not path:
            return
        _spawn_snap(["--replay", path])

    def run_demo(self) -> None:
        _spawn_snap(["--demo"])

    def ingest_vod(self, src: str, title: str = "") -> None:
        src = (src or "").strip()
        if not src:
            return
        args = ["--vod", src]
        t = (title or "").strip()
        if t:
            args.extend(["--vod-title", t])
        _spawn_snap(args)

    def list_vods(self) -> None:
        _spawn_snap(["--list-vods"])

    # ---- Folder opens (Finder) ----

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
        width=720,
        height=620,
        min_size=(640, 540),
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
