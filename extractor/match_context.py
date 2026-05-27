"""Match context: who you are, who your team is, who the enemy is, comp type.

Scoreboard OCR fires whenever the player holds Tab and the scoreboard renders.
Reads are noisy, so we keep a small history per slot and emit the majority vote.

Comp classification (dive / brawl / poke / hybrid) is a simple heuristic based
on hero roles plus a handful of known-comp anchor heroes. The canonical role
map lives in knowledge.overwatch.HERO_ROLES.
"""

from __future__ import annotations

import logging
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from extractor.ocr import ScoreboardRead

log = logging.getLogger(__name__)


@dataclass
class MatchContext:
    your_hero: Optional[str] = None
    allies: list[str] = field(default_factory=list)
    enemies: list[str] = field(default_factory=list)
    your_comp: Optional[str] = None
    enemy_comp: Optional[str] = None
    map_name: Optional[str] = None
    reads_count: int = 0

    def to_dict(self) -> dict:
        return {
            "your_hero": self.your_hero,
            "allies": self.allies,
            "enemies": self.enemies,
            "your_comp": self.your_comp,
            "enemy_comp": self.enemy_comp,
            "map_name": self.map_name,
            "reads_count": self.reads_count,
        }


# Lazy lookup so we do not hard-couple this module to knowledge.overwatch
# at import time. The role map is consulted when classify_comp is called.
def _hero_role(hero: str) -> str:
    try:
        from knowledge.overwatch import HERO_ROLES  # local import
    except Exception:
        return "unknown"
    return HERO_ROLES.get(hero, "unknown")


def _comp_anchors() -> dict[str, set[str]]:
    """Pull anchor heroes per comp from knowledge.overwatch.COMP_TYPES so the
    classifier and the knowledge base stay in sync."""
    try:
        from knowledge.overwatch import COMP_TYPES  # local import to avoid cycle
    except Exception:
        return {}
    return {name: set(spec.get("anchors", ())) for name, spec in COMP_TYPES.items() if spec.get("anchors")}


def classify_comp(heroes: list[str]) -> str:
    """Classify a team comp by scanning for anchor heroes. Each comp type in
    COMP_TYPES contributes its anchor set. Highest match count wins, with a
    minimum threshold of 2 anchors. Below that, we fall back to a role-based
    heuristic and 'hybrid' as the default."""

    if not heroes:
        return "hybrid"
    anchors = _comp_anchors()
    anchor_scores: Counter[str] = Counter()
    for h in heroes:
        for comp, names in anchors.items():
            if h in names:
                anchor_scores[comp] += 1
    if anchor_scores:
        top, count = anchor_scores.most_common(1)[0]
        if count >= 2:
            return top
    role_counts = Counter(_hero_role(h) for h in heroes)
    if role_counts.get("tank", 0) >= 1 and role_counts.get("dps", 0) <= 1:
        return "brawl"
    return "hybrid"


class MatchContextTracker:
    """Smooths noisy scoreboard reads into a stable MatchContext.

    For each slot (your_hero, ally_1..4, enemy_1..5) we keep the last N reads
    and emit the majority value. A single misread cannot flip the context."""

    def __init__(self, history_size: int = 3):
        self.history_size = history_size
        self.ally_history: dict[int, deque[str]] = defaultdict(lambda: deque(maxlen=history_size))
        self.enemy_history: dict[int, deque[str]] = defaultdict(lambda: deque(maxlen=history_size))
        self.your_history: deque[str] = deque(maxlen=history_size)
        self.context = MatchContext()

    def ingest_scoreboard(self, read: ScoreboardRead) -> MatchContext:
        if read.your_hero:
            self.your_history.append(read.your_hero)
        for i, name in enumerate(read.allies):
            self.ally_history[i].append(name)
        for i, name in enumerate(read.enemies):
            self.enemy_history[i].append(name)
        self.context.reads_count += 1
        self._recompute()
        return self.context

    def set_initial_hero(self, hero: str) -> None:
        self.your_history.append(hero)
        self.context.your_hero = hero
        self._recompute()

    def set_map(self, map_name: str) -> None:
        self.context.map_name = map_name

    def _majority(self, history: deque[str]) -> Optional[str]:
        if not history:
            return None
        return Counter(history).most_common(1)[0][0]

    def ingest_hero_observation(self, hero: str, source: str) -> MatchContext:
        """Direct hero name read (from pick screen, swap banner, spawn room).

        These sources are higher-confidence than scoreboard OCR (default skin,
        always-visible, single-name field). One read is enough to lock in the
        hero. Subsequent reads of a different hero indicate a swap."""

        prev = self.context.your_hero
        # Pick screen and swap banner are authoritative for hero swaps.
        if source in ("pick_screen", "swap_banner") and hero != prev:
            log.info("Hero swap detected via %s: %s -> %s", source, prev, hero)
            self.your_history.clear()
        self.your_history.append(hero)
        self._recompute()
        return self.context

    def observe_frame(self, frame: "np.ndarray") -> Optional[str]:
        """Try every skin-independent hero-name source on this frame.

        Order of priority: pick screen > swap banner > spawn room > scoreboard.
        Returns the hero name detected (and updates context) or None if no
        signal fired this frame."""

        # Import lazily so unit tests do not require the OCR module's heavy
        # tesseract import at module-load time.
        from extractor import game_state, ocr

        if game_state.detect_pick_screen_visible(frame):
            hero = ocr.read_pick_screen_hero(frame)
            if hero:
                self.ingest_hero_observation(hero, "pick_screen")
                return hero
        if game_state.detect_swap_banner_visible(frame):
            hero = ocr.read_swap_banner_hero(frame)
            if hero:
                self.ingest_hero_observation(hero, "swap_banner")
                return hero
        if game_state.detect_spawn_room_visible(frame):
            hero = ocr.read_spawn_room_hero(frame)
            if hero:
                self.ingest_hero_observation(hero, "spawn_room")
                return hero
        if game_state.detect_scoreboard_visible(frame):
            sb = ocr.read_scoreboard(frame)
            self.ingest_scoreboard(sb)
            return sb.your_hero
        return None

    def _recompute(self) -> None:
        you = self._majority(self.your_history)
        if you:
            self.context.your_hero = you
        allies: list[str] = []
        for i in sorted(self.ally_history.keys()):
            v = self._majority(self.ally_history[i])
            if v:
                allies.append(v)
        enemies: list[str] = []
        for i in sorted(self.enemy_history.keys()):
            v = self._majority(self.enemy_history[i])
            if v:
                enemies.append(v)
        self.context.allies = allies
        self.context.enemies = enemies
        team = ([you] if you else []) + allies
        self.context.your_comp = classify_comp(team) if team else None
        self.context.enemy_comp = classify_comp(enemies) if enemies else None
