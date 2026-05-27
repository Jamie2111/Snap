"""Soldier 76: sustained hitscan, biotic field for sustain, Visor wipes."""

HERO = {
    "role": "dps",
    "difficulty": "medium",
    "win_condition": "Sustained DPS at mid range, Helix Rocket for burst confirmation, Visor wins ult fights.",
    "abilities": {
        "tactical_visor": {
            "optimal_use": [
                "On grouped enemies with sightline.",
                "Combo with grav, shatter, anti-nade.",
                "Mid-fight to swing momentum.",
            ],
            "common_mistakes": [
                "Visor with no sightline.",
                "Burning ult on single target.",
            ],
            "held_too_long_threshold": 35,
        },
        "helix_rockets": {
            "optimal_use": [
                "Burst confirmation on low HP target.",
                "Damage stack on tanks.",
                "Self-defense against diver.",
            ],
            "common_mistakes": [
                "Wasted on full HP tanks alone.",
                "Not using on cooldown.",
            ],
        },
        "biotic_field": {
            "optimal_use": [
                "Sustain through brawl.",
                "Heal teammates near you.",
                "Survive burst window.",
            ],
            "common_mistakes": [
                "Placing in spot enemy can deny.",
                "Forgetting to use when low.",
            ],
        },
        "sprint": {
            "optimal_use": [
                "Reposition to angle.",
                "Reach objective fast.",
                "Escape diver.",
            ],
            "common_mistakes": [
                "Sprinting through enemy sightlines.",
                "Sprinting AT enemy team.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Mid range with cover steps.",
            "Stay near biotic field.",
            "Sprint to flank angles, then hold.",
        ],
        "common_positioning_mistakes": [
            "Sprinting into enemy team.",
            "Static angle with no field.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Field placed and helix ready.",
            "Team has pressure on enemy.",
        ],
        "when_not_to_fight": [
            "Field on cooldown and dove.",
            "Anti-naded.",
        ],
    },
}

MATCHUPS = {
    "tracer": {"difficulty": "medium", "key_threat": "Closes distance.",
               "advice": ["Helix on Tracer commit.", "Biotic field for sustain."]},
    "genji": {"difficulty": "medium", "key_threat": "Deflect returns helix.",
              "advice": ["Don't helix deflect.", "Primary fire Genji."]},
    "pharah": {"difficulty": "easy", "key_threat": "Aerial pressure.",
               "advice": ["Helix Pharah airborne.", "Primary tracks her arc."]},
    "widowmaker": {"difficulty": "hard", "key_threat": "Out-snipes long range.",
                   "advice": ["Take off-angles.", "Helix Widow scoped."]},
    "winston": {"difficulty": "medium", "key_threat": "Dives, beam shreds.",
                "advice": ["Helix Winston bubble.", "Sprint out of bubble."]},
    "reinhardt": {"difficulty": "easy", "key_threat": "Shield denies.",
                  "advice": ["Helix into shield breaks.", "Field behind shield."]},
}

SYNERGIES = {
    "mercy": {"rating": "S", "win_condition": "Pocketed Soldier outputs lethal damage.",
              "coordination": ["Damage boost during Visor.", "Stay near biotic field."]},
    "ana": {"rating": "A", "win_condition": "Nano Visor wipes teams.",
            "coordination": ["Anti grav cluster.", "Nano Visor."]},
    "lucio": {"rating": "A", "win_condition": "Speed engage with sustained fire.",
              "coordination": ["Speed amp on Visor.", "Sound barrier Visor."]},
    "zarya": {"rating": "A", "win_condition": "Grav + Visor wipes.",
              "coordination": ["Grav before Visor.", "Bubble Soldier on commit."]},
}
