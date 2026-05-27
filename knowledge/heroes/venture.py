"""Venture: melee dive DPS, burrow for repositioning and damage."""

HERO = {
    "role": "dps",
    "difficulty": "medium",
    "win_condition": "Burrow to engage, drill primary at close range, escape via second burrow. Tectonic Shock for grouped damage.",
    "abilities": {
        "tectonic_shock": {
            "optimal_use": [
                "On grouped enemies low HP.",
                "Combo with team CC ults.",
                "Push enemy off objective.",
            ],
            "common_mistakes": [
                "Ult cast in open ground enemies escape.",
                "Solo ult without team.",
            ],
            "held_too_long_threshold": 40,
        },
        "burrow": {
            "optimal_use": [
                "Engage from underground.",
                "Bypass enemy ult.",
                "Escape low HP.",
            ],
            "common_mistakes": [
                "Burrow into enemy team alone.",
                "Forgetting burrow as escape.",
            ],
        },
        "drill_dash": {
            "optimal_use": [
                "Closing distance.",
                "Confirm kill on low HP.",
                "Reposition after pick.",
            ],
            "common_mistakes": [
                "Dash into entire enemy team.",
                "Wasted on no value.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Close range. Burrow for repositioning.",
            "Engage flanks with burrow.",
            "Escape angle planned before commit.",
        ],
        "common_positioning_mistakes": [
            "Engaging without burrow ready.",
            "Long range as Venture.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Burrow ready and isolated support nearby.",
            "Team commits with you.",
        ],
        "when_not_to_fight": [
            "Burrow on cooldown.",
            "Brig peeling backline.",
        ],
    },
}

MATCHUPS = {
    "brigitte": {"difficulty": "very_hard", "key_threat": "Stun + whip denies engage.",
                 "advice": ["Engage non-Brig support.", "Bait stun, then dash."]},
    "ana": {"difficulty": "medium", "key_threat": "Sleep + anti.",
            "advice": ["Burrow on anti-nade.", "Dash post-sleep."]},
    "tracer": {"difficulty": "medium", "key_threat": "Picks you.",
               "advice": ["Drill burst Tracer.", "Burrow when low."]},
    "sombra": {"difficulty": "hard", "key_threat": "Hack disables dash.",
               "advice": ["Burrow pre-hack.", "Stay near walls."]},
    "reinhardt": {"difficulty": "easy", "key_threat": "Pin denies.",
                  "advice": ["Dash past shield.", "Burrow under pin."]},
    "winston": {"difficulty": "medium", "key_threat": "Beam at melee.",
                "advice": ["Burrow out of bubble.", "Dash Winston post-leap."]},
}

SYNERGIES = {
    "ana": {"rating": "A", "win_condition": "Anti + Venture burst.",
            "coordination": ["Anti the dash target.", "Sleep diver Venture commits to."]},
    "kiriko": {"rating": "A", "win_condition": "Suzu cleanses sleep, TP repositions.",
               "coordination": ["Suzu Venture on engage.", "TP Venture out of bad commit."]},
    "lucio": {"rating": "B", "win_condition": "Speed dive entry.",
              "coordination": ["Speed amp on burrow.", "Sound barrier dash."]},
    "winston": {"rating": "A", "win_condition": "Dive duo with disruption.",
                "coordination": ["Bubble Venture mid-dash.", "Engage same target."]},
}
