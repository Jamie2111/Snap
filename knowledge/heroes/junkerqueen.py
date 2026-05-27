"""Junker Queen: brawl tank with sustain. Adrenaline rush + Carnage chains anti-heal."""

HERO = {
    "role": "tank",
    "difficulty": "medium",
    "win_condition": "Anti-heal the enemy with axe and shotgun, sustain via Adrenaline Rush. Rampage finishes grouped enemies.",
    "abilities": {
        "rampage": {
            "optimal_use": [
                "On 3+ enemies grouped (denies all healing).",
                "Coordinate with Ana anti or Soldier visor.",
                "Right before your team commits a major push.",
            ],
            "common_mistakes": [
                "Solo Rampage past your team's range.",
                "Using on single targets.",
                "Wasted at low charge in non-fight scenarios.",
            ],
            "held_too_long_threshold": 30,
        },
        "jagged_blade": {
            "optimal_use": [
                "Pull a low HP enemy into your team.",
                "Bleed a tank to deny healing.",
                "Throw + recall combo for fast burst.",
            ],
            "common_mistakes": [
                "Throwing without follow-up shotgun.",
                "Pulling a tank into your backline (wrong target).",
            ],
        },
        "commanding_shout": {
            "optimal_use": [
                "Speed your team into engage.",
                "Trade HP buff before incoming burst.",
                "Combo with Carnage for sustained pressure.",
            ],
            "common_mistakes": [
                "Holding shout for nothing.",
                "Using shout to escape (better used in fight).",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Front line, but with cover steps.",
            "Hunt out-of-position supports with Knife pull.",
            "Don't tunnel. Reset bleed targets often.",
        ],
        "common_positioning_mistakes": [
            "Diving past your team.",
            "Bleeding low-priority targets instead of focusing tanks.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Bleed stacked on enemy tank, your team has anti-heal context.",
            "Your team has speed (Lucio) or Kitsune up.",
        ],
        "when_not_to_fight": [
            "Anti-naded yourself.",
            "Enemy has Mei wall to deny your knife.",
        ],
    },
}

MATCHUPS = {
    "mauga": {"difficulty": "hard", "key_threat": "Cage Fight isolates you, ignites burns through your sustain.",
              "advice": ["Don't let Mauga cage you. Move before commit.", "Save Rampage to anti during his ult."]},
    "ana": {"difficulty": "medium", "key_threat": "Anti melts your sustain.",
            "advice": ["Use Shout immediately if anti-naded.", "Force Ana to use anti early via fake engages."]},
    "reinhardt": {"difficulty": "medium", "key_threat": "Pin denies your kit.",
                  "advice": ["Pull him out of pin angle with knife.", "Outsustain via Carnage."]},
    "sigma": {"difficulty": "hard", "key_threat": "Out-ranges you.",
              "advice": ["Force chokes that bring Sigma close.", "Knife him to bleed when he peeks."]},
    "winston": {"difficulty": "medium", "key_threat": "Dives over your front line.",
                "advice": ["Knife pull Winston away from your support.", "Shotgun him at close range."]},
    "moira": {"difficulty": "easy", "key_threat": "Heal sustain on enemy tank.",
              "advice": ["Carnage anti-heals her tank target.", "Knife Moira out of fade range."]},
}

SYNERGIES = {
    "lucio": {"rating": "S", "win_condition": "Speed brawl chains kills with Carnage.",
              "coordination": ["Speed on commit.", "Sound barrier on shout follow-up."]},
    "ana": {"rating": "S", "win_condition": "Anti + Rampage = team wipe.",
            "coordination": ["Anti the grouped enemies.", "Rampage right after anti lands."]},
    "kiriko": {"rating": "A", "win_condition": "Suzu cleanses your anti, Kitsune speeds brawl.",
               "coordination": ["Suzu Rampage anti.", "Kitsune your push."]},
    "reaper": {"rating": "S", "win_condition": "Both close-range. Shred tanks together.",
               "coordination": ["Engage on shout speed.", "Death Blossom inside Rampage."]},
}
