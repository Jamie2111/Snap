"""Overwatch 2 coaching knowledge base.

Per-hero content lives in knowledge.heroes (one module per hero). This module
aggregates the per-hero modules and exposes the API the rest of the codebase
uses: HERO_COACHING, MATCHUPS, SYNERGIES, plus PATCH_CONTEXT, POSITIONING_PRINCIPLES,
GAME_SENSE_RULES, HERO_ROLES, COMP_TYPES.

The architecture supports easy expansion: drop a new file in knowledge/heroes/
and it is picked up automatically on next import.
"""

from __future__ import annotations

from knowledge.heroes import HERO_COACHING, MATCHUPS, SYNERGIES

HERO_ROLES: dict[str, str] = {
    "ana": "support", "baptiste": "support", "brigitte": "support",
    "illari": "support", "juno": "support", "kiriko": "support",
    "lifeweaver": "support", "lucio": "support", "mercy": "support",
    "moira": "support", "zenyatta": "support",
    "dva": "tank", "doomfist": "tank", "junkerqueen": "tank", "mauga": "tank",
    "orisa": "tank", "ramattra": "tank", "reinhardt": "tank", "roadhog": "tank",
    "sigma": "tank", "winston": "tank", "wreckingball": "tank", "zarya": "tank",
    "ashe": "dps", "bastion": "dps", "cassidy": "dps", "echo": "dps",
    "freja": "dps", "genji": "dps", "hanzo": "dps", "junkrat": "dps",
    "mei": "dps", "pharah": "dps", "reaper": "dps", "sojourn": "dps",
    "soldier76": "dps", "sombra": "dps", "symmetra": "dps", "torbjorn": "dps",
    "tracer": "dps", "venture": "dps", "widowmaker": "dps",
}


COMP_TYPES: dict[str, dict] = {
    "dive": {
        "win_condition": "Coordinated cooldown burns on isolated supports. Commit and escape together. Avoid prolonged brawls.",
        "anchors": ("winston", "dva", "sombra", "tracer", "genji", "wreckingball"),
        "support_picks": ("ana", "lucio", "kiriko"),
        "shape": "fast",
    },
    "brawl": {
        "win_condition": "Shield uptime, group movement, slow push to choke control. Win sustained fights, not picks.",
        "anchors": ("reinhardt", "zarya", "mauga", "brigitte", "lucio", "junkerqueen", "ramattra"),
        "support_picks": ("ana", "lucio", "brigitte", "kiriko"),
        "shape": "grouped",
    },
    "poke": {
        "win_condition": "Hold long sightlines, force their team to engage uphill. Build ult charge with safe damage.",
        "anchors": ("widowmaker", "hanzo", "ashe", "pharah", "sigma", "soldier76", "echo"),
        "support_picks": ("baptiste", "ana", "zenyatta"),
        "shape": "spread",
    },
    "anti_dive": {
        "win_condition": "Layer peel so divers cannot isolate your backline. Punish commitment then push.",
        "anchors": ("brigitte", "cassidy", "sombra", "hog", "mei"),
        "support_picks": ("brigitte", "kiriko", "baptiste"),
        "shape": "peel",
    },
    "rush": {
        "win_condition": "Group up and push together with speed + sustain. Chain ults to deny resets.",
        "anchors": ("reinhardt", "lucio", "junkerqueen", "brigitte", "mauga"),
        "support_picks": ("lucio", "brigitte", "kiriko"),
        "shape": "grouped",
    },
    "hold": {
        "win_condition": "Defensive setup. Force the enemy into your sightlines. Stall to extend the round.",
        "anchors": ("bastion", "torbjorn", "symmetra", "mei", "sigma"),
        "support_picks": ("baptiste", "moira", "zenyatta"),
        "shape": "stationary",
    },
    "bunker": {
        "win_condition": "Concentrated fortified position. Force teamfights into your zone of control.",
        "anchors": ("orisa", "bastion", "baptiste", "torbjorn"),
        "support_picks": ("baptiste", "mercy"),
        "shape": "stationary",
    },
    "pirate_ship": {
        "win_condition": "Mobile fortified payload push. Bastion + tank shield + amp aggression.",
        "anchors": ("bastion", "orisa", "baptiste", "mercy"),
        "support_picks": ("mercy", "baptiste"),
        "shape": "grouped",
    },
    "hybrid": {
        "win_condition": "Adapt fight by fight. You don't have a default win condition. Read the enemy comp first.",
        "anchors": (),
        "support_picks": (),
        "shape": "mixed",
    },
}


PATCH_CONTEXT: dict = {
    "current_season": "Season 15",
    "meta_notes": [
        "Tank-heavy compositions dominate at most ranks.",
        "Ana is a near-mandatory pick into almost every support combo.",
        "Tracer and Genji are strong flankers this patch.",
        "Support self-sustain has been reduced. Supports depend more on team protection.",
        "Overtime fights reward teams with better ult economy.",
    ],
    "hero_tier": {
        "S": ["ana", "lucio", "reinhardt", "tracer", "kiriko", "winston", "zarya"],
        "A": ["mercy", "zenyatta", "genji", "widowmaker", "sigma", "junkerqueen", "ashe", "sojourn"],
        "B": ["echo", "soldier76", "brigitte", "baptiste", "dva", "cassidy", "juno"],
    },
}


POSITIONING_PRINCIPLES: list[str] = [
    "Always know where your escape route is before engaging.",
    "High ground wins most fights. Contest it or deny it.",
    "The player who creates space wins. Don't fight in the open if you don't have to.",
    "Stay grouped during ult fights, spread during poke phases.",
    "Your position before the fight starts matters more than your mechanics during it.",
]


GAME_SENSE_RULES: list[dict] = [
    {
        "rule": "Ult economy",
        "principle": "Winning ult trades wins rounds. If the enemy team has 3 ults and you have 1, do not fight. Disengage and charge ults.",
        "signal": "deaths_with_ult_above_80pct > 2",
    },
    {
        "rule": "Fight timing",
        "principle": "Pick your fights. An even fight you force is worse than an uneven fight you wait for.",
        "signal": "fights_engaged_at_below_50pct_health > 3",
    },
    {
        "rule": "Cooldown sequencing",
        "principle": "Use your weakest cooldown first to confirm the engage. Save your best cooldown for the decisive moment.",
        "signal": "cooldown_held_after_death > 2",
    },
    {
        "rule": "Reset awareness",
        "principle": "After losing a fight, reset fully before engaging again. Half-health engages compound losses.",
        "signal": "avg_health_at_engage < 0.6",
    },
]


def classify_comp(heroes: list[str]) -> str:
    """Public re-export so callers can use knowledge.overwatch.classify_comp."""
    from extractor.match_context import classify_comp as impl

    return impl(heroes)
