"""Reaper: close-range shotgun, tank buster, Wraith to disengage."""

HERO = {
    "role": "dps",
    "difficulty": "low",
    "win_condition": "Close-range shred. Out-damage tanks with shotguns. Death Blossom in 1.5 second windows.",
    "abilities": {
        "death_blossom": {
            "optimal_use": [
                "On 2+ enemies grouped within melee range.",
                "Combo with grav, shatter.",
                "Behind enemy line via shadow step.",
            ],
            "common_mistakes": [
                "Cast from too far.",
                "Burning ult with no team setup.",
            ],
            "held_too_long_threshold": 35,
        },
        "wraith_form": {
            "optimal_use": [
                "Escape low HP.",
                "Bypass damage windows.",
                "Reposition to flank angle.",
            ],
            "common_mistakes": [
                "Wraith in middle of fight (no damage during).",
                "Forgetting to use when low.",
            ],
        },
        "shadow_step": {
            "optimal_use": [
                "Reposition to flank.",
                "Reach high ground angle.",
                "Engage from enemy backline.",
            ],
            "common_mistakes": [
                "Telegraphed shadow step.",
                "Stepping into enemy team.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Close range. Always within shotgun spread.",
            "Flank angles to dive tanks from behind.",
            "Wraith ready when low.",
        ],
        "common_positioning_mistakes": [
            "Long range damage (you do nothing).",
            "Wraith blown out of fight.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Enemy tank exposed.",
            "Death Blossom + team push.",
        ],
        "when_not_to_fight": [
            "Anti-naded.",
            "Sombra hunting and Wraith on cooldown.",
        ],
    },
}

MATCHUPS = {
    "winston": {"difficulty": "easy", "key_threat": "Beam shreds at melee.",
                "advice": ["Shotgun Winston in 1v1.", "Wraith out of bubble."]},
    "dva": {"difficulty": "easy", "key_threat": "DM eats shotgun rounds.",
            "advice": ["Force her to drop DM.", "Shotgun mech post-DM."]},
    "ana": {"difficulty": "very_hard", "key_threat": "Anti melts you, sleep cancels.",
            "advice": ["Wraith on anti.", "Engage Ana from blind angle."]},
    "tracer": {"difficulty": "hard", "key_threat": "Out-mobiles you.",
               "advice": ["Wraith Tracer engages.", "Force shotgun spread on her."]},
    "pharah": {"difficulty": "very_hard", "key_threat": "Aerial out of shotgun range.",
               "advice": ["Switch heroes if Pharah uncountered.", "Wraith her ult."]},
    "moira": {"difficulty": "medium", "key_threat": "Beam locks on, fade saves her.",
              "advice": ["Wait for fade then shotgun.", "Wraith her beam."]},
}

SYNERGIES = {
    "ana": {"rating": "S", "win_condition": "Anti + Reaper shreds tanks instantly.",
            "coordination": ["Anti the tank.", "Nano Reaper for Blossom."]},
    "lucio": {"rating": "A", "win_condition": "Speed engage on flank.",
              "coordination": ["Speed amp to flank.", "Sound barrier Blossom."]},
    "zarya": {"rating": "S", "win_condition": "Grav + Blossom wipes.",
              "coordination": ["Grav before Blossom.", "Bubble Reaper on dive."]},
    "junkerqueen": {"rating": "S", "win_condition": "Close-range brawl duo.",
                    "coordination": ["JQ knife pull, Reaper shotguns.", "Anti-heal stack."]},
}
