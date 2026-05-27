"""Baptiste: sustained healer with burst damage, Immortality denies kills, Amp Matrix doubles team damage."""

HERO = {
    "role": "support",
    "difficulty": "high",
    "win_condition": "Sustained team healing with Regen. Immortality denies key burst kills. Amp Matrix wins ult fights.",
    "abilities": {
        "amplification_matrix": {
            "optimal_use": [
                "Combo with team ults (Visor, Bastion config, Pharah Barrage).",
                "Burst tank under coordinated focus.",
                "Force enemy off objective.",
            ],
            "common_mistakes": [
                "Amp matrix without team damage source.",
                "Placed where enemy can shoot you instead.",
            ],
            "held_too_long_threshold": 35,
        },
        "immortality_field": {
            "optimal_use": [
                "Tank below 30 percent under burst.",
                "Counter enemy ult (Blade, Pulse, Dragonstrike).",
                "Save key DPS in flank duel.",
            ],
            "common_mistakes": [
                "Immortality too early before commit.",
                "Placed in spot easy to destroy.",
            ],
        },
        "regenerative_burst": {
            "optimal_use": [
                "Burst heal grouped team.",
                "Self-heal when dove.",
                "Heal between fights.",
            ],
            "common_mistakes": [
                "Wasted out of fight.",
                "Forgetting cooldown.",
            ],
        },
        "exo_boots": {
            "optimal_use": [
                "Reach high ground angle.",
                "Reposition to safer cover.",
                "Escape diver.",
            ],
            "common_mistakes": [
                "Jumping into enemy sightlines.",
                "Not using vertical advantage.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "High ground with sightlines.",
            "Stay within Immortality range of team.",
            "Cover near you for diver escapes.",
        ],
        "common_positioning_mistakes": [
            "Static angle vs Widow.",
            "Open ground when dove.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Amp matrix ready and team has damage.",
            "Immortality up for safety net.",
        ],
        "when_not_to_fight": [
            "Immortality and matrix both on cooldown.",
            "Dive comp targeting you.",
        ],
    },
}

MATCHUPS = {
    "widowmaker": {"difficulty": "very_hard", "key_threat": "Picks before Immortality.",
                   "advice": ["Take angle behind cover.", "Don't peek static."]},
    "tracer": {"difficulty": "hard", "key_threat": "Closes range.",
               "advice": ["Immortality Tracer pulse.", "Exo boots out of pulse range."]},
    "sombra": {"difficulty": "hard", "key_threat": "Hack disables Immortality.",
               "advice": ["Stay near walls.", "Pre-Immortality on hack incoming."]},
    "ana": {"difficulty": "medium", "key_threat": "Anti melts your team.",
            "advice": ["Immortality on anti-nade.", "Sleep dart denies your peek."]},
    "winston": {"difficulty": "medium", "key_threat": "Bubble dives backline.",
                "advice": ["Immortality on Winston commit.", "Exo boots to high ground."]},
    "reinhardt": {"difficulty": "easy", "key_threat": "Shatter wipes grouped.",
                  "advice": ["Immortality on shatter cast.", "Amp matrix the shatter follow-up."]},
}

SYNERGIES = {
    "ashe": {"rating": "S", "win_condition": "Amp matrix B.O.B. = team wipe.",
             "coordination": ["Amp matrix on B.O.B. cast.", "Immortality during Ashe scope."]},
    "bastion": {"rating": "S", "win_condition": "Amp matrix Bastion config doubles damage.",
                "coordination": ["Amp matrix Bastion ult.", "Immortality during config."]},
    "sojourn": {"rating": "S", "win_condition": "Amp matrix Overclock.",
                "coordination": ["Amp matrix Overclock.", "Immortality on Sojourn dive."]},
    "ana": {"rating": "A", "win_condition": "Double support sustain.",
            "coordination": ["Immortality the anti-nade target.", "Amp matrix on Ana nano."]},
}
