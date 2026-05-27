"""Juno: mobile support, Hyper Ring speeds team, Orbital Ray sustained heal/damage."""

HERO = {
    "role": "support",
    "difficulty": "medium",
    "win_condition": "Mobile healing via Pulsar Torpedoes and Hyper Ring. Orbital Ray amplifies team damage and healing.",
    "abilities": {
        "orbital_ray": {
            "optimal_use": [
                "On grouped team during commit.",
                "Combo with team burst ults.",
                "Heal sustained brawl.",
            ],
            "common_mistakes": [
                "Cast on spread team.",
                "Cast out of fight.",
            ],
            "held_too_long_threshold": 35,
        },
        "pulsar_torpedoes": {
            "optimal_use": [
                "Burst heal multiple teammates.",
                "Combine with damage focus.",
                "Save teammates under burst.",
            ],
            "common_mistakes": [
                "Wasted on full HP team.",
                "Locking on out of LoS.",
            ],
        },
        "hyper_ring": {
            "optimal_use": [
                "Speed team through choke.",
                "Engage with brawl team.",
                "Reposition fast.",
            ],
            "common_mistakes": [
                "Ring placed where team isn't.",
                "Forgetting to use.",
            ],
        },
        "glide_boost": {
            "optimal_use": [
                "Reach high ground.",
                "Escape diver.",
                "Reposition between fights.",
            ],
            "common_mistakes": [
                "Boosting into sightlines.",
                "Burning boost.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Aerial angles for LoS to team.",
            "Stay mobile, use glide.",
            "Cover for escape.",
        ],
        "common_positioning_mistakes": [
            "Static angle.",
            "Open air without cover.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Ring up and team committed.",
            "Torpedoes ready and team needs burst heal.",
        ],
        "when_not_to_fight": [
            "Dive on you with no peel.",
            "Anti-naded.",
        ],
    },
}

MATCHUPS = {
    "tracer": {"difficulty": "hard", "key_threat": "Picks you fast.",
               "advice": ["Glide boost to escape.", "Torpedoes on engage."]},
    "widowmaker": {"difficulty": "hard", "key_threat": "Snipes you in air.",
                   "advice": ["Take cover angles.", "Don't fly static."]},
    "sombra": {"difficulty": "hard", "key_threat": "Hack disables glide.",
               "advice": ["Stay near walls.", "Torpedoes Sombra on hack."]},
    "winston": {"difficulty": "medium", "key_threat": "Dives air control.",
                "advice": ["Glide out of bubble.", "Torpedoes Winston commit."]},
    "ana": {"difficulty": "medium", "key_threat": "Anti melts.",
            "advice": ["Torpedoes on anti.", "Glide out of LoS."]},
    "reinhardt": {"difficulty": "easy", "key_threat": "Shatter on grouped.",
                  "advice": ["Speed team out of shatter.", "Heal during recovery."]},
}

SYNERGIES = {
    "reinhardt": {"rating": "A", "win_condition": "Speed brawl with Hyper Ring.",
                  "coordination": ["Ring on shatter cast.", "Heal Rein under focus."]},
    "junkerqueen": {"rating": "A", "win_condition": "Anti-heal brawl with speed.",
                    "coordination": ["Ring on JQ engage.", "Heal during Carnage."]},
    "winston": {"rating": "A", "win_condition": "Dive duo with speed and burst heal.",
                "coordination": ["Ring on Winston commit.", "Torpedoes during dive."]},
    "ana": {"rating": "A", "win_condition": "Double support with mobility.",
            "coordination": ["Torpedoes the anti target.", "Glide to peel for Ana."]},
}
