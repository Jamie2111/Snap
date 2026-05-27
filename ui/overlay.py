"""Discord-style adaptive overlay.

Always-on-top, semi-transparent, sits over the gameplay without blocking it.
Three render modes driven by the player_state field streamed in over stdin:

    FIGHT   tiny pill in the corner (REC dot + clock + 1 word tip if any)
    DYING   medium card with the death's root cause
    SPAWN   medium card with what to do this life
    LOBBY   full coaching card with the just-finished match's focus
    PLAYING heartbeat-only pill

Runs as its own subprocess so its tkinter loop does not fight rumps for the
macOS main thread.

Layout philosophy: minimal, glanceable, never blocks the center of the screen.
Top-right by default, draggable.
"""

from __future__ import annotations

import json
import select
import sys
from typing import Optional


PALETTE = {
    "bg":              "#0b0b0d",
    "bg_subtle":       "#15161a",
    "border":          "#26282d",
    "text":            "#e6e7ea",
    "text_dim":        "#8e919a",
    "text_muted":      "#5b5e66",
    "accent":          "#5f8eff",
    "rec":             "#ff3b30",
    "warn":            "#ffb020",
    "crit":            "#ff5e57",
    "ok":              "#37d67a",
}

FONT_FAMILY = "SF Pro Display"
FONT_MONO = "SF Mono"

# Per-mode dimensions
PILL_W, PILL_H = 160, 38
CARD_W, CARD_H = 320, 110
FULL_W, FULL_H = 360, 180


def _format_clock(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:d}:{s:02d}"


