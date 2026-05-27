"""Kiriko: cleanse with suzu, kunai picks, TP peel anywhere."""

HERO = {
    "role": "support",
    "difficulty": "high",
    "win_condition": "Cleanse key debuffs, suzu the enemy ult, kunai picks on low targets. Mobility lets you peel for anyone on demand.",
    "abilities": {
        "protection_suzu": {
            "optimal_use": [
                "Cancel anti-nade on your tank or yourself.",
                "Negate the damage of an enemy ult (Dragonblade, Pulse Bomb, etc.).",
                "Cleanse hack or sleep on a key target.",
            ],
            "common_mistakes": [
                "Suzu used too early. Wait for the threat to commit.",
                "Suzu on a player who is going to die anyway.",
                "Saving suzu and watching your tank die.",
            ],
            "timing_threshold_seconds": 10,
            "held_too_long_threshold": 20,
        },
        "kitsune_rush": {
            "optimal_use": [
                "On a coordinated push through choke.",
                "Combined with team ults (Nano, Visor, etc.).",
            ],
            "common_mistakes": [
                "Used solo with no team commitment.",
                "Used when team is already winning the fight and doesn't need it.",
            ],
            "held_too_long_threshold": 40,
        },
        "swift_step": {
            "optimal_use": [
                "Reposition to peel for a diver.",
                "Escape a flank ambush.",
            ],
            "common_mistakes": [
                "Teleporting into a lost fight.",
                "Teleporting to a teammate who is about to die.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "You're mobile but fragile. Take high-ground angles for kunai and TP back to safety.",
            "Stay near a teammate you can TP to as escape.",
            "Don't be the front line. Your damage comes from off-angles.",
        ],
        "common_positioning_mistakes": [
            "Pushing kunai duels in the open against tracer/genji.",
            "Standing next to your other support so both die to one dive.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Tank engaged and suzu is up.",
            "Enemy support is alone and kunai range.",
        ],
        "when_not_to_fight": [
            "Suzu and TP both on cooldown. You have no escape.",
            "Enemy hitscan has angle on your TP spot.",
        ],
    },
}

MATCHUPS = {
    "winston": {"difficulty": "hard", "key_threat": "Bubble + leap removes your escape options.",
                "advice": ["Save suzu for the moment Winston ults or anti-nades you.", "TP to a teammate before Winston lands."]},
    "tracer": {"difficulty": "hard", "key_threat": "Pulse bomb negates Kiriko sustain.",
               "advice": ["Suzu yourself or teammate on pulse-bomb stick.", "TP to escape if pulse hits a teammate near you."]},
    "sombra": {"difficulty": "hard", "key_threat": "Hack removes TP and suzu.",
               "advice": ["Pre-suzu yourself before hack lands if you see her commit.", "Position near walls she can't LoS through."]},
    "ana": {"difficulty": "easy", "key_threat": "Anti-nade still threatens your team.",
            "advice": ["Suzu the anti-nade. Highest-leverage suzu in most matchups."]},
    "reinhardt": {"difficulty": "easy", "key_threat": "Shatter wipes a grouped team.",
                  "advice": ["Suzu the shatter for a free team-save."]},
    "moira": {"difficulty": "medium", "key_threat": "Coalescence pierces suzu duration.",
              "advice": ["TP out of coalescence range. Don't try to out-heal it."]},
}

SYNERGIES = {
    "winston": {"rating": "S", "win_condition": "Dive comp with cleanse on tank.",
                "coordination": ["TP to Winston when he commits.", "Suzu Winston anti."]},
    "reinhardt": {"rating": "S", "win_condition": "Suzu cleanses anti, Kitsune amplifies shatter pushes.",
                  "coordination": ["Suzu shatter cast.", "Kitsune the push through choke."]},
    "tracer": {"rating": "A", "win_condition": "Suzu on Tracer pulse anti is huge.",
               "coordination": ["TP to Tracer when she's low.", "Suzu when she's anti-naded."]},
    "ana": {"rating": "A", "win_condition": "Twin support that covers anti-cleanse and sleep peel.",
            "coordination": ["Suzu Ana sleep on key targets.", "TP rotate to peel for Ana under dive."]},
}
