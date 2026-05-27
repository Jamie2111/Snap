"""Mauga: brawl tank, Cage Fight isolates a duel, Overrun closes distance."""

HERO = {
    "role": "tank",
    "difficulty": "medium",
    "win_condition": "Apply ignite, then chain crit damage with second chaingun. Cage Fight isolates a tank or key DPS for a forced 1v1.",
    "abilities": {
        "cage_fight": {
            "optimal_use": [
                "Trap enemy tank or key DPS alone.",
                "Combo with anti-nade for guaranteed kill.",
                "Deny escape ults (Recall, Fade).",
            ],
            "common_mistakes": [
                "Caging enemies with their support inside.",
                "Caging without anti or burst support.",
            ],
            "held_too_long_threshold": 40,
        },
        "overrun": {
            "optimal_use": [
                "Close distance to apply ignite.",
                "Disengage when at low HP.",
                "Knock enemies into your team.",
            ],
            "common_mistakes": [
                "Charging past your team.",
                "Wasting on single non-threat enemies.",
            ],
        },
        "cardiac_overdrive": {
            "optimal_use": [
                "Survive burst damage windows.",
                "Sustain through ignite stacks.",
                "Trade with enemy tank in extended fight.",
            ],
            "common_mistakes": [
                "Using before damage commit.",
                "Holding to fight over.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Front line, close range.",
            "Always cycle ignite onto next threat.",
            "Stay near supports for sustain through Cardiac.",
        ],
        "common_positioning_mistakes": [
            "Caging away from team support.",
            "Overrun into a lost fight.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Anti-nade available, cage on cooldown.",
            "Enemy tank isolated.",
        ],
        "when_not_to_fight": [
            "Mauga vs Mauga without anti.",
            "Enemy has Sombra hunting your cage.",
        ],
    },
}

MATCHUPS = {
    "ana": {"difficulty": "very_hard", "key_threat": "Anti melts your sustain.",
            "advice": ["Cardiac on anti.", "Sleep dart cancels your Cage. Engage after sleep is used."]},
    "junkerqueen": {"difficulty": "medium", "key_threat": "Anti-heal denies Cardiac.",
                    "advice": ["Cage JQ in 1v1.", "Don't fight under Carnage stacks."]},
    "reinhardt": {"difficulty": "medium", "key_threat": "Pin disrupts cage.",
                  "advice": ["Cage Rein when he's used pin.", "Stay outside hammer range."]},
    "zarya": {"difficulty": "hard", "key_threat": "Bubble denies ignite damage.",
              "advice": ["Don't shoot bubble.", "Cage Zarya away from her team."]},
    "sombra": {"difficulty": "hard", "key_threat": "Hack stops Cage and Cardiac.",
               "advice": ["Pre-Cardiac before hack.", "Stay near walls."]},
    "winston": {"difficulty": "easy", "key_threat": "Bubble blocks ignite.",
                "advice": ["Wait for bubble to drop.", "Cage Winston alone."]},
}

SYNERGIES = {
    "ana": {"rating": "S", "win_condition": "Anti Cage = guaranteed tank kill.",
            "coordination": ["Anti the caged target.", "Nano Mauga for ignite sustained."]},
    "kiriko": {"rating": "A", "win_condition": "Suzu the anti, Kitsune the Cage push.",
               "coordination": ["Suzu Mauga's anti.", "Kitsune Cage Fight."]},
    "lucio": {"rating": "B", "win_condition": "Speed engage into Cage.",
              "coordination": ["Speed amp.", "Sound barrier Cage burst."]},
    "baptiste": {"rating": "A", "win_condition": "Immortality during Cage burst window.",
                 "coordination": ["Bap window inside Cage.", "Amp matrix the chaingun."]},
}
