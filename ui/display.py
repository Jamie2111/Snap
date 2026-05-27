"""Terminal live UI. Minimalist Rich panel updated at 1Hz.

Drives off ui.live_state.LiveState so multiple surfaces share one source of
truth. Calling render_live(...) starts a Rich Live context that keeps the
panel pinned to the bottom of the terminal until the context exits.
"""

from __future__ import annotations

import time
from typing import Optional

from rich.align import Align
from rich.box import MINIMAL
from rich.columns import Columns
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ui.live_state import LiveState, LiveSnapshot


def _format_clock(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:d}:{s:02d}"


def _rec_marker(recording: bool, elapsed: float) -> Text:
    """Pulsing red dot when recording, dim when idle."""
    t = Text()
    if recording:
        # Pulse: alternate intensity every second
        bright = (int(time.time()) % 2) == 0
        color = "bold red" if bright else "red"
        t.append("●", style=color)
        t.append("  REC  ", style="bold red")
        t.append(_format_clock(elapsed), style="white")
    else:
        t.append("○", style="dim")
        t.append("  IDLE", style="dim")
    return t


def _meta_grid(snap: LiveSnapshot) -> Table:
    g = Table.grid(padding=(0, 3))
    g.add_column(style="dim", justify="left", no_wrap=True)
    g.add_column(justify="left")
    g.add_row("Hero", snap.hero.title() if snap.hero else "—")
    g.add_row("Allies", ", ".join(a.title() for a in snap.allies) if snap.allies else "—")
    g.add_row("Enemies", ", ".join(e.title() for e in snap.enemies) if snap.enemies else "—")
    g.add_row("Frames", f"{snap.frames_seen:,}")
    events_str = (
        f"{snap.deaths} death{'s' if snap.deaths != 1 else ''}"
        f"  ·  {snap.ults_used} ult{'s' if snap.ults_used != 1 else ''} used"
        f"  ·  {snap.ults_wasted} wasted"
    )
    g.add_row("Events", events_str)
    return g


def _recent_events_table(snap: LiveSnapshot) -> Table:
    t = Table.grid(padding=(0, 2))
    t.add_column(style="dim", justify="right", no_wrap=True)
    t.add_column(justify="left")
    if not snap.recent_events:
        t.add_row("", Text("—", style="dim"))
        return t
    for ts, label in list(snap.recent_events)[-5:]:
        t.add_row(_format_clock(ts), label)
    return t


def _build_panel(snap: LiveSnapshot) -> Panel:
    header = _rec_marker(snap.recording, snap.elapsed_seconds)
    meta = _meta_grid(snap)
    recent_heading = Text("Recent", style="dim italic")
    recent = _recent_events_table(snap)
    body = Group(
        Align.left(header),
        Text(""),
        meta,
        Text(""),
        recent_heading,
        recent,
    )
    return Panel(
        body,
        title=Text("SNAP", style="bold"),
        title_align="left",
        border_style="white",
        box=MINIMAL,
        padding=(1, 2),
    )


def live_panel(state: LiveState, console: Optional[Console] = None) -> Live:
    """Return a started Rich Live context that renders the live panel from
    `state` at 1Hz. Use as: `with live_panel(state):` ... your loop ..."""
    console = console or Console()

    def renderable():
        return _build_panel(state.snapshot())

    return Live(renderable(), console=console, refresh_per_second=1, get_renderable=renderable, transient=False)


# Legacy / backwards-compat helpers
def banner(console: Console, title: str = "SNAP") -> None:
    console.rule(f"[bold]{title}")


def render_live_status(
    console: Console,
    match,
    frames_seen: int,
    last_event: str = "",
) -> None:
    """Old API kept for callers that have not migrated to LiveState."""
    g = Table.grid(padding=(0, 3))
    g.add_column(style="dim")
    g.add_column()
    g.add_row("Frames", str(frames_seen))
    if match and getattr(match, "your_hero", None):
        g.add_row("Hero", match.your_hero.title())
    if match and getattr(match, "allies", None):
        g.add_row("Allies", ", ".join(a.title() for a in match.allies))
    if last_event:
        g.add_row("Last", last_event)
    console.print(Panel(g, title="SNAP", border_style="white", box=MINIMAL, padding=(1, 2)))
