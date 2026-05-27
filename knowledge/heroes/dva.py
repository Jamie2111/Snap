"""D.Va: dive tank with Defense Matrix, can eat enemy ults and bomb to wipe."""

HERO = {
    "role": "tank",
    "difficulty": "medium",
    "win_condition": "Pressure backline with boosters, DM enemy damage abilities, Self-Destruct grouped enemies.",
    "abilities": {
        "self_destruct": {
            "optimal_use": [
                "Force enemy to leave position (zoning ult).",
                "Combo with grav, shatter, blade for guaranteed wipe.",
                "Boop bomb to high angle so it lands in enemy backline.",
            ],
            "common_mistakes": [
                "Bombing in open ground enemies can run from.",
                "Self-bombing with no team follow-up.",
                "Eject + bomb without escape angle.",
            ],
            "held_too_long_threshold": 30,
        },
        "defense_matrix": {
            "optimal_use": [
                "Eat Pharah Barrage, Soldier Visor, Tracer Pulse, Junkrat tire.",
                "DM your support's key burst window.",
                "Cover your team during a push.",
            ],
            "common_mistakes": [
                "DM small projectiles when big ones are coming.",
                "Burning DM out of fight.",
            ],
        },
        "boosters": {
            "optimal_use": [
                "Engage isolated support.",
                "Boop bomb after self-destruct cast.",
                "Disengage when low.",
            ],
            "common_mistakes": [
                "Boosting into the entire enemy team.",
                "Not having boosters ready when bomb peeks.",
            ],
        },
        "micro_missiles": {
            "optimal_use": [
                "Burst combo with primary fire.",
                "Finish low targets.",
            ],
            "common_mistakes": [
                "Wasting missiles on full HP tanks.",
                "Not using on cooldown.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Mid-range pressure, dive when supports are isolated.",
            "Always know where you can DM the next big damage.",
            "Stay near a wall to limit enemy angles on you.",
        ],
        "common_positioning_mistakes": [
            "Sitting in open ground with DM burned.",
            "Diving without team backup.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Enemy has key ults on cooldown.",
            "Your team can follow your dive.",
        ],
        "when_not_to_fight": [
            "DM is empty and you have no cover.",
            "Mei wall + Brig combo zones you out.",
        ],
    },
}

MATCHUPS = {
    "zarya": {"difficulty": "very_hard", "key_threat": "Beam ignores DM, bubble denies your damage.",
              "advice": ["Don't push Zarya at high charge.", "DM her grav cast, not her beam."]},
    "reaper": {"difficulty": "hard", "key_threat": "Shotguns shred your mech.",
               "advice": ["Don't dive Reaper. Boost away.", "DM his shotgun spread when forced close."]},
    "ana": {"difficulty": "medium", "key_threat": "Anti melts your mech.",
            "advice": ["DM anti-nade as it flies.", "Don't dive Ana sleep angle."]},
    "sombra": {"difficulty": "hard", "key_threat": "Hack disables DM and boosters.",
               "advice": ["Stay near a wall.", "Bait hack with a feint, then dive."]},
    "junkrat": {"difficulty": "easy", "key_threat": "Tire ult, but you eat it.",
                "advice": ["DM Junkrat tire on sight.", "Dive Junkrat constantly. He has no escape."]},
    "winston": {"difficulty": "medium", "key_threat": "Bubble + beam dive your backline.",
                "advice": ["Boost into Winston, force 1v1 close.", "DM his ult cast."]},
}

SYNERGIES = {
    "tracer": {"rating": "S", "win_condition": "Dual dive on enemy supports.",
               "coordination": ["DM Tracer pulse anti.", "Boost together onto same target."]},
    "genji": {"rating": "S", "win_condition": "Dive duo with DM cover.",
              "coordination": ["DM the dive entry.", "Bomb behind Blade for cluster damage."]},
    "ana": {"rating": "A", "win_condition": "Anti the bomb cluster.",
            "coordination": ["Anti as bomb peeks.", "Nano D.Va for sustained dive."]},
    "lucio": {"rating": "A", "win_condition": "Speed dive entry, sound barrier dive escape.",
              "coordination": ["Speed amp on boost.", "Sound barrier bomb landing."]},
}
