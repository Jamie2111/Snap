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
    """During the death screen: hero-specific root-cause of this death."""
    from knowledge.hero_stats import HERO_ABILITY_LABELS

    if last_death is None:
        # No death-state info; lean on hero positioning instead of generic reset
        if hero and hero in HERO_COACHING:
            mistakes = HERO_COACHING[hero].get("positioning", {}).get("common_positioning_mistakes", [])
            if mistakes:
                return RealtimeTip(state=PlayerState.DYING, text="Reset.",
                                   detail=f"Common {hero.title()} death cause: {mistakes[0].lower()}")
        return RealtimeTip(state=PlayerState.DYING, text="Reset.", detail="Take the long way back.")

    if last_death.ult_pct_at_death >= 0.80:
        pct = int(last_death.ult_pct_at_death * 100)
        # Pull hero-specific ult advice from HERO_COACHING when available.
        detail = "Next life: use it earlier or before you commit."
        if hero:
            ult_key = HERO_ABILITY_LABELS.get(hero, {}).get("ult")
            if ult_key:
                ability = HERO_COACHING.get(hero, {}).get("abilities", {}).get(ult_key, {})
                tmpl = ability.get("feedback_templates", {}).get("died_holding")
                if tmpl:
                    try:
                        detail = tmpl.format(pct=last_death.ult_pct_at_death, duration=0)
                    except Exception:
                        detail = tmpl
                else:
                    mistakes = ability.get("common_mistakes", [])
                    if mistakes:
                        detail = mistakes[0]
        return RealtimeTip(
            state=PlayerState.DYING,
            text=f"Held ult @ {pct}%",
            detail=detail,
            urgency="crit",
        )

    if last_death.cooldowns_available:
        # Convert slot IDs to hero-specific ability names.
        labels = HERO_ABILITY_LABELS.get(hero or "", {}) if hero else {}
        pretty = []
        for slot_id in last_death.cooldowns_available[:2]:
            slot_key = "slot" + slot_id[-1]
            name = labels.get(slot_key)
            pretty.append(name.replace("_", " ").title() if name else slot_id)
        text = f"Had {' + '.join(pretty)} ready"
        detail = "Cooldowns are insurance. Use one to confirm engages."
        if hero and pretty:
            first_slot_id = last_death.cooldowns_available[0]
            first_slot_key = "slot" + first_slot_id[-1]
            first_name = labels.get(first_slot_key)
            if first_name:
                opt = HERO_COACHING.get(hero, {}).get("abilities", {}).get(first_name, {}).get("optimal_use", [])
                if opt:
                    detail = f"Spend {pretty[0]} on: {opt[0].lower()}"
        return RealtimeTip(
            state=PlayerState.DYING,
            text=text,
            detail=detail,
            urgency="crit",
        )

    # Generic death (no ult, no cooldowns): give hero-specific positioning tip
    if hero and hero in HERO_COACHING:
        mistakes = HERO_COACHING[hero].get("positioning", {}).get("common_positioning_mistakes", [])
        if mistakes:
            return RealtimeTip(
                state=PlayerState.DYING, text="Reset fully.",
                detail=f"Common {hero.title()} death cause: {mistakes[0].lower()}",
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
    """In spawn room, about to walk out: what to fix this life.

    Priority: previous-death lesson > hard-counter advice > hero win condition."""
    from feedback.matchup_briefing import analyze

    if last_death is not None and last_death.ult_pct_at_death >= 0.80:
        return RealtimeTip(
            state=PlayerState.SPAWN,
            text="Use ult earlier this life.",
            detail="If charge is >80%, throw it the next engage.",
        )

    briefing = analyze(hero, enemies)
    if briefing.priority and briefing.priority.is_weakness:
        return RealtimeTip(
            state=PlayerState.SPAWN,
            text=f"Hard matchup: {briefing.priority.enemy.title()}",
            detail=briefing.detail or briefing.priority.key_threat,
            urgency="warn",
        )
    if briefing.priority and briefing.priority.is_strength:
        return RealtimeTip(
            state=PlayerState.SPAWN,
            text=f"Target: {briefing.priority.enemy.title()}",
            detail=briefing.detail or "Favorable matchup. Make space for your team here.",
        )
    if hero and hero in HERO_COACHING:
        wc = HERO_COACHING[hero].get("win_condition", "")
        if wc:
            return RealtimeTip(state=PlayerState.SPAWN, text="Win condition:", detail=wc)
    return None


def tip_for_lobby(
    last_match_focus: Optional[str],
    hero: Optional[str] = None,
    enemies: Optional[list[str]] = None,
) -> Optional[RealtimeTip]:
    """Between matches: surface the matchup briefing for the next match if we
    have enemy data, else the last match's focus."""
    from feedback.matchup_briefing import analyze

    briefing = analyze(hero, enemies or [])
    if briefing.has_data:
        return RealtimeTip(
            state=PlayerState.LOBBY,
            text=briefing.headline or "Matchup briefing",
            detail=briefing.detail or "",
            urgency="warn" if briefing.weaknesses else "info",
        )
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
        return tip_for_lobby(last_match_focus, hero=hero, enemies=enemies)
    return None  # PLAYING: silent
