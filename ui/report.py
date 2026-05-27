"""Post-game terminal report (Rich) plus markdown writer."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Optional

from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

import config
from feedback.engine import Feedback


def _grade_color(grade: str) -> str:
    return {"A": "green", "B": "cyan", "C": "yellow", "D": "red"}.get(grade, "white")


def _summary_panel(fb: Feedback) -> Panel:
    s = fb.session_summary
    table = Table.grid(padding=(0, 2))
    table.add_column(justify="left")
    table.add_column(justify="right")
    table.add_row("Ult Efficiency", f"[bold]{s.ult_efficiency_score}/100[/]")
    table.add_row("Deaths", str(s.deaths))
    table.add_row("Avoidable", str(s.estimated_avoidable_deaths))
    table.add_row("Session Grade", f"[bold {_grade_color(s.session_grade)}]{s.session_grade}[/]")
    return Panel(table, title="Session", border_style="cyan", box=ROUNDED)


def _context_panel(fb: Feedback) -> Optional[Panel]:
    m = fb.match_context
    if m is None or not m.your_hero:
        return None
    rows: list[str] = []
    rows.append(f"[bold]You:[/] {m.your_hero.title()}  ({m.your_comp or '?'})")
    if m.allies:
        rows.append("[bold]Allies:[/] " + ", ".join(a.title() for a in m.allies))
    if m.enemies:
        rows.append(f"[bold]Enemy:[/] " + ", ".join(e.title() for e in m.enemies) + f"  ({m.enemy_comp or '?'})")
    if m.map_name:
        rows.append(f"[bold]Map:[/] {m.map_name}")
    return Panel(
        "\n".join(rows),
        title="Match Context",
        border_style="blue",
        box=ROUNDED,
    )


def _critical_panel(fb: Feedback) -> Optional[Panel]:
    if not fb.critical:
        return None
    lines: list[str] = []
    for c in fb.critical:
        lines.append(f"[red bold]●[/] {c.render()}")
    return Panel("\n\n".join(lines), title="Critical", border_style="red", box=ROUNDED)


def _improvement_panel(fb: Feedback) -> Optional[Panel]:
    if not fb.improvement:
        return None
    lines: list[str] = []
    for imp in fb.improvement:
        lines.append(
            f"[yellow bold]●[/] {imp.pattern}: {imp.suggestion}\n"
            f"   [dim]{imp.historical_trend}, n={imp.frequency}[/]"
        )
    return Panel("\n\n".join(lines), title="Improvement", border_style="yellow", box=ROUNDED)


def _insight_panel(fb: Feedback) -> Optional[Panel]:
    if not fb.insight:
        return None
    blocks: list[str] = []
    for ins in fb.insight:
        block = [f"[magenta bold]●[/] {ins.observation}"]
        if ins.evidence:
            block.append(f"   [dim]Evidence: {ins.evidence}[/]")
        if ins.principle:
            block.append(f"   [italic]{ins.principle}[/]")
        blocks.append("\n".join(block))
    return Panel("\n\n".join(blocks), title="Insight", border_style="magenta", box=ROUNDED)


def _focus_panel(fb: Feedback) -> Panel:
    text = Text(fb.one_thing_to_focus_on or "", style="bold")
    if fb.progress_acknowledgment:
        text.append("\n\n")
        text.append(fb.progress_acknowledgment, style="green italic")
    return Panel(text, title="Focus Next Game", border_style="green", box=ROUNDED)


def render(fb: Feedback, console: Optional[Console] = None) -> None:
    console = console or Console()
    panels = [p for p in (
        _summary_panel(fb),
        _context_panel(fb),
        _critical_panel(fb),
        _improvement_panel(fb),
        _insight_panel(fb),
        _focus_panel(fb),
    ) if p is not None]
    console.rule("[bold cyan]SNAP  Session Report")
    for p in panels:
        console.print(p)


def write_markdown(fb: Feedback, session_id: str, reports_dir: Optional[Path] = None) -> Path:
    reports_dir = Path(reports_dir or config.REPORTS_DIR)
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = reports_dir / f"{stamp}-{session_id}.md"

    lines: list[str] = []
    s = fb.session_summary
    lines.append(f"# Snap Session Report  {stamp}\n")
    lines.append(f"**Hero:** {s.hero or 'unknown'}    **Grade:** {s.session_grade}")
    lines.append(f"**Ult Efficiency:** {s.ult_efficiency_score}/100    **Deaths:** {s.deaths} (avoidable: {s.estimated_avoidable_deaths})")
    lines.append("")
    m = fb.match_context
    if m and m.your_hero:
        lines.append("## Match Context")
        lines.append(f"- You: {m.your_hero} ({m.your_comp or '?'})")
        if m.allies:
            lines.append(f"- Allies: {', '.join(m.allies)}")
        if m.enemies:
            lines.append(f"- Enemy: {', '.join(m.enemies)} ({m.enemy_comp or '?'})")
        if m.map_name:
            lines.append(f"- Map: {m.map_name}")
        lines.append("")
    if fb.critical:
        lines.append("## Critical")
        for c in fb.critical:
            lines.append(f"- {c.render()}")
        lines.append("")
    if fb.improvement:
        lines.append("## Improvement")
        for imp in fb.improvement:
            lines.append(f"- **{imp.pattern}**: {imp.suggestion}  ({imp.historical_trend}, n={imp.frequency})")
        lines.append("")
    if fb.insight:
        lines.append("## Insight")
        for ins in fb.insight:
            lines.append(f"- **{ins.observation}**")
            if ins.evidence:
                lines.append(f"  - Evidence: {ins.evidence}")
            if ins.principle:
                lines.append(f"  - Principle: {ins.principle}")
        lines.append("")
    lines.append("## Focus Next Game")
    lines.append(fb.one_thing_to_focus_on or "")
    if fb.progress_acknowledgment:
        lines.append("")
        lines.append(f"*{fb.progress_acknowledgment}*")
    path.write_text("\n".join(lines) + "\n")
    return path
