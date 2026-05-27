"""Symmetra: utility DPS, turrets for area denial, beam for sustained damage, TP for repositioning."""

HERO = {
    "role": "dps",
    "difficulty": "medium",
    "win_condition": "Hold a position with turrets. Charge beam on shields and tanks. TP team into off-angles.",
    "abilities": {
        "photon_barrier": {
            "optimal_use": [
                "Block enemy ult line.",
                "Push through choke.",
                "Save teammate from burst.",
            ],
            "common_mistakes": [
                "Barrier in spots that block your team.",
                "Wasted on no sightline value.",
            ],
            "held_too_long_threshold": 40,
        },
        "teleporter": {
            "optimal_use": [
                "Surprise flank with team.",
                "Reposition support to safety.",
                "Return RIP-Tire or D.Va bomb.",
            ],
            "common_mistakes": [
                "TP placed at exposed location.",
                "Forgetting TP exists when team needs it.",
            ],
        },
        "sentry_turret": {
            "optimal_use": [
                "Cover flank route.",
                "Slow enemy push.",
                "Charge your beam off turret damage.",
            ],
            "common_mistakes": [
                "Turrets in low-value spots.",
                "Not replacing destroyed turrets.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Choke control with turret + beam.",
            "Stay near your TP for repositions.",
            "Charge beam on shields safely.",
        ],
        "common_positioning_mistakes": [
            "Solo beam tank without escape.",
            "TP placed where enemy can destroy.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Beam fully charged.",
            "TP placed for team push.",
        ],
        "when_not_to_fight": [
            "Beam 1 charge and dove.",
            "Open ground with no turrets.",
        ],
    },
}

MATCHUPS = {
    "pharah": {"difficulty": "very_hard", "key_threat": "Aerial out of beam range.",
               "advice": ["Switch off Sym into Pharah.", "Barrier her sightline."]},
    "widowmaker": {"difficulty": "hard", "key_threat": "Picks before beam charges.",
                   "advice": ["Take TP angles she can't see.", "Barrier her sightline."]},
    "reinhardt": {"difficulty": "easy", "key_threat": "Shield is beam fuel.",
                  "advice": ["Charge beam on Rein shield freely.", "Don't melee Rein."]},
    "winston": {"difficulty": "easy", "key_threat": "Bubble is beam fuel.",
                "advice": ["Charge beam on bubble.", "Melt Winston post-bubble."]},
    "tracer": {"difficulty": "medium", "key_threat": "Closes range.",
               "advice": ["Turret your back angles.", "Beam Tracer at melee."]},
    "ana": {"difficulty": "medium", "key_threat": "Anti melts you.",
            "advice": ["Don't beam anti-naded.", "TP through anti."]},
}

SYNERGIES = {
    "reinhardt": {"rating": "B", "win_condition": "Sym charges on Rein shield, TP for shatter angles.",
                  "coordination": ["Charge beam on Rein.", "TP team to shatter angle."]},
    "winston": {"rating": "B", "win_condition": "Beam fuels on bubble, dive synergy.",
                "coordination": ["Bubble + beam tank.", "TP backup angle."]},
    "ana": {"rating": "B", "win_condition": "Anti + Sym beam = melted.",
            "coordination": ["Anti the beam target.", "Nano Sym for sustained beam."]},
    "lucio": {"rating": "B", "win_condition": "Speed amp on TP push.",
              "coordination": ["Speed to TP entry.", "Sound barrier the push."]},
}
