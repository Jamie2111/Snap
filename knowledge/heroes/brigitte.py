"""Brigitte: anti-dive support, peel for backline, Rally for sustained brawl."""

HERO = {
    "role": "support",
    "difficulty": "medium",
    "win_condition": "Anti-dive your backline. Whip + shield bash combo bursts squishies. Rally enables brawl pushes.",
    "abilities": {
        "rally": {
            "optimal_use": [
                "On a coordinated team push.",
                "When team is grouped and brawling.",
                "Defensive boost when teamfight is starting.",
            ],
            "common_mistakes": [
                "Rally with team out of position.",
                "Rally too early before commit.",
            ],
            "held_too_long_threshold": 45,
        },
        "shield_bash": {
            "optimal_use": [
                "Stun diver attempting to dunk your backline.",
                "Cancel enemy ult cast.",
                "Combo with whip shot for burst.",
            ],
            "common_mistakes": [
                "Wasted on no threat.",
                "Bash with shield broken (no use without shield up).",
            ],
        },
        "whip_shot": {
            "optimal_use": [
                "Knock diver away from teammate.",
                "Confirm kill on low HP enemy.",
                "Apply pressure at range.",
            ],
            "common_mistakes": [
                "Wasted on no peel value.",
                "Whip into your own team.",
            ],
        },
        "repair_pack": {
            "optimal_use": [
                "Heal tank under burst.",
                "Heal flanker between engages.",
                "Triple-stack on key target.",
            ],
            "common_mistakes": [
                "Wasting on full HP allies.",
                "Forgetting on cooldown.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Stay near support to peel for them.",
            "Inspire aura must be touching your team.",
            "Shield up but don't burn it.",
        ],
        "common_positioning_mistakes": [
            "Roaming alone away from team.",
            "Shield broken with no escape.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Diver entering your backline (anti-dive moment).",
            "Team commits brawl with Rally up.",
        ],
        "when_not_to_fight": [
            "Solo against full enemy team.",
            "Shield broken and no support nearby.",
        ],
    },
}

MATCHUPS = {
    "tracer": {"difficulty": "easy", "key_threat": "Pulse bomb burst.",
               "advice": ["Whip + bash Tracer on engage.", "Peel for second support."]},
    "genji": {"difficulty": "easy", "key_threat": "Blade burst.",
              "advice": ["Whip Genji during deflect to deny dash.", "Bash blade cast."]},
    "doomfist": {"difficulty": "medium", "key_threat": "Punch through your shield.",
                 "advice": ["Bash mid-punch.", "Whip into your team after Doom commits."]},
    "winston": {"difficulty": "medium", "key_threat": "Beam shreds at melee.",
                "advice": ["Bash Winston in bubble.", "Whip Winston off ledge."]},
    "reinhardt": {"difficulty": "hard", "key_threat": "Hammer chains.",
                  "advice": ["Don't melee duel Rein.", "Peel for your support."]},
    "ana": {"difficulty": "medium", "key_threat": "Anti-nade.",
            "advice": ["Whip Ana sleep cast.", "Repair pack the anti target."]},
}

SYNERGIES = {
    "reinhardt": {"rating": "S", "win_condition": "Brawl synergy with armor + speed.",
                  "coordination": ["Repair Rein under focus.", "Rally on shatter cast."]},
    "junkerqueen": {"rating": "A", "win_condition": "Anti-dive brawl combo.",
                    "coordination": ["Peel JQ after knife pull.", "Rally on Rampage."]},
    "lucio": {"rating": "A", "win_condition": "Healing aura stack with speed.",
              "coordination": ["Heal aura while Brig peels.", "Sound barrier on Rally."]},
    "cassidy": {"rating": "S", "win_condition": "Anti-dive duo.",
                "coordination": ["Brig peels diver, Cass executes.", "Whip combo with mag-grenade."]},
}
