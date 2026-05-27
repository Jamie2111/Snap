"""Freja: agile DPS, crossbow burst with explosive bolts, mobile via Take Aim."""

HERO = {
    "role": "dps",
    "difficulty": "medium",
    "win_condition": "Mobile burst kills with explosive bolt. Take Aim windows confirm picks. Aerodynamic Strike zones an area.",
    "abilities": {
        "aerodynamic_strike": {
            "optimal_use": [
                "On grouped enemies.",
                "Force enemy off objective.",
                "Combo with team CC.",
            ],
            "common_mistakes": [
                "Ult open ground.",
                "Solo ult.",
            ],
            "held_too_long_threshold": 40,
        },
        "take_aim": {
            "optimal_use": [
                "Charged shot on key target.",
                "Reposition between shots.",
                "Burst tank.",
            ],
            "common_mistakes": [
                "Burning charge with no shot.",
                "Holding charge too long.",
            ],
        },
        "quick_dash": {
            "optimal_use": [
                "Escape diver.",
                "Reach off-angle.",
                "Reposition.",
            ],
            "common_mistakes": [
                "Dash into enemy team.",
                "Burning dash escape.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Mid range with mobility.",
            "Off-angles for charged shots.",
            "Stay agile, don't anchor.",
        ],
        "common_positioning_mistakes": [
            "Front line as Freja.",
            "Static angle.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Take Aim charged with target.",
            "Team commits with you.",
        ],
        "when_not_to_fight": [
            "Dash on cooldown.",
            "Anti-naded.",
        ],
    },
}

MATCHUPS = {
    "tracer": {"difficulty": "medium", "key_threat": "Closes range.",
               "advice": ["Dash out of pulse range.", "Charged shot on commit."]},
    "widowmaker": {"difficulty": "hard", "key_threat": "Out-snipes long range.",
                   "advice": ["Take off-angles.", "Dash erratically."]},
    "sombra": {"difficulty": "hard", "key_threat": "Hack disables dash.",
               "advice": ["Stay near walls.", "Charged shot Sombra on hack."]},
    "ana": {"difficulty": "medium", "key_threat": "Anti + sleep.",
            "advice": ["Dash on sleep.", "Charged shot Ana from blind angle."]},
    "winston": {"difficulty": "medium", "key_threat": "Beam at melee.",
                "advice": ["Dash out of bubble.", "Burst Winston pre-leap."]},
    "reinhardt": {"difficulty": "easy", "key_threat": "Shield denies.",
                  "advice": ["Charged shot around shield.", "Dash flank angle."]},
}

SYNERGIES = {
    "ana": {"rating": "A", "win_condition": "Anti + Freja burst.",
            "coordination": ["Anti the charged shot target.", "Nano Freja for burst sustained."]},
    "lucio": {"rating": "B", "win_condition": "Speed positioning.",
              "coordination": ["Speed amp to off-angle.", "Sound barrier commit."]},
    "kiriko": {"rating": "A", "win_condition": "Suzu cleanses anti, kunai chains burst.",
               "coordination": ["Suzu Freja anti.", "Kitsune the burst window."]},
    "zarya": {"rating": "A", "win_condition": "Grav + Freja Aerodynamic wipes.",
              "coordination": ["Grav before ult.", "Bubble Freja on commit."]},
}
