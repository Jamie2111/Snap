"""Illari: sniper support, rifle picks at range, Healing Pylon for autonomous heal."""

HERO = {
    "role": "support",
    "difficulty": "medium",
    "win_condition": "Pick at long range with rifle. Pylon heals team while you damage. Captive Sun zones grouped enemies.",
    "abilities": {
        "captive_sun": {
            "optimal_use": [
                "On grouped enemies stunning them.",
                "Combo with team CC ults.",
                "Force enemy off objective.",
            ],
            "common_mistakes": [
                "Sun open ground enemies dodge.",
                "Solo ult.",
            ],
            "held_too_long_threshold": 40,
        },
        "healing_pylon": {
            "optimal_use": [
                "Placed behind cover near team.",
                "Cover support that's out of position.",
                "Heal sustained during siege.",
            ],
            "common_mistakes": [
                "Pylon placed in enemy sightline.",
                "Forgetting to replace destroyed pylon.",
            ],
        },
        "outburst": {
            "optimal_use": [
                "Reach high ground.",
                "Escape diver.",
                "Boop enemy off ledge.",
            ],
            "common_mistakes": [
                "Burning out of fight.",
                "Boosting into enemy line.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Long sightlines for rifle.",
            "Stay near Pylon for autonomous heal.",
            "High ground angles.",
        ],
        "common_positioning_mistakes": [
            "Front line with sniper rifle.",
            "Pylon placed bad.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Pylon up and rifle charged.",
            "Sun ready for zone control.",
        ],
        "when_not_to_fight": [
            "Pylon down and dove.",
            "Anti-naded.",
        ],
    },
}

MATCHUPS = {
    "tracer": {"difficulty": "hard", "key_threat": "Picks you.",
               "advice": ["Outburst out of pulse range.", "Pylon for sustain."]},
    "widowmaker": {"difficulty": "hard", "key_threat": "Out-snipes.",
                   "advice": ["Take off angles.", "Pylon out of her LoS."]},
    "sombra": {"difficulty": "very_hard", "key_threat": "Hack disables outburst.",
               "advice": ["Stay near walls.", "Pre-Outburst on hack."]},
    "ana": {"difficulty": "medium", "key_threat": "Anti + sleep.",
            "advice": ["Outburst on anti.", "Rifle Ana at long range."]},
    "winston": {"difficulty": "medium", "key_threat": "Beam at melee.",
                "advice": ["Outburst out of bubble.", "Pylon for sustain."]},
    "reinhardt": {"difficulty": "easy", "key_threat": "Shatter on grouped.",
                  "advice": ["Sun on shatter follow-up.", "Pylon during recovery."]},
}

SYNERGIES = {
    "ana": {"rating": "A", "win_condition": "Long-range duo with sustain.",
            "coordination": ["Sun the Anti target.", "Both pick from range."]},
    "reinhardt": {"rating": "A", "win_condition": "Sun on shatter cluster.",
                  "coordination": ["Sun shatter follow-up.", "Pylon Rein under focus."]},
    "winston": {"rating": "B", "win_condition": "Dive backup with rifle picks.",
                "coordination": ["Rifle Winston's dive target.", "Pylon Winston dive escape."]},
    "kiriko": {"rating": "A", "win_condition": "Suzu cleanses anti, dual peel.",
               "coordination": ["Suzu Illari anti.", "Kunai chain on Illari picks."]},
}
