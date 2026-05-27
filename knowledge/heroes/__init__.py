"""Hero knowledge: one module per hero.

Each module in this package exports up to three top-level constants:
    HERO       dict with the coaching profile (role, win condition, abilities, etc.)
    MATCHUPS   dict[enemy_hero, matchup_profile]
    SYNERGIES  dict[ally_hero, synergy_profile]

The aggregator below imports every module and builds the three master dicts
keyed by hero name. knowledge.overwatch re-exports these to keep the public
API stable.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Any


def _discover_modules() -> list:
    """Import every sibling module and return the imported module objects."""
    pkg = importlib.import_module(__name__)
    modules = []
    for info in pkgutil.iter_modules(pkg.__path__):
        if info.name.startswith("_"):
            continue
        mod = importlib.import_module(f"{__name__}.{info.name}")
        modules.append((info.name, mod))
    return modules


def _build() -> tuple[dict[str, Any], dict[str, dict], dict[str, dict]]:
    coaching: dict[str, Any] = {}
    matchups: dict[str, dict] = {}
    synergies: dict[str, dict] = {}
    for hero_key, mod in _discover_modules():
        if hasattr(mod, "HERO"):
            coaching[hero_key] = mod.HERO
        if hasattr(mod, "MATCHUPS"):
            matchups[hero_key] = mod.MATCHUPS
        if hasattr(mod, "SYNERGIES"):
            synergies[hero_key] = mod.SYNERGIES
    return coaching, matchups, synergies


HERO_COACHING, MATCHUPS, SYNERGIES = _build()
