"""Wrecking Ball: rolling dive tank, disruption-first, isolates picks via grapple."""

HERO = {
    "role": "tank",
    "difficulty": "very_high",
    "win_condition": "Disrupt backline positioning, isolate one squishy, escape via grapple. Minefield denies an area.",
    "abilities": {
        "minefield": {
            "optimal_use": [
                "On capture point during overtime.",
                "Combo with grav or shatter.",
                "Block enemy push lane.",
            ],
            "common_mistakes": [
                "Mines in open area with multiple escape routes.",
                "Ult with no team follow-up.",
            ],
            "held_too_long_threshold": 35,
        },
        "grappling_claw": {
            "optimal_use": [
                "Roll-momentum slam onto enemy.",
                "Escape after picking.",
                "Reach high ground angles.",
            ],
            "common_mistakes": [
                "Grappling into entire enemy team.",
                "Not using to disengage when low.",
            ],
        },
        "adaptive_shield": {
            "optimal_use": [
                "Engage with shields up.",
                "Survive burst windows.",
                "Bait enemy cooldowns then shield.",
            ],
            "common_mistakes": [
                "Shielding too early before commit.",
                "Forgetting to shield during dive.",
            ],
        },
        "piledriver": {
            "optimal_use": [
                "Slam onto isolated support after grapple swing.",
                "Knock enemies off ledges.",
                "Cancel enemy ult cast.",
            ],
            "common_mistakes": [
                "Slamming with no follow-up damage.",
                "Slam in open area.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Always swinging, never static.",
            "Disrupt = win. Knock enemies out of position.",
            "Escape angle planned BEFORE engage.",
        ],
        "common_positioning_mistakes": [
            "Engaging without an exit grapple.",
            "Slamming with shield down.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Enemy support isolated.",
            "Shields and grapple both up.",
        ],
        "when_not_to_fight": [
            "Sombra healthy on enemy.",
            "Brig + Cass anti-dive on backline.",
        ],
    },
}

MATCHUPS = {
    "sombra": {"difficulty": "very_hard", "key_threat": "Hack kills your swing.",
               "advice": ["Bait hack, then engage.", "Grapple from blind angles."]},
    "ana": {"difficulty": "hard", "key_threat": "Sleep mid-swing.",
            "advice": ["Engage when sleep is gone.", "Shield through anti-nade."]},
    "brigitte": {"difficulty": "very_hard", "key_threat": "Whip + stun denies engage.",
                 "advice": ["Don't slam into Brig.", "Pick the OTHER support."]},
    "reinhardt": {"difficulty": "easy", "key_threat": "Hammer can punish slow rolls.",
                  "advice": ["Boop Rein team out of position.", "Avoid pin angle."]},
    "moira": {"difficulty": "medium", "key_threat": "Fade dodges piledriver.",
              "advice": ["Slam post-fade.", "Boop Moira off objective."]},
    "winston": {"difficulty": "medium", "key_threat": "Beam shreds during slam.",
                "advice": ["Shield + swing past Winston.", "Don't 1v1 his bubble."]},
}

SYNERGIES = {
    "ana": {"rating": "A", "win_condition": "Anti the slam target.",
            "coordination": ["Anti pre-piledriver.", "Sleep peel target Hammond commits to."]},
    "tracer": {"rating": "S", "win_condition": "Dive duo.",
               "coordination": ["Hammond disrupts, Tracer finishes.", "Engage same target."]},
    "kiriko": {"rating": "S", "win_condition": "TP and suzu enable aggressive Hammond.",
               "coordination": ["Suzu Hammond anti-nade.", "TP Hammond out of bad swing."]},
    "lucio": {"rating": "A", "win_condition": "Speed swing chains.",
              "coordination": ["Speed amp on engage.", "Sound barrier disruption."]},
}
