"""Pharah: aerial DPS, rockets force enemy to track high, Barrage zones grouped enemies."""

HERO = {
    "role": "dps",
    "difficulty": "medium",
    "win_condition": "Stay airborne, poke from angles enemy can't punish. Barrage cluster kills.",
    "abilities": {
        "barrage": {
            "optimal_use": [
                "On grouped enemies with no escape.",
                "From high angle they can't shoot.",
                "Combo with grav, shatter, or hack.",
            ],
            "common_mistakes": [
                "Barrage with sightline of multiple hitscan.",
                "Barrage open area enemies kite.",
            ],
            "held_too_long_threshold": 40,
        },
        "concussive_blast": {
            "optimal_use": [
                "Boop enemy off high ground.",
                "Push enemy into your team's damage.",
                "Increase your aerial mobility (jet boost).",
            ],
            "common_mistakes": [
                "Wasted on no positional gain.",
                "Forgetting to use.",
            ],
        },
        "jump_jet": {
            "optimal_use": [
                "Reach barrage angle.",
                "Escape hitscan focus.",
                "Reposition.",
            ],
            "common_mistakes": [
                "Burning jet out of fight.",
                "Stuck on ground without jet.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Stay airborne. Don't land.",
            "Use boost to maintain altitude.",
            "Take angles enemy hitscan can't track.",
        ],
        "common_positioning_mistakes": [
            "Landing in enemy team.",
            "Flying into Soldier/Ashe sightline.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "No enemy hitscan healthy.",
            "Pocket Mercy with you.",
        ],
        "when_not_to_fight": [
            "Soldier/Ashe/Cassidy uncountered.",
            "Sombra hunting (hack ends your aerial).",
        ],
    },
}

MATCHUPS = {
    "soldier76": {"difficulty": "very_hard", "key_threat": "Hitscan with helix.",
                  "advice": ["Stay above his max angle.", "Don't barrage in his sightline."]},
    "ashe": {"difficulty": "very_hard", "key_threat": "Scoped hitscan tracks you.",
             "advice": ["Boost erratically.", "Barrage from Ashe's blind angle."]},
    "cassidy": {"difficulty": "hard", "key_threat": "Mag-grenade auto tracks.",
                "advice": ["Stay out of mag range.", "Barrage when he's on cooldown."]},
    "sombra": {"difficulty": "very_hard", "key_threat": "Hack ends aerial.",
               "advice": ["Stay high so hack can't connect.", "Barrage when Sombra's revealed."]},
    "reinhardt": {"difficulty": "easy", "key_threat": "Shield denies rockets.",
                  "advice": ["Splash rockets around shield.", "Barrage cluster behind shield."]},
    "zenyatta": {"difficulty": "medium", "key_threat": "Discord melts you.",
                 "advice": ["Stay out of LoS when discorded.", "Barrage Zen during ult."]},
}

SYNERGIES = {
    "mercy": {"rating": "S", "win_condition": "Pharmercy: aerial control of match.",
              "coordination": ["GA chain off Pharah.", "Damage boost Barrage."]},
    "ana": {"rating": "A", "win_condition": "Nano Barrage wipes grouped enemies.",
            "coordination": ["Anti the cluster.", "Nano on Barrage cast."]},
    "winston": {"rating": "A", "win_condition": "Bubble splits enemy focus, Pharah barrage from above.",
                "coordination": ["Winston dives, Pharah barrages.", "Bubble Pharah grounded."]},
    "lucio": {"rating": "B", "win_condition": "Speed positioning, sound barrier on Barrage.",
              "coordination": ["Speed amp on rocket jump.", "Sound barrier Barrage commit."]},
}
