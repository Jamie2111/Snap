"""Per-hero stat schemas and benchmarks.

For each hero, we declare:
  - ability_slot_map: which OW2 keybind maps to which slot 1..4 + the ult
  - tracked_stats: names of stats Snap computes internally from events
  - benchmarks: target values per skill tier (avg / diamond / gm) for each
    tracked stat. Used by the feedback engine to flag under-performance.

Stats are computed by extractor/match_stats.py from existing event data
(cooldown transitions, ult uses, ult hold durations, fight survival). We
don't OCR the post-match scoreboard. Pure internal calculation.
"""

from __future__ import annotations

from typing import Optional


# Slot order is consistent across heroes:
#   slot 1 = primary ability (Shift / E / RMB depending on hero)
#   slot 2 = secondary ability
#   slot 3 = passive/movement (e.g. Tracer recall, Genji deflect)
#   slot 4 = situational (some heroes lack a slot 4)
# The ult is tracked separately via ult_pct.
HERO_ABILITY_LABELS: dict[str, dict[str, str]] = {
    "tracer": {"slot1": "blink", "slot2": "recall", "ult": "pulse_bomb"},
    "ana": {"slot1": "sleep_dart", "slot2": "biotic_grenade", "ult": "nano_boost"},
    "lucio": {"slot1": "amp_it_up", "slot2": "soundwave", "slot3": "crossfade", "ult": "sound_barrier"},
    "mercy": {"slot1": "guardian_angel", "slot2": "resurrect", "ult": "valkyrie"},
    "reinhardt": {"slot1": "fire_strike", "slot2": "charge", "slot3": "barrier_field", "ult": "earthshatter"},
    "genji": {"slot1": "swift_strike", "slot2": "deflect", "ult": "dragonblade"},
    "zenyatta": {"slot1": "orb_of_discord", "slot2": "orb_of_harmony", "ult": "transcendence"},
    "widowmaker": {"slot1": "grappling_hook", "slot2": "venom_mine", "slot3": "infra_sight_passive", "ult": "infra_sight"},
    "kiriko": {"slot1": "swift_step", "slot2": "protection_suzu", "ult": "kitsune_rush"},
    "winston": {"slot1": "jump_pack", "slot2": "barrier_projector", "ult": "primal_rage"},
    "sigma": {"slot1": "accretion", "slot2": "experimental_barrier", "slot3": "kinetic_grasp", "ult": "gravitic_flux"},
    "zarya": {"slot1": "particle_barrier", "slot2": "projected_barrier", "ult": "graviton_surge"},
    "junkerqueen": {"slot1": "jagged_blade", "slot2": "commanding_shout", "ult": "rampage"},
    "dva": {"slot1": "boosters", "slot2": "defense_matrix", "slot3": "micro_missiles", "ult": "self_destruct"},
    "orisa": {"slot1": "javelin_throw", "slot2": "fortify", "slot3": "energy_javelin", "ult": "terra_surge"},
    "ramattra": {"slot1": "ravenous_vortex", "slot2": "nemesis_form", "slot3": "void_barrier", "ult": "annihilation"},
    "mauga": {"slot1": "overrun", "slot2": "cardiac_overdrive", "ult": "cage_fight"},
    "doomfist": {"slot1": "rocket_punch", "slot2": "power_block", "slot3": "seismic_slam", "ult": "meteor_strike"},
    "roadhog": {"slot1": "chain_hook", "slot2": "take_a_breather", "slot3": "pig_pen", "ult": "whole_hog"},
    "wreckingball": {"slot1": "grappling_claw", "slot2": "adaptive_shield", "slot3": "piledriver", "ult": "minefield"},
    "ashe": {"slot1": "dynamite", "slot2": "coach_gun", "ult": "bob"},
    "sojourn": {"slot1": "disruptor_shot", "slot2": "power_slide", "ult": "overclock"},
    "cassidy": {"slot1": "magnetic_grenade", "slot2": "combat_roll", "slot3": "flashbang", "ult": "deadeye"},
    "soldier76": {"slot1": "helix_rockets", "slot2": "biotic_field", "slot3": "sprint", "ult": "tactical_visor"},
    "sombra": {"slot1": "hack", "slot2": "virus", "slot3": "translocator", "ult": "emp"},
    "pharah": {"slot1": "concussive_blast", "slot2": "jump_jet", "ult": "barrage"},
    "reaper": {"slot1": "wraith_form", "slot2": "shadow_step", "ult": "death_blossom"},
    "hanzo": {"slot1": "storm_arrow", "slot2": "sonic_arrow", "slot3": "lunge", "ult": "dragonstrike"},
    "echo": {"slot1": "sticky_bombs", "slot2": "focusing_beam", "slot3": "flight", "ult": "duplicate"},
    "junkrat": {"slot1": "concussion_mine", "slot2": "steel_trap", "ult": "riptire"},
    "mei": {"slot1": "cryo_freeze", "slot2": "ice_wall", "ult": "blizzard"},
    "bastion": {"slot1": "configuration_assault", "slot2": "a36_tactical_grenade", "ult": "configuration_artillery"},
    "symmetra": {"slot1": "sentry_turret", "slot2": "photon_barrier", "slot3": "teleporter", "ult": "teleporter_ult"},
    "torbjorn": {"slot1": "deploy_turret", "slot2": "overload", "ult": "molten_core"},
    "venture": {"slot1": "drill_dash", "slot2": "burrow", "ult": "tectonic_shock"},
    "freja": {"slot1": "take_aim", "slot2": "quick_dash", "ult": "aerodynamic_strike"},
    "brigitte": {"slot1": "whip_shot", "slot2": "shield_bash", "slot3": "repair_pack", "ult": "rally"},
    "baptiste": {"slot1": "regenerative_burst", "slot2": "immortality_field", "slot3": "exo_boots", "ult": "amplification_matrix"},
    "moira": {"slot1": "biotic_orb", "slot2": "fade", "ult": "coalescence"},
    "lifeweaver": {"slot1": "petal_platform", "slot2": "life_grip", "slot3": "healing_blossom", "ult": "tree_of_life"},
    "illari": {"slot1": "healing_pylon", "slot2": "outburst", "ult": "captive_sun"},
    "juno": {"slot1": "pulsar_torpedoes", "slot2": "hyper_ring", "slot3": "glide_boost", "ult": "orbital_ray"},
}


