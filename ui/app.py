"""Snap desktop launcher.

A small, clean Tk window that exposes every Snap feature without requiring
terminal commands. Click Live Capture, pick a hero, hit Start. Click VOD
Ingest, paste a YouTube URL. Click Sessions to browse the post-game reports
you've already generated.

Runs Snap modes in subprocesses so a long-running --live or --vod doesn't
freeze the GUI. The launcher itself just dispatches; the rendering of
reports happens in the launched subprocess's terminal output OR the
overlay, depending on the mode.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import config

PALETTE = {
    "bg":          "#0d0e11",
    "panel":       "#15171b",
    "border":      "#272a30",
    "text":        "#e7e8eb",
    "text_dim":    "#9ea1a8",
    "text_muted":  "#5e6168",
    "accent":      "#5f8eff",
    "accent_hi":   "#7da4ff",
    "danger":      "#ff5e57",
}

FONT_FAMILY = "SF Pro Display"
FONT_MONO = "SF Mono"

APP_WIDTH = 720
APP_HEIGHT = 520


def _python_exec() -> str:
    """The Python in the active venv (the same one running this script)."""
    return sys.executable


def _spawn_snap(args: list[str]) -> Optional[subprocess.Popen]:
    """Launch `python main.py <args>` as a child process, inheriting the
    parent's stdout/stderr so the report renders to the terminal that
    launched the GUI."""
    cwd = config.BASE_DIR
    cmd = [_python_exec(), str(cwd / "main.py"), *args]
    try:
        return subprocess.Popen(cmd, cwd=str(cwd))
    except Exception as e:
        print(f"Failed to launch: {e}")
        return None


def run_app() -> None:
    try:
        import tkinter as tk
        from tkinter import filedialog, simpledialog, ttk
    except ImportError:
        sys.stderr.write(
            "Snap launcher: tkinter not available. "
            "On macOS with Homebrew Python, install: brew install python-tk\n"
        )
        return

    root = tk.Tk()
    root.title("Snap")
    root.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
    root.configure(bg=PALETTE["bg"])
    root.minsize(640, 480)

    # ---- Header ----
    header = tk.Frame(root, bg=PALETTE["bg"])
    header.pack(fill="x", padx=24, pady=(20, 4))
    tk.Label(header, text="Snap", fg=PALETTE["text"], bg=PALETTE["bg"],
             font=(FONT_FAMILY, 22, "bold")).pack(side="left")
    tk.Label(header, text="OW2 coach", fg=PALETTE["text_muted"], bg=PALETTE["bg"],
             font=(FONT_MONO, 11)).pack(side="left", padx=(12, 0), pady=(8, 0))

    # ---- Status: tesseract / ffmpeg / live readiness ----
    status_row = tk.Frame(root, bg=PALETTE["bg"])
    status_row.pack(fill="x", padx=24, pady=(0, 18))
    import shutil
    chips = []
    chips.append(("Tesseract", shutil.which(config.TESSERACT_CMD) is not None))
    chips.append(("ffmpeg", shutil.which("ffmpeg") is not None))
    chips.append(("yt-dlp", shutil.which("yt-dlp") is not None))
    for name, ok in chips:
        color = PALETTE["accent"] if ok else PALETTE["danger"]
        chip = tk.Label(status_row, text=("✓ " if ok else "✗ ") + name,
                        fg=color, bg=PALETTE["panel"], font=(FONT_MONO, 9),
                        padx=10, pady=3)
        chip.pack(side="left", padx=(0, 6))

    # ---- Two-column body ----
    body = tk.Frame(root, bg=PALETTE["bg"])
    body.pack(fill="both", expand=True, padx=24, pady=(0, 24))

    left = tk.Frame(body, bg=PALETTE["bg"])
    left.pack(side="left", fill="both", expand=True, padx=(0, 12))
    right = tk.Frame(body, bg=PALETTE["bg"])
    right.pack(side="right", fill="both", expand=True, padx=(12, 0))

    def section_title(parent, label):
        tk.Label(parent, text=label, fg=PALETTE["text_dim"], bg=PALETTE["bg"],
                 font=(FONT_MONO, 9, "bold")).pack(anchor="w", pady=(0, 8))

    def action_button(parent, label, sublabel, on_click):
        btn = tk.Frame(parent, bg=PALETTE["panel"], cursor="hand2",
                       highlightthickness=1, highlightbackground=PALETTE["border"])
        btn.pack(fill="x", pady=(0, 8))
        inner = tk.Frame(btn, bg=PALETTE["panel"], padx=14, pady=12)
        inner.pack(fill="both", expand=True)
        title = tk.Label(inner, text=label, fg=PALETTE["text"], bg=PALETTE["panel"],
                         font=(FONT_FAMILY, 12, "bold"), anchor="w")
        title.pack(fill="x")
        sub = tk.Label(inner, text=sublabel, fg=PALETTE["text_muted"], bg=PALETTE["panel"],
                       font=(FONT_FAMILY, 10), anchor="w")
        sub.pack(fill="x")
        for w in (btn, inner, title, sub):
            w.bind("<Button-1>", lambda _e: on_click())
            w.bind("<Enter>", lambda _e, b=btn: b.configure(bg=PALETTE["border"]))
            w.bind("<Leave>", lambda _e, b=btn: b.configure(bg=PALETTE["panel"]))
        return btn

    # ---- LEFT: live / video / replay ----
    section_title(left, "PLAY")

    def start_live():
        hero = simpledialog.askstring("Live Capture", "Starting hero (blank to auto-detect):",
                                      parent=root) or ""
        args = ["--live"]
        if hero.strip():
            args += ["--hero", hero.strip().lower().replace(" ", "")]
        _spawn_snap(args)

    def start_replay():
        path = filedialog.askdirectory(title="Pick a session-frames directory",
                                       initialdir=str(config.SESSIONS_DIR))
        if not path:
            return
        _spawn_snap(["--replay", path])

    def start_video():
        path = filedialog.askopenfilename(
            title="Pick a gameplay video",
            initialdir=str(config.SESSIONS_DIR),
            filetypes=[("Video", "*.mp4 *.mkv *.webm *.mov"), ("All files", "*.*")],
        )
        if not path:
            return
        hero = simpledialog.askstring("Hero",
                                      "Hero the player in this video is on (blank to auto-detect):",
                                      parent=root) or ""
        args = ["--video", path]
        if hero.strip():
            args += ["--hero", hero.strip().lower().replace(" ", "")]
        _spawn_snap(args)

    def run_demo():
        _spawn_snap(["--demo"])

    action_button(left, "Start Live Capture",
                  "Capture your screen, coach in real time, report on stop", start_live)
    action_button(left, "Analyze Video File",
                  "Pick an MP4 / WebM and run the live pipeline against it", start_video)
    action_button(left, "Replay Saved Frames",
                  "Re-run a previously captured frames directory", start_replay)
    action_button(left, "Demo Report",
                  "Generate a sample 3-match report without any input", run_demo)

    # ---- RIGHT: VOD library + sessions ----
    section_title(right, "LEARN")

    def ingest_vod():
        url_or_path = simpledialog.askstring(
            "Ingest VOD",
            "Paste a YouTube URL or local video file path:",
            parent=root,
        )
        if not url_or_path:
            return
        title = simpledialog.askstring("Title", "VOD title (for reports):", parent=root) or ""
        args = ["--vod", url_or_path.strip()]
        if title.strip():
            args += ["--vod-title", title.strip()]
        _spawn_snap(args)

    def list_vods():
        _spawn_snap(["--list-vods"])

    action_button(right, "Ingest a Coach VOD",
                  "Transcribe + tag a coach review for the Coach Said tier", ingest_vod)
    action_button(right, "Browse VOD Library",
                  "List every VOD ingested and the concept rollups", list_vods)

    section_title(right, "HISTORY")

    def open_reports_folder():
        try:
            subprocess.run(["open", str(config.REPORTS_DIR)])
        except Exception:
            pass

    def open_db_folder():
        try:
            subprocess.run(["open", str(config.PROFILES_DIR)])
        except Exception:
            pass

    action_button(right, "Open Reports Folder",
                  f"{config.REPORTS_DIR}", open_reports_folder)
    action_button(right, "Open Memory DB",
                  "View the SQLite database with your liquid memory", open_db_folder)

    # ---- Footer ----
    footer = tk.Label(root,
                      text="Reports stream to the terminal you launched from. Overlay sits over the game.",
                      fg=PALETTE["text_muted"], bg=PALETTE["bg"], font=(FONT_MONO, 9))
    footer.pack(side="bottom", pady=(0, 12))

    root.mainloop()


if __name__ == "__main__":
    run_app()
