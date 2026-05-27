"""Real-time tip generation. Produces a short coaching string appropriate to
the player's current state. Different states get different tip densities:

  FIGHT      one to three words, glanceable, no full sentences
  DYING      one-sentence root-cause of the death you just had
  SPAWN      one-sentence reminder of what to do this life
  LOBBY      full coaching paragraph from the just-finished match
  PLAYING    silent (no tip), so the overlay stays minimal

Pulls from MatchTracker state + just-finished events + knowledge base.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from extractor.player_state import PlayerState
from knowledge.overwatch import HERO_COACHING, MATCHUPS


@dataclass
class RealtimeTip:
    """One tip to surface in the overlay."""
    state: PlayerState
    text: str
    detail: str = ""        # secondary line, shown on bigger overlays only
    urgency: str = "info"   # info | warn | crit


def tip_for_fight(hero: Optional[str], enemies: list[str]) -> Optional[RealtimeTip]:
    """During an active fight: terse, glanceable. Most-relevant hard counter
    if any, else nothing."""
    if hero and enemies:
        for enemy in enemies:
            profile = MATCHUPS.get(hero, {}).get(enemy)
            if profile and profile.get("difficulty") in ("very_hard", "hard"):
                return RealtimeTip(
                    state=PlayerState.FIGHT,
                    text=f"WATCH {enemy.upper()}",
                    urgency="warn",
                )
    return None


def tip_for_dying(
    hero: Optional[str],
    last_death=None,  # PlayerDeath dataclass or None
) -> Optional[RealtimeTip]:
    """During the death screen: root-cause of this specific death."""
    if last_death is None:
        return RealtimeTip(state=PlayerState.DYING, text="Reset.", detail="Take the long way back.")
    if last_death.ult_pct_at_death >= 0.80:
        pct = int(last_death.ult_pct_at_death * 100)
        return RealtimeTip(
            state=PlayerState.DYING,
            text=f"Held ult @ {pct}%",
            detail="Next life: use it earlier or before you commit.",
            urgency="crit",
        )
    if last_death.cooldowns_available:
        abilities = ", ".join(last_death.cooldowns_available[:2])
        return RealtimeTip(
            state=PlayerState.DYING,
            text=f"Had {abilities} ready",
            detail="Cooldowns are insurance. Use one to confirm engages.",
            urgency="crit",
        )
    return RealtimeTip(
        state=PlayerState.DYING,
        text="Reset fully.",
        detail="Half-health engages compound losses.",
    )


def tip_for_spawn(
    hero: Optional[str],
    enemies: list[str],
    last_death=None,
) -> Optional[RealtimeTip]:
    """In spawn room, about to walk out: what to fix this life."""
    if last_death is not None:
        # Continue the previous death's lesson into spawn
        if last_death.ult_pct_at_death >= 0.80:
            return RealtimeTip(
                state=PlayerState.SPAWN,
                text="Use ult earlier this life.",
                detail="If charge is >80%, throw it the next engage.",
            )
    if hero and enemies:
        # Highlight any hard counters before the player even walks out
        hard = [e for e in enemies if MATCHUPS.get(hero, {}).get(e, {}).get("difficulty") in ("very_hard", "hard")]
        if hard:
            return RealtimeTip(
                state=PlayerState.SPAWN,
                text=f"Hard matchup: {hard[0]}",
                detail=MATCHUPS.get(hero, {}).get(hard[0], {}).get("advice", [""])[0],
                urgency="warn",
            )
    if hero and hero in HERO_COACHING:
        wc = HERO_COACHING[hero].get("win_condition", "")
        if wc:
            return RealtimeTip(state=PlayerState.SPAWN, text="Win condition:", detail=wc)
    return None


def tip_for_lobby(last_match_focus: Optional[str]) -> Optional[RealtimeTip]:
    """Between matches: surface the last match's focus next-game advice."""
    if last_match_focus:
        return RealtimeTip(
            state=PlayerState.LOBBY,
            text="Focus next match",
            detail=last_match_focus,
        )
    return RealtimeTip(state=PlayerState.LOBBY, text="Queue up.", detail="Snap is watching.")


def generate(
    state: PlayerState,
    hero: Optional[str],
    enemies: list[str],
    last_death=None,
    last_match_focus: Optional[str] = None,
) -> Optional[RealtimeTip]:
    """Dispatch to the appropriate state-specific generator."""
    if state == PlayerState.FIGHT:
        return tip_for_fight(hero, enemies)
    if state == PlayerState.DYING:
        return tip_for_dying(hero, last_death)
    if state == PlayerState.SPAWN:
        return tip_for_spawn(hero, enemies, last_death)
    if state == PlayerState.LOBBY:
        return tip_for_lobby(last_match_focus)
    return None  # PLAYING: silent
