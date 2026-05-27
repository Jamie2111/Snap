"""Orisa: bunker tank, Fortify + Javelin Spin denies dive, Terra Surge zones."""

HERO = {
    "role": "tank",
    "difficulty": "medium",
    "win_condition": "Hold a position with Fortify uptime. Force enemies to commit into you. Terra Surge confirms grouped kills.",
    "abilities": {
        "terra_surge": {
            "optimal_use": [
                "Hold the front line during enemy push.",
                "Combo with team burst ults.",
                "Stall an objective when team is dead.",
            ],
            "common_mistakes": [
                "Casting without team follow-up.",
                "Surging when enemy is grouped at long range. They walk away.",
            ],
            "held_too_long_threshold": 40,
        },
        "fortify": {
            "optimal_use": [
                "Eat anti-nade, hack, or burst combo.",
                "Push through chokepoint.",
                "Charge javelin shot under pressure.",
            ],
            "common_mistakes": [
                "Fortifying when no threat exists.",
                "Holding fortify until you die.",
            ],
        },
        "javelin_throw": {
            "optimal_use": [
                "Stun a key target before team focuses.",
                "Pin into wall for guaranteed kill setup.",
                "Cancel enemy ult cast.",
            ],
            "common_mistakes": [
                "Wasted on tanks (no stun effect).",
                "Missing because target is moving fast. Lead it.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Anchor a chokepoint or high-ground position.",
            "Fortify is your offense AND defense.",
            "Stay where your supports can heal through your sustain.",
        ],
        "common_positioning_mistakes": [
            "Pushing without supports.",
            "Burning Fortify before commit.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Fortify ready.",
            "Team has push synergy ult ready.",
        ],
        "when_not_to_fight": [
            "Fortify on cooldown and Ana has anti up.",
            "Dive comp targeting your supports.",
        ],
    },
}

MATCHUPS = {
    "reinhardt": {"difficulty": "easy", "key_threat": "Pin disrupts.",
                  "advice": ["Javelin throw stuns mid-pin.", "Fortify to deny shatter."]},
    "tracer": {"difficulty": "hard", "key_threat": "Hard to hit, picks supports.",
               "advice": ["Spin Javelin to peel for support.", "Don't burn Fortify on Tracer harass."]},
    "ana": {"difficulty": "medium", "key_threat": "Anti melts you.",
            "advice": ["Fortify on anti-nade.", "Don't push past your team without Fortify."]},
    "sombra": {"difficulty": "medium", "key_threat": "Hack ends Fortify.",
               "advice": ["Pre-Fortify if you suspect hack.", "Stay near walls."]},
    "winston": {"difficulty": "medium", "key_threat": "Beam ignores Javelin Spin.",
                "advice": ["Spin while supports peel.", "Throw Winston off ledge with Javelin."]},
    "bastion": {"difficulty": "easy", "key_threat": "Configuration burst.",
                "advice": ["Fortify during Bastion ult.", "Surge his config zone."]},
}

SYNERGIES = {
    "bastion": {"rating": "S", "win_condition": "Pirate ship: Orisa frontline, Bastion behind.",
                "coordination": ["Fortify on Bastion config.", "Surge during Bastion ult."]},
    "baptiste": {"rating": "S", "win_condition": "Immortality + Fortify makes the bunker unkillable for 5 seconds.",
                 "coordination": ["Bap window inside Fortify.", "Amp matrix the front line."]},
    "mercy": {"rating": "A", "win_condition": "Pocketed Orisa with damage-boosted Javelin.",
              "coordination": ["Mercy boosts Javelin charge.", "GA to Orisa during Surge."]},
    "ana": {"rating": "A", "win_condition": "Anti-nade behind your Surge.",
            "coordination": ["Anti right before Terra Surge lands.", "Nano you for Fortify push."]},
}
