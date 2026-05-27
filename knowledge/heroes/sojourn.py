"""Sojourn: hitscan + railgun, mobility via slide, Overclock ult auto-charges railgun."""

HERO = {
    "role": "dps",
    "difficulty": "high",
    "win_condition": "Build railgun charge with primary, then secure picks with charged shots. Overclock chains kills.",
    "abilities": {
        "overclock": {
            "optimal_use": [
                "On grouped enemies with sightline.",
                "Combo with grav or shatter.",
                "Mid-fight when team pushes.",
            ],
            "common_mistakes": [
                "Overclock without sightline.",
                "Hold ult past optimal moment.",
            ],
            "held_too_long_threshold": 35,
        },
        "power_slide": {
            "optimal_use": [
                "Escape diver.",
                "Reach high ground angle.",
                "Reposition between shots.",
            ],
            "common_mistakes": [
                "Slide into enemy team.",
                "Burning slide without need.",
            ],
        },
        "disruptor_shot": {
            "optimal_use": [
                "Slow enemy push through choke.",
                "Damage cluster of enemies.",
                "Deny escape route.",
            ],
            "common_mistakes": [
                "Throwing in open ground.",
                "Wasted on solo target.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Mid range with sightline.",
            "Slide to refresh angles.",
            "Charge rail safely before commit.",
        ],
        "common_positioning_mistakes": [
            "Sliding into enemy line.",
            "Holding charged rail too long without firing.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Rail charged and target visible.",
            "Overclock up and team pushes.",
        ],
        "when_not_to_fight": [
            "Sombra hunting.",
            "Diver healthy on enemy team.",
        ],
    },
}

MATCHUPS = {
    "tracer": {"difficulty": "hard", "key_threat": "Closes range fast.",
               "advice": ["Slide away from Tracer engage.", "Don't duel without peel."]},
    "genji": {"difficulty": "hard", "key_threat": "Deflect returns rail.",
              "advice": ["Don't shoot Genji deflect with rail.", "Primary fire him."]},
    "sombra": {"difficulty": "hard", "key_threat": "Hack disables slide.",
               "advice": ["Stay near walls.", "Pre-slide if Sombra suspected."]},
    "winston": {"difficulty": "medium", "key_threat": "Dives you.",
                "advice": ["Slide out of bubble.", "Rail Winston before commit."]},
    "widowmaker": {"difficulty": "medium", "key_threat": "Out-snipes long range.",
                   "advice": ["Take off angles.", "Disruptor shot her angle."]},
    "reinhardt": {"difficulty": "easy", "key_threat": "Shield denies.",
                  "advice": ["Rail over/around shield.", "Disruptor shot behind shield."]},
}

SYNERGIES = {
    "mercy": {"rating": "S", "win_condition": "Boosted rail one-shots tanks below 50 percent.",
              "coordination": ["Damage boost on charged rail.", "GA off Sojourn."]},
    "ana": {"rating": "A", "win_condition": "Anti + rail confirms kills.",
            "coordination": ["Anti before Overclock.", "Nano Sojourn for sustained rail."]},
    "winston": {"rating": "A", "win_condition": "Dive duo with rail confirmation.",
                "coordination": ["Winston commits, Sojourn rails.", "Bubble Sojourn sightline."]},
    "baptiste": {"rating": "A", "win_condition": "Amp matrix doubles rail damage.",
                 "coordination": ["Amp matrix Overclock.", "Immortality through dive."]},
}
