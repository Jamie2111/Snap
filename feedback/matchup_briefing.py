"""Matchup analysis: given your hero and the enemy team, produce a structured
briefing covering your weaknesses (hard counters), strengths (favorable
matchups), and the single highest-priority action this match.

Used both in real-time (overlay LOBBY/SPAWN modes) and in the post-game
report (Matchups panel).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from knowledge.overwatch import MATCHUPS


DIFFICULTY_ORDER = {
    "very_hard": 4, "hard": 3, "medium": 2, "easy": 1,
}


@dataclass
class MatchupLine:
    enemy: str
    difficulty: str          # very_hard | hard | medium | easy
    key_threat: str
    advice: list[str] = field(default_factory=list)

    @property
    def is_weakness(self) -> bool:
        return self.difficulty in ("very_hard", "hard")

    @property
    def is_strength(self) -> bool:
        return self.difficulty == "easy"


@dataclass
class MatchupBriefing:
    your_hero: str
    enemies: list[str] = field(default_factory=list)
    weaknesses: list[MatchupLine] = field(default_factory=list)
    strengths: list[MatchupLine] = field(default_factory=list)
    neutral: list[MatchupLine] = field(default_factory=list)
    priority: Optional[MatchupLine] = None   # single hardest matchup
    headline: str = ""                       # one-liner for the overlay
    detail: str = ""                         # follow-up sentence

    @property
    def has_data(self) -> bool:
        return bool(self.weaknesses or self.strengths or self.neutral)


def analyze(your_hero: Optional[str], enemies: list[str]) -> MatchupBriefing:
    """Build the full matchup briefing. Skips enemies we have no data on."""
    out = MatchupBriefing(your_hero=your_hero or "", enemies=list(enemies))
    if not your_hero:
        return out
    table = MATCHUPS.get(your_hero, {})
    if not table:
        return out

    for enemy in enemies:
        profile = table.get(enemy)
        if not profile:
            continue
        line = MatchupLine(
            enemy=enemy,
            difficulty=profile.get("difficulty", "medium"),
            key_threat=profile.get("key_threat", ""),
            advice=list(profile.get("advice", [])),
        )
        if line.is_weakness:
            out.weaknesses.append(line)
        elif line.is_strength:
            out.strengths.append(line)
        else:
            out.neutral.append(line)

    # Sort weaknesses worst-first, strengths easiest-first
    out.weaknesses.sort(key=lambda m: DIFFICULTY_ORDER.get(m.difficulty, 0), reverse=True)
    out.strengths.sort(key=lambda m: DIFFICULTY_ORDER.get(m.difficulty, 0))

    # Pick the single priority matchup: worst counter if present, else best target
    if out.weaknesses:
        out.priority = out.weaknesses[0]
    elif out.strengths:
        out.priority = out.strengths[0]

    # Build headline + detail for the overlay
    if out.weaknesses:
        names = ", ".join(m.enemy.title() for m in out.weaknesses[:2])
        out.headline = f"Hard matchup: {names}"
        if out.priority and out.priority.advice:
            out.detail = out.priority.advice[0]
        elif out.priority:
            out.detail = out.priority.key_threat
    elif out.strengths:
        names = ", ".join(m.enemy.title() for m in out.strengths[:2])
        out.headline = f"Target priority: {names}"
        if out.priority and out.priority.advice:
            out.detail = out.priority.advice[0]
    elif out.neutral:
        out.headline = "Neutral matchups"
        out.detail = "No standout counters either way. Play your hero's win condition."

    return out
