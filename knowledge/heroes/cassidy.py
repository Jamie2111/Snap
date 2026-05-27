"""Cassidy: anti-dive hitscan, magnetic grenade burst, Deadeye for stalling."""

HERO = {
    "role": "dps",
    "difficulty": "medium",
    "win_condition": "Anti-dive your backline with mag-grenade. Pick squishies with primary. Deadeye stalls or wipes.",
    "abilities": {
        "deadeye": {
            "optimal_use": [
                "Stall objective when team is dead.",
                "Combo with grav or shatter.",
                "Force enemy to break sightline.",
            ],
            "common_mistakes": [
                "Casting in open sightline (you get killed mid-channel).",
                "Hold ult too long.",
            ],
            "held_too_long_threshold": 35,
        },
        "magnetic_grenade": {
            "optimal_use": [
                "Stick on diver entering your backline.",
                "Combine with fan + roll for burst kill.",
                "Stick on Pharah/Echo to deny aerial.",
            ],
            "common_mistakes": [
                "Throwing into shields.",
                "Wasted on full HP tanks.",
                "Missing because target moved (lead it).",
            ],
        },
        "combat_roll": {
            "optimal_use": [
                "Reload while moving.",
                "Escape dive.",
                "Combo with grenade for burst.",
            ],
            "common_mistakes": [
                "Rolling into enemy team.",
                "Burning roll out of fight.",
            ],
        },
        "flashbang": {
            "optimal_use": [
                "Stop diver attempting to dunk you.",
                "Cancel enemy ult cast.",
                "Set up fan kill.",
            ],
            "common_mistakes": [
                "Wasting on no threat.",
                "Forgetting to use on diver.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Mid range. Need primary fire to land.",
            "Stay near supports to peel.",
            "Use cover to bait dive into mag-grenade range.",
        ],
        "common_positioning_mistakes": [
            "Long sightlines (you're not a sniper).",
            "Standing static when Genji climbs angle.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Enemy diver attempting to engage.",
            "Mag-grenade up and target visible.",
        ],
        "when_not_to_fight": [
            "Diver healthy with all cooldowns.",
            "Anti-naded.",
        ],
    },
}

MATCHUPS = {
    "tracer": {"difficulty": "easy", "key_threat": "Pulse bomb if she gets close.",
               "advice": ["Mag-grenade on engage.", "Fan when she's stuck."]},
    "genji": {"difficulty": "medium", "key_threat": "Deflect returns mag.",
              "advice": ["Don't mag-grenade deflect.", "Fan + flashbang Genji."]},
    "pharah": {"difficulty": "medium", "key_threat": "Aerial out-poke.",
               "advice": ["Mag-grenade Pharah when she's airborne.", "Reposition for clearer shot."]},
    "widowmaker": {"difficulty": "hard", "key_threat": "Out-snipes.",
                   "advice": ["Take Off-angles.", "Bait Widow scope to reposition."]},
    "winston": {"difficulty": "medium", "key_threat": "Dives your backline.",
                "advice": ["Mag-grenade + fan combo on Winston bubble.", "Roll out of bubble."]},
    "reinhardt": {"difficulty": "easy", "key_threat": "Shield denies.",
                  "advice": ["Mag-grenade around shield.", "Fan Rein post-pin."]},
}

SYNERGIES = {
    "mercy": {"rating": "A", "win_condition": "Boosted fan-the-hammer burst kills.",
              "coordination": ["Damage boost on fan.", "GA off Cassidy."]},
    "ana": {"rating": "A", "win_condition": "Anti + mag-grenade confirms kill.",
            "coordination": ["Anti the mag target.", "Sleep diver Cass mags."]},
    "kiriko": {"rating": "A", "win_condition": "Suzu the anti-dive setup.",
               "coordination": ["Suzu Cass during deadeye.", "Kunai chain on Cass picks."]},
    "brigitte": {"rating": "S", "win_condition": "Anti-dive duo.",
                 "coordination": ["Brig peels diver, Cass executes.", "Whip combo with mag."]},
}
