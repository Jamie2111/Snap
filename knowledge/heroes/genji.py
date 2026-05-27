"""Genji: dive isolated supports, escape with dash; Dragonblade needs team setup."""

HERO = {
    "role": "dps",
    "difficulty": "very_high",
    "win_condition": "Dive isolated supports and escape. Dragonblade only works when your team is also fighting. Never blade alone.",
    "abilities": {
        "dragonblade": {
            "optimal_use": [
                "After Nano Boost from Ana.",
                "When enemy supports are isolated or low.",
                "When your team has already won the fight and you clean up.",
            ],
            "common_mistakes": [
                "Blading into a full team with no setup.",
                "Blading without communicating to your team.",
                "Blading when sleep dart or anti-nade are available on you.",
            ],
            "held_too_long_threshold": 25,
        },
        "swift_strike": {
            "optimal_use": [
                "Reset on kill to chain eliminations.",
                "Escape tool. Dash through enemies to disengage.",
            ],
            "common_mistakes": [
                "Using Swift Strike to engage with no escape plan.",
                "Not using the reset on kill to extend blade.",
            ],
        },
        "deflect": {
            "optimal_use": [
                "Against projectile DPS and ultimates (Dragonstrike, Junkrat ult).",
                "When closing distance to disrupt enemy aim.",
            ],
            "common_mistakes": [
                "Deflecting hitscan with no angle. They keep hitting you.",
                "Wasting on Lucio or Mercy who deal negligible damage.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "You need a way out before you go in.",
            "Target the support, not the tank.",
            "High ground gives you deflect angles and escape routes.",
        ],
        "common_positioning_mistakes": [
            "Standing on the front line where the tank can punish you.",
            "Climbing into the enemy backline without an escape angle.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Enemy support is alone or low.",
            "Your tank has engaged and pulled focus.",
        ],
        "when_not_to_fight": [
            "Anti-dive comp on the field (Brig, Cass, Sombra).",
            "You have no dash or no deflect after first engage.",
        ],
    },
}

MATCHUPS = {
    "moira": {"difficulty": "hard", "key_threat": "Beam locks on through deflect angles.",
              "advice": ["Don't duel Moira with no escape. Dash through her to break beam.", "Wait for her fade before committing your dash."]},
    "brigitte": {"difficulty": "very_hard", "key_threat": "Whip shot, shield bash, and aura sustain shred your dive.",
                 "advice": ["Don't blade with Brig alive on the enemy team.", "If you must engage, do it from max range with deflect ready."]},
    "cassidy": {"difficulty": "hard", "key_threat": "Mag-grenade ends your engages.",
                "advice": ["Engage from a flank, not head-on.", "Bait mag-grenade with a dash, then commit on cooldown."]},
    "sombra": {"difficulty": "hard", "key_threat": "Hack ends your dash + deflect window.",
               "advice": ["Watch your translocator and her positioning before committing."]},
    "zenyatta": {"difficulty": "easy", "key_threat": "Discord kills you fast if hit.",
                 "advice": ["Zen has no mobility. Dash + blade combo lands if his team is busy."]},
    "mercy": {"difficulty": "easy", "key_threat": "GA escape if she sees you coming.",
              "advice": ["Engage from her blind spot. Climb angles."]},
}

SYNERGIES = {
    "ana": {"rating": "S", "win_condition": "Nano-blade. Period.",
            "coordination": ["Communicate blade timing.", "Anti-nade the cluster you dive through."]},
    "zarya": {"rating": "S", "win_condition": "Grav + blade clears teams.",
              "coordination": ["Wait for grav before blade.", "Bubble yourself when committing solo."]},
    "lucio": {"rating": "A", "win_condition": "Speed dive, sound barrier extends blade.",
              "coordination": ["Engage on speed amp.", "Sound barrier the blade commit."]},
    "kiriko": {"rating": "S", "win_condition": "Kitsune + blade wins almost any fight.",
               "coordination": ["Combo Kitsune + blade timing.", "Suzu yourself on anti or sleep."]},
}
