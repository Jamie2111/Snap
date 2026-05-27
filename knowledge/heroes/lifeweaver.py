"""Lifeweaver: utility support, Petal Platform for verticality, Life Grip pulls allies, Tree of Life for sustain."""

HERO = {
    "role": "support",
    "difficulty": "medium",
    "win_condition": "Utility above raw healing. Life Grip saves allies, Petal repositions, Tree heals sustained.",
    "abilities": {
        "tree_of_life": {
            "optimal_use": [
                "Stall objective during overtime.",
                "Counter enemy burst ult (RIP-Tire, Blade).",
                "Sustain team during siege.",
            ],
            "common_mistakes": [
                "Tree in open ground enemies shoot down.",
                "Tree before fight starts (wasted).",
            ],
            "held_too_long_threshold": 40,
        },
        "life_grip": {
            "optimal_use": [
                "Pull low ally out of focus fire.",
                "Counter Blade / pulse stick on teammate.",
                "Reposition support out of dive.",
            ],
            "common_mistakes": [
                "Pulling ally mid-engage (you save them but ruin their angle).",
                "Forgetting Grip when teammate is dying.",
            ],
        },
        "petal_platform": {
            "optimal_use": [
                "Reach high ground.",
                "Disrupt diver path.",
                "Save teammate from ground burst.",
            ],
            "common_mistakes": [
                "Petal in open ground.",
                "Not using to escape.",
            ],
        },
        "healing_blossom": {
            "optimal_use": [
                "Sustained heal on tank.",
                "Burst heal under pressure.",
                "Charge up while team is in cover.",
            ],
            "common_mistakes": [
                "Wasted on full HP allies.",
                "Charging too long during burst windows.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Behind team with sightline.",
            "Petal angles for vertical advantage.",
            "Stay near Grip range of key DPS.",
        ],
        "common_positioning_mistakes": [
            "Open ground without Petal.",
            "Out of range when DPS needs Grip.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Tree ready and team commits.",
            "Grip ready for peel.",
        ],
        "when_not_to_fight": [
            "Petal and Grip on cooldown.",
            "Sombra hunting.",
        ],
    },
}

MATCHUPS = {
    "tracer": {"difficulty": "hard", "key_threat": "Picks you fast.",
               "advice": ["Petal to high ground.", "Grip yourself or teammate on pulse."]},
    "genji": {"difficulty": "medium", "key_threat": "Blade burst.",
              "advice": ["Grip during Blade.", "Petal to escape dash."]},
    "sombra": {"difficulty": "very_hard", "key_threat": "Hack disables Grip and Petal.",
               "advice": ["Stay near walls.", "Pre-Petal before hack lands."]},
    "ana": {"difficulty": "easy", "key_threat": "Anti melts team.",
            "advice": ["Tree counters anti for 5 seconds.", "Grip Ana sleep target."]},
    "winston": {"difficulty": "medium", "key_threat": "Bubble dives.",
                "advice": ["Petal Winston jump.", "Grip support pulled by Winston."]},
    "reinhardt": {"difficulty": "easy", "key_threat": "Shatter wipes.",
                  "advice": ["Tree on shatter cast.", "Grip your DPS post-shatter."]},
}

SYNERGIES = {
    "reinhardt": {"rating": "A", "win_condition": "Tree on shatter push enables brawl.",
                  "coordination": ["Tree the shatter follow-up.", "Heal Rein post-shatter."]},
    "ana": {"rating": "B", "win_condition": "Anti + Tree sustains team through anti.",
            "coordination": ["Tree on anti-nade.", "Grip Ana sleep target."]},
    "tracer": {"rating": "A", "win_condition": "Grip Tracer out of pulse.",
               "coordination": ["Grip Tracer when caught.", "Petal Tracer high ground."]},
    "genji": {"rating": "A", "win_condition": "Grip Genji out of Blade danger.",
              "coordination": ["Grip Genji post-Blade.", "Petal Genji escape."]},
}
