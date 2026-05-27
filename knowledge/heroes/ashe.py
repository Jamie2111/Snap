"""Ashe: scoped hitscan, B.O.B. for instant pressure, dynamite for poke."""

HERO = {
    "role": "dps",
    "difficulty": "high",
    "win_condition": "Pick supports with scoped shots from long range. B.O.B. forces enemies to break formation.",
    "abilities": {
        "bob": {
            "optimal_use": [
                "On capture point during overtime.",
                "Combo with grav or anti-nade.",
                "Push enemy off objective.",
            ],
            "common_mistakes": [
                "B.O.B. into open ground enemies kite.",
                "Solo B.O.B. without team follow-up.",
            ],
            "held_too_long_threshold": 40,
        },
        "dynamite": {
            "optimal_use": [
                "Damage cluster of enemies.",
                "Set up scoped shot kill.",
                "Reveal enemy positions via burn.",
            ],
            "common_mistakes": [
                "Wasted on full HP tanks.",
                "Not shooting dynamite to detonate early.",
            ],
        },
        "coach_gun": {
            "optimal_use": [
                "Boop diver off your back.",
                "Reposition to high angle.",
                "Combo with dynamite for cluster damage.",
            ],
            "common_mistakes": [
                "Wasting on no threat.",
                "Coaching into enemy team.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Long sightlines. Stay scoped angle.",
            "Reposition after 2-3 shots.",
            "High ground only if you have escape.",
        ],
        "common_positioning_mistakes": [
            "Static angle gets sniped.",
            "Front line with no scoping room.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Enemy support in your sightline.",
            "B.O.B. up and team has follow-up.",
        ],
        "when_not_to_fight": [
            "Genji/Tracer alive and you have no peel.",
            "Pharah uncountered (you can't deal with aerial).",
        ],
    },
}

MATCHUPS = {
    "tracer": {"difficulty": "very_hard", "key_threat": "Closes distance fast.",
               "advice": ["Coach Gun on Tracer engage.", "Peel partner mandatory."]},
    "genji": {"difficulty": "hard", "key_threat": "Climbs to your angle.",
              "advice": ["Pre-place dynamite on his climb route.", "Coach Gun if he commits."]},
    "pharah": {"difficulty": "hard", "key_threat": "Aerial denies your scope.",
               "advice": ["Switch focus to Pharah if uncovered.", "Lead shots; she's predictable."]},
    "sombra": {"difficulty": "hard", "key_threat": "Hack disables Coach Gun.",
               "advice": ["Stay near walls.", "Don't scope when Sombra invisible nearby."]},
    "widowmaker": {"difficulty": "medium", "key_threat": "Out-snipes you on long range.",
                   "advice": ["Take off-angles she doesn't cover.", "B.O.B. to pressure her."]},
    "reinhardt": {"difficulty": "easy", "key_threat": "Shield denies your shots.",
                  "advice": ["Dynamite over shield.", "Reposition for off-angle scope."]},
}

SYNERGIES = {
    "mercy": {"rating": "S", "win_condition": "Pocketed scoped shots one-shot squishies.",
              "coordination": ["Damage boost on scope.", "GA off Ashe for repositioning."]},
    "ana": {"rating": "A", "win_condition": "Nano + B.O.B. and dynamite cluster wipes.",
            "coordination": ["Anti the B.O.B. cluster.", "Nano Ashe for sustained scope."]},
    "sigma": {"rating": "A", "win_condition": "Sigma covers Ashe sightline.",
              "coordination": ["Barrier her scope angle.", "Grav into B.O.B."]},
    "baptiste": {"rating": "A", "win_condition": "Bap window amp matrix Ashe damage.",
                 "coordination": ["Amp matrix on B.O.B. cast.", "Immortality during dynamite cluster."]},
}