def run_overlay() -> None:
    """Entrypoint when invoked as a subprocess.

    Reads JSON snapshots from stdin and re-renders one of three layouts based
    on the player_state field. Layouts are achieved by recreating the inner
    widgets when state changes, not by trying to morph one layout into another."""

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
        root.attributes("-alpha", 0.93)
    except tk.TclError:
        pass

    # Default position: top-right of primary screen
    screen_w = root.winfo_screenwidth()
    root.geometry(f"{PILL_W}x{PILL_H}+{screen_w - PILL_W - 24}+30")
    root.configure(bg=PALETTE["bg"])

    # Container frame (everything we render lives in here, so we can wipe
    # and rebuild for mode switches)
    container = tk.Frame(root, bg=PALETTE["bg"])
    container.pack(fill="both", expand=True)

    state_holder: dict = {
        "current_mode": "init",
        "last_snapshot": {},
        "pulse_on": True,
    }

    # Drag-to-move
    drag = {"x": 0, "y": 0}

    def on_press(e):
        drag["x"] = e.x_root - root.winfo_x()
        drag["y"] = e.y_root - root.winfo_y()

    def on_drag(e):
        root.geometry(f"+{e.x_root - drag['x']}+{e.y_root - drag['y']}")

    def bind_drag(widget):
        widget.bind("<Button-1>", on_press)
        widget.bind("<B1-Motion>", on_drag)

    def clear_container():
        for w in container.winfo_children():
            w.destroy()

    def render_pill(snap: dict) -> None:
        root.geometry(f"{PILL_W}x{PILL_H}")
        clear_container()
        bind_drag(container)
        inner = tk.Frame(container, bg=PALETTE["bg"], padx=12, pady=8)
        inner.pack(fill="both", expand=True)
        bind_drag(inner)
        dot_color = PALETTE["rec"] if state_holder["pulse_on"] else "#660000"
        if not snap.get("recording"):
            dot_color = PALETTE["text_muted"]
        dot = tk.Label(inner, text="●", fg=dot_color, bg=PALETTE["bg"], font=(FONT_MONO, 11, "bold"))
        dot.pack(side="left")
        clock = tk.Label(inner, text=_format_clock(snap.get("elapsed_seconds", 0)),
                         fg=PALETTE["text"], bg=PALETTE["bg"], font=(FONT_MONO, 10))
        clock.pack(side="left", padx=(8, 0))
        tip = snap.get("tip_text", "")
        if tip:
            color = PALETTE["warn"] if snap.get("tip_urgency") == "warn" else PALETTE["text_dim"]
            tk.Label(inner, text=tip[:16], fg=color, bg=PALETTE["bg"],
                     font=(FONT_MONO, 9, "bold")).pack(side="right")
        bind_drag(dot)
        bind_drag(clock)

    def render_card(snap: dict, *, urgency_color: str) -> None:
        root.geometry(f"{CARD_W}x{CARD_H}")
        clear_container()
        outer = tk.Frame(container, bg=PALETTE["bg"], padx=14, pady=12,
                         highlightthickness=1, highlightbackground=PALETTE["border"])
        outer.pack(fill="both", expand=True)
        bind_drag(outer)
        header = tk.Frame(outer, bg=PALETTE["bg"])
        header.pack(fill="x")
        bind_drag(header)
        state_label = snap.get("player_state", "playing").upper()
        tk.Label(header, text=state_label, fg=urgency_color, bg=PALETTE["bg"],
                 font=(FONT_MONO, 9, "bold")).pack(side="left")
        clock = tk.Label(header, text=_format_clock(snap.get("elapsed_seconds", 0)),
                         fg=PALETTE["text_muted"], bg=PALETTE["bg"], font=(FONT_MONO, 9))
        clock.pack(side="right")
        bind_drag(clock)
        tip_text = snap.get("tip_text", "") or "—"
        tip_lbl = tk.Label(outer, text=tip_text, fg=PALETTE["text"], bg=PALETTE["bg"],
                           font=(FONT_FAMILY, 13, "bold"), anchor="w", wraplength=CARD_W - 30,
                           justify="left")
        tip_lbl.pack(fill="x", pady=(6, 2))
        bind_drag(tip_lbl)
        detail = snap.get("tip_detail", "")
        if detail:
            tk.Label(outer, text=detail, fg=PALETTE["text_dim"], bg=PALETTE["bg"],
                     font=(FONT_FAMILY, 10), anchor="w", wraplength=CARD_W - 30,
                     justify="left").pack(fill="x")

    def render_full(snap: dict) -> None:
        root.geometry(f"{FULL_W}x{FULL_H}")
        clear_container()
        outer = tk.Frame(container, bg=PALETTE["bg"], padx=16, pady=14,
                         highlightthickness=1, highlightbackground=PALETTE["border"])
        outer.pack(fill="both", expand=True)
        bind_drag(outer)
        header = tk.Frame(outer, bg=PALETTE["bg"])
        header.pack(fill="x")
        bind_drag(header)
        tk.Label(header, text="BETWEEN MATCHES", fg=PALETTE["accent"], bg=PALETTE["bg"],
                 font=(FONT_MONO, 9, "bold")).pack(side="left")
        match_idx = snap.get("match_index", 0)
        if match_idx:
            tk.Label(header, text=f"#{match_idx} done",
                     fg=PALETTE["text_muted"], bg=PALETTE["bg"],
                     font=(FONT_MONO, 9)).pack(side="right")
        title = snap.get("tip_text", "") or "Queue up."
        tk.Label(outer, text=title, fg=PALETTE["text"], bg=PALETTE["bg"],
                 font=(FONT_FAMILY, 14, "bold"), anchor="w", wraplength=FULL_W - 32,
                 justify="left").pack(fill="x", pady=(8, 4))
        detail = snap.get("tip_detail", "")
        if detail:
            tk.Label(outer, text=detail, fg=PALETTE["text_dim"], bg=PALETTE["bg"],
                     font=(FONT_FAMILY, 11), anchor="w", wraplength=FULL_W - 32,
                     justify="left").pack(fill="x", pady=(0, 8))
        # Recent context line
        hero = (snap.get("hero") or "").title()
        enemies = snap.get("enemies", []) or []
        if hero:
            context_line = f"{hero}" + (
                f"  ·  vs {', '.join(e.title() for e in enemies[:3])}" if enemies else ""
            )
            tk.Label(outer, text=context_line, fg=PALETTE["text_muted"], bg=PALETTE["bg"],
                     font=(FONT_MONO, 9), anchor="w").pack(fill="x")

    def pick_mode(snap: dict) -> str:
        ps = snap.get("player_state", "playing")
        if ps == "lobby":
            return "full"
        if ps == "dying":
            return "card_crit"
        if ps == "spawn":
            return "card_warn"
        if ps == "fight":
            return "pill"
        return "pill"

    def render(snap: dict) -> None:
        mode = pick_mode(snap)
        if mode != state_holder["current_mode"]:
            state_holder["current_mode"] = mode
        if mode == "full":
            render_full(snap)
        elif mode == "card_crit":
            render_card(snap, urgency_color=PALETTE["crit"])
        elif mode == "card_warn":
            render_card(snap, urgency_color=PALETTE["warn"])
        else:
            render_pill(snap)

    def pulse():
        state_holder["pulse_on"] = not state_holder["pulse_on"]
        # Only redraw pill mode (others don't pulse to stay readable)
        if state_holder["current_mode"] == "pill" and state_holder["last_snapshot"]:
            render_pill(state_holder["last_snapshot"])
        root.after(800, pulse)

    pulse()

    def poll_stdin():
        try:
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
                    state_holder["last_snapshot"] = snap
                    render(snap)
                except json.JSONDecodeError:
                    pass
                ready, _, _ = select.select([sys.stdin], [], [], 0)
        except Exception:
            pass
        root.after(250, poll_stdin)

    render_pill({"recording": True, "elapsed_seconds": 0, "tip_text": "", "tip_urgency": "info"})
    poll_stdin()

    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run_overlay()
