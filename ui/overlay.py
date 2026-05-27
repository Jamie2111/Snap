"""Floating always-on-top overlay window.

Tiny, dark, monospaced, draggable. Sits over whatever you're watching so you
can keep an eye on Snap without leaving the video.

Runs in its own subprocess (started via main.py) because Tkinter and rumps
both want the macOS main thread. The subprocess receives state via JSON over
stdin lines so we do not need to share Python objects across processes.
"""

from __future__ import annotations

import json
import sys
import time
from typing import Optional


WIDTH = 260
HEIGHT = 92


def _format_clock(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:d}:{s:02d}"


def run_overlay() -> None:
    """Entrypoint when this module is invoked as a script (subprocess).

    Reads JSON snapshots from stdin, one per line. Last line wins."""

    try:
        import tkinter as tk
    except ImportError:
        sys.stderr.write(
            "Snap overlay: tkinter not available. "
            "On macOS with Homebrew Python, install: brew install python-tk\n"
        )
        return

    root = tk.Tk()
    root.title("Snap")
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    try:
        root.attributes("-alpha", 0.92)
    except tk.TclError:
        pass

    # Position top-right of the primary screen by default.
    screen_w = root.winfo_screenwidth()
    x = screen_w - WIDTH - 20
    y = 40
    root.geometry(f"{WIDTH}x{HEIGHT}+{x}+{y}")

    BG = "#0a0a0a"
    FG = "#e6e6e6"
    DIM = "#7a7a7a"
    REC = "#ff3b30"

    root.configure(bg=BG)
    frame = tk.Frame(root, bg=BG, highlightthickness=1, highlightbackground="#222222")
    frame.pack(fill="both", expand=True)

    header = tk.Frame(frame, bg=BG)
    header.pack(fill="x", padx=12, pady=(10, 4))
    dot_lbl = tk.Label(header, text="●", fg=REC, bg=BG, font=("SF Mono", 12, "bold"))
    dot_lbl.pack(side="left")
    rec_lbl = tk.Label(header, text="REC", fg=REC, bg=BG, font=("SF Mono", 10, "bold"), padx=6)
    rec_lbl.pack(side="left")
    clock_lbl = tk.Label(header, text="0:00", fg=FG, bg=BG, font=("SF Mono", 10))
    clock_lbl.pack(side="right")

    hero_lbl = tk.Label(frame, text="—", fg=FG, bg=BG, font=("SF Pro Display", 13, "bold"), anchor="w")
    hero_lbl.pack(fill="x", padx=12, pady=(2, 0))
    event_lbl = tk.Label(frame, text="No events yet", fg=DIM, bg=BG, font=("SF Mono", 9), anchor="w")
    event_lbl.pack(fill="x", padx=12, pady=(0, 10))

    # Drag to reposition
    drag_state = {"x": 0, "y": 0}

    def on_press(e):
        drag_state["x"] = e.x_root - root.winfo_x()
        drag_state["y"] = e.y_root - root.winfo_y()

    def on_drag(e):
        root.geometry(f"+{e.x_root - drag_state['x']}+{e.y_root - drag_state['y']}")

    for w in (frame, header, hero_lbl, event_lbl):
        w.bind("<Button-1>", on_press)
        w.bind("<B1-Motion>", on_drag)

    pulse_state = {"on": True}

    def pulse_dot():
        pulse_state["on"] = not pulse_state["on"]
        dot_lbl.config(fg=REC if pulse_state["on"] else "#660000")
        root.after(700, pulse_dot)

    pulse_dot()

    last_snapshot: dict = {}

    def poll_stdin():
        # Non-blocking-ish read of any available stdin lines
        try:
            import select
            ready, _, _ = select.select([sys.stdin], [], [], 0)
            while ready:
                line = sys.stdin.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    break
                try:
                    snap = json.loads(line)
                    last_snapshot.update(snap)
                except json.JSONDecodeError:
                    pass
                ready, _, _ = select.select([sys.stdin], [], [], 0)
        except Exception:
            pass

        if last_snapshot:
            recording = last_snapshot.get("recording", False)
            elapsed = float(last_snapshot.get("elapsed_seconds", 0.0))
            hero = last_snapshot.get("hero") or "—"
            last_event = last_snapshot.get("last_event") or "Watching..."

            if recording:
                dot_lbl.config(fg=REC)
                rec_lbl.config(text="REC", fg=REC)
            else:
                dot_lbl.config(fg=DIM)
                rec_lbl.config(text="IDLE", fg=DIM)
                pulse_state["on"] = False
            clock_lbl.config(text=_format_clock(elapsed))
            hero_lbl.config(text=str(hero).title() if hero != "—" else "—")
            event_lbl.config(text=last_event[:38])

        root.after(500, poll_stdin)

    poll_stdin()

    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run_overlay()
