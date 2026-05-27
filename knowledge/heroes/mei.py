"""Mei: utility DPS, wall denies angles, freeze sets up burst, Blizzard CC."""

HERO = {
    "role": "dps",
    "difficulty": "medium",
    "win_condition": "Wall to deny enemy positioning. Freeze + icicle bursts squishies. Blizzard sets up teamfight wins.",
    "abilities": {
        "blizzard": {
            "optimal_use": [
                "On grouped enemies (CC chain).",
                "Combo with shatter, grav.",
                "Deny objective during overtime.",
            ],
            "common_mistakes": [
                "Blizzard with no follow-up.",
                "Wasted on single targets.",
            ],
            "held_too_long_threshold": 40,
        },
        "ice_wall": {
            "optimal_use": [
                "Split enemy team.",
                "Block enemy ult line.",
                "Save teammate from burst.",
            ],
            "common_mistakes": [
                "Walling in your own team.",
                "Wasted on no positional value.",
            ],
        },
        "cryo_freeze": {
            "optimal_use": [
                "Bypass damage windows.",
                "Heal up mid-fight.",
                "Wait out enemy ult.",
            ],
            "common_mistakes": [
                "Freezing in open ground enemies surround.",
                "Freezing past optimal moment.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Close range with wall escape.",
            "Hold corners; wait for enemy to peek.",
            "Wall for vertical advantage.",
        ],
        "common_positioning_mistakes": [
            "Open ground without wall.",
            "Wall trapping yourself.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Blizzard up and team committed.",
            "Wall ready for split.",
        ],
        "when_not_to_fight": [
            "Cryo on cooldown and dove.",
            "Anti-naded.",
        ],
    },
}

MATCHUPS = {
    "pharah": {"difficulty": "hard", "key_threat": "Aerial out of freeze range.",
               "advice": ["Wall block Pharah line.", "Icicle Pharah grounded."]},
    "widowmaker": {"difficulty": "hard", "key_threat": "Out-snipes.",
                   "advice": ["Wall split her sightline.", "Cryo on scope."]},
    "winston": {"difficulty": "medium", "key_threat": "Bubble dives.",
                "advice": ["Wall block bubble.", "Freeze his target."]},
    "tracer": {"difficulty": "medium", "key_threat": "Out-mobiles.",
               "advice": ["Wall trap Tracer.", "Freeze when she's stuck."]},
    "reinhardt": {"difficulty": "easy", "key_threat": "Pin denies.",
                  "advice": ["Wall Rein's pin angle.", "Freeze Rein in shatter cast."]},
    "ana": {"difficulty": "medium", "key_threat": "Anti + sleep.",
            "advice": ["Cryo on anti.", "Wall her sleep sightline."]},
}

SYNERGIES = {
    "reinhardt": {"rating": "A", "win_condition": "Wall + Shatter combo.",
                  "coordination": ["Wall to group enemies for shatter.", "Freeze post-shatter."]},
    "ana": {"rating": "A", "win_condition": "Anti + Blizzard wipes.",
            "coordination": ["Anti the Blizzard cluster.", "Nano Mei for sustained walls."]},
    "zarya": {"rating": "S", "win_condition": "Grav + Blizzard for guaranteed wipe.",
              "coordination": ["Grav before Blizzard.", "Bubble Mei on commit."]},
    "kiriko": {"rating": "A", "win_condition": "Suzu cleanses anti during commit.",
               "coordination": ["Suzu Mei on Blizzard cast.", "Kitsune the wall push."]},
}