# Per-hero benchmark values. Each entry is {stat_name: {avg, diamond, gm}}.
# Stats Snap can compute internally without OCR:
#   ult_uses_per_10min     how often the ult fires (proxy for charge speed)
#   ult_avg_hold_seconds   time between full charge and use (lower = better)
#   ability_slot_N_uses_per_10min   throughput per ability slot
#   fight_survival_rate    survived / engaged
#   deaths_per_10min       death rate normalized by playtime
#
# Numbers are rough but realistic; refine with more data over time.
HERO_BENCHMARKS: dict[str, dict[str, dict[str, float]]] = {
    "tracer": {
        "ult_uses_per_10min":         {"avg": 2.0,  "diamond": 3.0,  "gm": 4.5},
        "ult_avg_hold_seconds":       {"avg": 18.0, "diamond": 10.0, "gm": 5.0},
        "slot1_uses_per_10min":       {"avg": 80.0, "diamond": 110.0, "gm": 140.0},  # blinks
        "slot2_uses_per_10min":       {"avg": 3.0,  "diamond": 4.0,  "gm": 5.0},     # recalls
        "deaths_per_10min":           {"avg": 9.0,  "diamond": 6.0,  "gm": 4.0},
        "fight_survival_rate":        {"avg": 0.40, "diamond": 0.55, "gm": 0.70},
    },
    "ana": {
        "ult_uses_per_10min":         {"avg": 1.2,  "diamond": 1.8,  "gm": 2.4},
        "ult_avg_hold_seconds":       {"avg": 30.0, "diamond": 18.0, "gm": 10.0},
        "slot1_uses_per_10min":       {"avg": 3.0,  "diamond": 4.5,  "gm": 6.0},     # sleep darts
        "slot2_uses_per_10min":       {"avg": 4.5,  "diamond": 6.0,  "gm": 7.5},     # anti-nades
        "deaths_per_10min":           {"avg": 4.5,  "diamond": 3.0,  "gm": 2.0},
        "fight_survival_rate":        {"avg": 0.55, "diamond": 0.70, "gm": 0.82},
    },
    "kiriko": {
        "ult_uses_per_10min":         {"avg": 1.0,  "diamond": 1.5,  "gm": 2.0},
        "ult_avg_hold_seconds":       {"avg": 30.0, "diamond": 20.0, "gm": 12.0},
        "slot1_uses_per_10min":       {"avg": 6.0,  "diamond": 9.0,  "gm": 12.0},    # TPs
        "slot2_uses_per_10min":       {"avg": 5.0,  "diamond": 7.0,  "gm": 9.0},     # suzus
        "deaths_per_10min":           {"avg": 5.0,  "diamond": 3.5,  "gm": 2.5},
        "fight_survival_rate":        {"avg": 0.50, "diamond": 0.65, "gm": 0.78},
    },
    "mercy": {
        "ult_uses_per_10min":         {"avg": 0.8,  "diamond": 1.2,  "gm": 1.5},
        "ult_avg_hold_seconds":       {"avg": 35.0, "diamond": 22.0, "gm": 15.0},
        "slot2_uses_per_10min":       {"avg": 1.5,  "diamond": 2.5,  "gm": 3.5},     # resurrects
        "deaths_per_10min":           {"avg": 3.5,  "diamond": 2.5,  "gm": 1.5},
        "fight_survival_rate":        {"avg": 0.65, "diamond": 0.78, "gm": 0.88},
    },
    "reinhardt": {
        "ult_uses_per_10min":         {"avg": 1.5,  "diamond": 2.2,  "gm": 3.0},
        "ult_avg_hold_seconds":       {"avg": 25.0, "diamond": 15.0, "gm": 8.0},
        "slot1_uses_per_10min":       {"avg": 8.0,  "diamond": 11.0, "gm": 14.0},    # fire strikes
        "slot2_uses_per_10min":       {"avg": 2.5,  "diamond": 3.5,  "gm": 4.5},     # charges
        "deaths_per_10min":           {"avg": 6.0,  "diamond": 4.5,  "gm": 3.0},
        "fight_survival_rate":        {"avg": 0.50, "diamond": 0.62, "gm": 0.75},
    },
    "genji": {
        "ult_uses_per_10min":         {"avg": 1.5,  "diamond": 2.2,  "gm": 3.0},
        "ult_avg_hold_seconds":       {"avg": 28.0, "diamond": 18.0, "gm": 10.0},
        "slot1_uses_per_10min":       {"avg": 30.0, "diamond": 42.0, "gm": 55.0},    # dashes
        "slot2_uses_per_10min":       {"avg": 5.0,  "diamond": 7.0,  "gm": 9.0},     # deflects
        "deaths_per_10min":           {"avg": 9.0,  "diamond": 6.0,  "gm": 4.0},
        "fight_survival_rate":        {"avg": 0.40, "diamond": 0.55, "gm": 0.70},
    },
    "winston": {
        "ult_uses_per_10min":         {"avg": 1.0,  "diamond": 1.6,  "gm": 2.2},
        "ult_avg_hold_seconds":       {"avg": 28.0, "diamond": 18.0, "gm": 10.0},
        "slot1_uses_per_10min":       {"avg": 8.0,  "diamond": 11.0, "gm": 14.0},    # jumps
        "slot2_uses_per_10min":       {"avg": 5.0,  "diamond": 7.0,  "gm": 9.0},     # bubbles
        "deaths_per_10min":           {"avg": 8.0,  "diamond": 6.0,  "gm": 4.0},
        "fight_survival_rate":        {"avg": 0.45, "diamond": 0.58, "gm": 0.72},
    },
    "zenyatta": {
        "ult_uses_per_10min":         {"avg": 1.5,  "diamond": 2.2,  "gm": 3.0},
        "ult_avg_hold_seconds":       {"avg": 30.0, "diamond": 20.0, "gm": 12.0},
        "deaths_per_10min":           {"avg": 5.0,  "diamond": 3.5,  "gm": 2.5},
        "fight_survival_rate":        {"avg": 0.50, "diamond": 0.65, "gm": 0.78},
    },
}


def benchmark_for(hero: str, stat: str, tier: str = "diamond") -> Optional[float]:
    """Returns the benchmark value for a hero+stat at a given tier, or None
    if unknown."""
    return HERO_BENCHMARKS.get(hero, {}).get(stat, {}).get(tier)


def ability_label(hero: str, slot_key: str) -> Optional[str]:
    """slot_key is one of slot1/slot2/slot3/ult. Returns the human-readable
    ability name for that hero+slot."""
    return HERO_ABILITY_LABELS.get(hero, {}).get(slot_key)
