"""Moira: hybrid DPS/heal support, beam at melee, Fade for repositioning, Coalescence for ult."""

HERO = {
    "role": "support",
    "difficulty": "low",
    "win_condition": "Sustain via heal orbs at range, beam at melee, fade to escape. Coalescence for ult chain.",
    "abilities": {
        "coalescence": {
            "optimal_use": [
                "Sustain team through enemy burst ult.",
                "Damage grouped enemies.",
                "Combo with brawl push.",
            ],
            "common_mistakes": [
                "Coalescence open ground (you die mid-channel).",
                "Burning ult with no team commit.",
            ],
            "held_too_long_threshold": 40,
        },
        "biotic_orb": {
            "optimal_use": [
                "Heal orb for team sustain.",
                "Damage orb in tight space.",
                "Both orbs in fight start.",
            ],
            "common_mistakes": [
                "Heal orb wasted out of fight.",
                "Damage orb in open area.",
            ],
        },
        "fade": {
            "optimal_use": [
                "Escape burst damage.",
                "Reposition to flank.",
                "Bypass anti-nade or sleep.",
            ],
            "common_mistakes": [
                "Fade before damage incoming.",
                "Forgetting to use when low.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Mid-range with fade safety net.",
            "Heal orb your team behind cover.",
            "Don't anchor; you're mobile.",
        ],
        "common_positioning_mistakes": [
            "Diving past your team.",
            "Out of LoS to teammates.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Fade up and team commits.",
            "Coalescence ready.",
        ],
        "when_not_to_fight": [
            "Fade on cooldown and dove.",
            "Anti-naded.",
        ],
    },
}

MATCHUPS = {
    "tracer": {"difficulty": "medium", "key_threat": "Picks you fast.",
               "advice": ["Fade on pulse stick.", "Beam Tracer at melee."]},
    "genji": {"difficulty": "easy", "key_threat": "Blade burst.",
              "advice": ["Beam Genji during blade (lock on).", "Fade out of dash."]},
    "sombra": {"difficulty": "hard", "key_threat": "Hack disables Fade.",
               "advice": ["Stay near walls.", "Fade pre-hack."]},
    "ana": {"difficulty": "medium", "key_threat": "Anti melts.",
            "advice": ["Fade on anti.", "Sleep cancels Coalescence."]},
    "winston": {"difficulty": "medium", "key_threat": "Beam at melee.",
                "advice": ["Beam Winston back at melee.", "Fade out of bubble."]},
    "reinhardt": {"difficulty": "easy", "key_threat": "Shatter wipes.",
                  "advice": ["Fade on shatter.", "Coalescence during recovery."]},
}

SYNERGIES = {
    "junkerqueen": {"rating": "A", "win_condition": "Anti-heal brawl, Moira sustains rear.",
                    "coordination": ["Heal JQ during Rampage.", "Coalescence on Carnage push."]},
    "reinhardt": {"rating": "B", "win_condition": "Brawl sustain.",
                  "coordination": ["Heal orb behind shield.", "Coalescence on shatter cast."]},
    "lucio": {"rating": "B", "win_condition": "Mobility synergy.",
              "coordination": ["Speed amp on fade.", "Sound barrier on Coalescence."]},
    "winston": {"rating": "B", "win_condition": "Dive duo with sustain.",
                "coordination": ["Heal orb Winston bubble.", "Beam Winston target at melee."]},
}
