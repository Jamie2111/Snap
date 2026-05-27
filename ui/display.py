"""Live in-session display (Rich). Heartbeat, current hero, allies, last event."""

from __future__ import annotations

from typing import Optional

from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from extractor.match_context import MatchContext


def render_live_status(
    console: Console,
    match: Optional[MatchContext],
    frames_seen: int,
    last_event: str = "",
) -> None:
    table = Table.grid(padding=(0, 2))
    table.add_column(justify="left")
    table.add_column(justify="left")
    table.add_row("Frames", str(frames_seen))
    if match and match.your_hero:
        table.add_row("Hero", match.your_hero.title())
    if match and match.allies:
        table.add_row("Allies", ", ".join(a.title() for a in match.allies))
    if match and match.enemies:
        table.add_row("Enemy", ", ".join(e.title() for e in match.enemies))
    if last_event:
        table.add_row("Last event", last_event)
    console.print(Panel(table, title="Snap (live)", border_style="cyan", box=ROUNDED))


def banner(console: Console, title: str = "SNAP") -> None:
    console.rule(f"[bold cyan]{title}")
