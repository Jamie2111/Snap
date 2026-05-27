"""Echo: aerial flex DPS, sticky bombs + beam, Duplicate copies enemy ults."""

HERO = {
    "role": "dps",
    "difficulty": "high",
    "win_condition": "Burst combo (stick + beam) finishes squishies. Duplicate copies key enemy ults.",
    "abilities": {
        "duplicate": {
            "optimal_use": [
                "Duplicate enemy tank for second ult use.",
                "Counter dive ulting their support.",
                "Force re-engage when team is dead.",
            ],
            "common_mistakes": [
                "Duplicating low-value targets.",
                "Forgetting to use stolen ult.",
            ],
            "held_too_long_threshold": 35,
        },
        "sticky_bombs": {
            "optimal_use": [
                "Combo with beam for kill.",
                "Cluster damage on grouped enemies.",
                "Tank chip damage.",
            ],
            "common_mistakes": [
                "Sticking shielded targets.",
                "Wasted on full HP tanks.",
            ],
        },
        "focusing_beam": {
            "optimal_use": [
                "Finish low HP target (<50 percent).",
                "Burst tank low.",
                "Cancel enemy ult cast.",
            ],
            "common_mistakes": [
                "Beam full HP target.",
                "Beam exposed to multiple angles.",
            ],
        },
        "flight": {
            "optimal_use": [
                "Reach aerial angles.",
                "Escape diver.",
                "Engage from above.",
            ],
            "common_mistakes": [
                "Flying into hitscan focus.",
                "Burning flight escape.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Aerial angles enemies can't easily track.",
            "Stay flying as much as possible.",
            "Land only for cover.",
        ],
        "common_positioning_mistakes": [
            "Grounded in fight.",
            "Flying low into hitscan.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Aerial advantage uncontested.",
            "Duplicate target available.",
        ],
        "when_not_to_fight": [
            "Hitscan healthy.",
            "Sombra hunting.",
        ],
    },
}

MATCHUPS = {
    "soldier76": {"difficulty": "hard", "key_threat": "Hitscan tracks aerial.",
                  "advice": ["Stay high.", "Burst Soldier when his field down."]},
    "ashe": {"difficulty": "hard", "key_threat": "Scoped tracks aerial.",
             "advice": ["Take angles she can't scope.", "Duplicate Ashe ult."]},
    "sombra": {"difficulty": "very_hard", "key_threat": "Hack ends flight.",
               "advice": ["Stay near walls.", "Duplicate Sombra for EMP."]},
    "winston": {"difficulty": "medium", "key_threat": "Bubble dives backline.",
                "advice": ["Stay above Winston jump.", "Beam Winston post-bubble."]},
    "pharah": {"difficulty": "easy", "key_threat": "Aerial duelist.",
               "advice": ["Burst Pharah airborne.", "Duplicate Pharah for double Barrage."]},
    "reinhardt": {"difficulty": "easy", "key_threat": "Shield denies.",
                  "advice": ["Stick over shield.", "Duplicate Rein for double shatter."]},
}

SYNERGIES = {
    "mercy": {"rating": "S", "win_condition": "Pharmercy-style aerial control.",
              "coordination": ["GA chain off Echo.", "Boost beam."]},
    "ana": {"rating": "A", "win_condition": "Nano Duplicate for sustained power.",
            "coordination": ["Nano duplicated ult.", "Anti beam target."]},
    "winston": {"rating": "A", "win_condition": "Dive duo with aerial pressure.",
                "coordination": ["Winston bubbles, Echo bursts.", "Stick + beam Winston's target."]},
    "kiriko": {"rating": "A", "win_condition": "Suzu enables aggressive Duplicate.",
               "coordination": ["Suzu Echo on commit.", "Kunai chain on Echo picks."]},
}
