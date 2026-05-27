"""Roadhog: hook tank, burst kills isolated targets, Trap denies mobility."""

HERO = {
    "role": "tank",
    "difficulty": "low",
    "win_condition": "Hook + shotgun bursts squishies. Trap denies mobility on key duels. Whole Hog zones an objective.",
    "abilities": {
        "whole_hog": {
            "optimal_use": [
                "Push enemy team off objective.",
                "Combo with grav or shatter.",
                "Stall during overtime.",
            ],
            "common_mistakes": [
                "Pig ulting from low ground (enemies walk above).",
                "Burning ult with no team.",
            ],
            "held_too_long_threshold": 35,
        },
        "chain_hook": {
            "optimal_use": [
                "Pull isolated support into your team.",
                "Confirm kill on low HP enemy.",
                "Disrupt a channeled ult cast.",
            ],
            "common_mistakes": [
                "Hooking tanks (no kill secured).",
                "Missing or wasting hook cooldown.",
            ],
        },
        "take_a_breather": {
            "optimal_use": [
                "Sustain through ranged damage.",
                "Activate when out of LoS.",
                "Trade against anti-heal Ana.",
            ],
            "common_mistakes": [
                "Breather in open ground (enemies kill you mid-channel).",
                "Forgetting to use when low.",
            ],
        },
        "pig_pen": {
            "optimal_use": [
                "Trap a flank route.",
                "Deny a diver's escape angle.",
                "Hook + trap combo.",
            ],
            "common_mistakes": [
                "Trap thrown into open spam zones.",
                "Forgetting to refresh trap.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Mid range. You want hook lines.",
            "Stay near cover for Breather.",
            "Don't lead pushes. You support team's pick attempts.",
        ],
        "common_positioning_mistakes": [
            "Front-lining without main tank.",
            "Burning Breather under focus fire.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Hook available and target visible.",
            "Trap placed and enemy is about to engage.",
        ],
        "when_not_to_fight": [
            "Anti-naded.",
            "Sombra hunting and hook on cooldown.",
        ],
    },
}

MATCHUPS = {
    "ana": {"difficulty": "very_hard", "key_threat": "Anti shuts down Breather.",
            "advice": ["Don't engage anti-naded.", "Sleep cancels your hook commit."]},
    "reinhardt": {"difficulty": "medium", "key_threat": "Pin disrupts.",
                  "advice": ["Hook Rein over shield only when team can follow.", "Avoid pin angle."]},
    "zarya": {"difficulty": "medium", "key_threat": "Bubble denies hook damage.",
              "advice": ["Hook Zarya bubble-free.", "Don't shoot bubbled targets."]},
    "winston": {"difficulty": "medium", "key_threat": "Beam shreds while you breathe.",
                "advice": ["Trap Winston jump.", "Hook Winston while bubble down."]},
    "sombra": {"difficulty": "hard", "key_threat": "Hack disables breather mid-channel.",
               "advice": ["Breather around walls.", "Hook Sombra on hack cast."]},
    "moira": {"difficulty": "medium", "key_threat": "Fade dodges hook.",
              "advice": ["Hook Moira post-fade.", "Trap her fade exit angle."]},
}

SYNERGIES = {
    "ana": {"rating": "A", "win_condition": "Anti hook target = guaranteed kill.",
            "coordination": ["Sleep diver. Hook escape target.", "Anti pre-hook."]},
    "kiriko": {"rating": "B", "win_condition": "Suzu cleanses anti, Kitsune speeds hooks.",
               "coordination": ["Suzu Hog under focus.", "TP Hog out of bad position."]},
    "junkerqueen": {"rating": "A", "win_condition": "Anti-heal stack with knife pulls.",
                    "coordination": ["Hook JQ knife target.", "Carnage hooked target."]},
    "lucio": {"rating": "B", "win_condition": "Speed positioning.",
              "coordination": ["Speed to hook line.", "Sound barrier hook burst."]},
}
