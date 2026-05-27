"""Torbjorn: bunker/poke DPS, turret denies angles, Overload for personal burst."""

HERO = {
    "role": "dps",
    "difficulty": "low",
    "win_condition": "Turret denies enemy angles. Rivet gun picks squishies. Molten Core zones an objective.",
    "abilities": {
        "molten_core": {
            "optimal_use": [
                "On objective during overtime.",
                "Combo with grav, shatter.",
                "Force enemy off control point.",
            ],
            "common_mistakes": [
                "Lava with no team follow-up.",
                "Open area enemies kite.",
            ],
            "held_too_long_threshold": 40,
        },
        "deploy_turret": {
            "optimal_use": [
                "Cover flank route.",
                "Force enemy to break sightline.",
                "Charge with Overload for burst.",
            ],
            "common_mistakes": [
                "Turret in low-value spots.",
                "Not replacing destroyed turret.",
            ],
        },
        "overload": {
            "optimal_use": [
                "Engage a tank brawl.",
                "Self-defense against diver.",
                "Combo with primary burst.",
            ],
            "common_mistakes": [
                "Overload without need.",
                "Forgetting to use under burst.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Behind turret for area denial.",
            "Mid range with rivet gun.",
            "Cover for Overload duels.",
        ],
        "common_positioning_mistakes": [
            "Front line without Overload.",
            "Turret placed in low-value spots.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Turret placed and Overload up.",
            "Lava down with team push.",
        ],
        "when_not_to_fight": [
            "Diver focused on you with Overload down.",
            "Anti-naded.",
        ],
    },
}

MATCHUPS = {
    "pharah": {"difficulty": "very_hard", "key_threat": "Aerial out of rivet range.",
               "advice": ["Switch off Torb into Pharah.", "Turret her grounded angle."]},
    "widowmaker": {"difficulty": "hard", "key_threat": "Picks before Overload.",
                   "advice": ["Take cover.", "Turret her angle."]},
    "tracer": {"difficulty": "medium", "key_threat": "Closes range.",
               "advice": ["Turret your back.", "Overload + rivet burst."]},
    "winston": {"difficulty": "easy", "key_threat": "Beam at melee.",
                "advice": ["Overload to survive bubble.", "Turret Winston jump path."]},
    "reinhardt": {"difficulty": "easy", "key_threat": "Shield denies.",
                  "advice": ["Lava behind shield.", "Rivet over shield."]},
    "ana": {"difficulty": "medium", "key_threat": "Anti melts you.",
            "advice": ["Don't engage anti-naded.", "Overload through anti."]},
}

SYNERGIES = {
    "orisa": {"rating": "S", "win_condition": "Bunker with turret + Fortify.",
              "coordination": ["Turret on Orisa front.", "Lava during Surge."]},
    "baptiste": {"rating": "A", "win_condition": "Amp matrix doubles rivet damage.",
                 "coordination": ["Amp matrix Torb burst.", "Immortality on Overload."]},
    "mercy": {"rating": "A", "win_condition": "Pocketed Torb shreds.",
              "coordination": ["Damage boost Overload.", "Stay near turret."]},
    "ana": {"rating": "B", "win_condition": "Anti the lava cluster.",
            "coordination": ["Anti the lava target.", "Nano Torb on Overload."]},
}
