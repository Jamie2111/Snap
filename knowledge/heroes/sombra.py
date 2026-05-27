"""Sombra: hack denies key abilities, virus burst, translocator escape."""

HERO = {
    "role": "dps",
    "difficulty": "high",
    "win_condition": "Hack the highest-leverage enemy ability, virus + primary to burst pick. EMP wipes ults and shields.",
    "abilities": {
        "emp": {
            "optimal_use": [
                "Right before team commits a push.",
                "Combo with grav or shatter.",
                "Counter enemy ult cast (Bap window, Trans).",
            ],
            "common_mistakes": [
                "EMP without team follow-up.",
                "Burning EMP solo.",
            ],
            "held_too_long_threshold": 40,
        },
        "hack": {
            "optimal_use": [
                "Hack key ability target (Ana sleep, Suzu, Bap window).",
                "Hack diver to deny escape.",
                "Hack tank pre-engage.",
            ],
            "common_mistakes": [
                "Hacking low-leverage targets.",
                "Hack from a position you can't damage from after.",
            ],
        },
        "virus": {
            "optimal_use": [
                "Hack + virus + primary for burst kill.",
                "DoT a low HP target.",
                "Force healing waste.",
            ],
            "common_mistakes": [
                "Virus full HP tank.",
                "Wasted virus without hack setup.",
            ],
        },
        "translocator": {
            "optimal_use": [
                "Escape after pick.",
                "Reposition to flank angle.",
                "Engage from unexpected angle.",
            ],
            "common_mistakes": [
                "Translocator into enemy team.",
                "Not having translocator ready when low.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Behind enemy lines, flank angles.",
            "Always have translocator ready.",
            "Track enemy cooldowns to know what to hack.",
        ],
        "common_positioning_mistakes": [
            "Engaging without escape ready.",
            "Hacking from a corner you can't damage from.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Enemy support out of position.",
            "Hack + virus combo ready.",
        ],
        "when_not_to_fight": [
            "Translocator on cooldown.",
            "Mei/Brig walling your flank routes.",
        ],
    },
}

MATCHUPS = {
    "mercy": {"difficulty": "easy", "key_threat": "GA escape.",
              "advice": ["Hack pre-virus.", "Position to cut off GA target."]},
    "ana": {"difficulty": "easy", "key_threat": "Sleep cancels you.",
            "advice": ["Hack Ana first.", "Virus + primary while she sleeps."]},
    "tracer": {"difficulty": "hard", "key_threat": "Closes range, picks you.",
               "advice": ["Translocator on Tracer engage.", "Hack her recall."]},
    "brigitte": {"difficulty": "medium", "key_threat": "Stuns deny hack.",
                 "advice": ["Hack from outside whip range.", "Pick non-Brig support."]},
    "winston": {"difficulty": "medium", "key_threat": "Beam shreds at melee.",
                "advice": ["Hack Winston bubble.", "Translocator out of bubble."]},
    "reinhardt": {"difficulty": "easy", "key_threat": "Pin if close.",
                  "advice": ["Hack Rein to deny pin and shatter.", "Virus from behind shield."]},
}

SYNERGIES = {
    "tracer": {"rating": "S", "win_condition": "Hack support, Tracer secures pulse.",
               "coordination": ["Hack the dive target.", "Engage simultaneously."]},
    "genji": {"rating": "S", "win_condition": "EMP + Blade wipes teams.",
              "coordination": ["EMP before Blade cast.", "Hack peel target."]},
    "ana": {"rating": "A", "win_condition": "Hack Suzu so anti-nade lands.",
            "coordination": ["Hack their Kiriko.", "Virus + anti = kill."]},
    "winston": {"rating": "A", "win_condition": "Dive duo with hack disruption.",
                "coordination": ["Hack Winston's dive target.", "EMP on Winston commit."]},
}
