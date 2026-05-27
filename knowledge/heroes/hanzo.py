"""Hanzo: projectile sniper, Storm Arrow burst, Dragonstrike zoning."""

HERO = {
    "role": "dps",
    "difficulty": "high",
    "win_condition": "Pick squishies with body shots. Storm Arrow for burst confirmation. Dragonstrike zones objectives.",
    "abilities": {
        "dragonstrike": {
            "optimal_use": [
                "Down a long sightline.",
                "Combo with grav.",
                "Force enemy off objective.",
            ],
            "common_mistakes": [
                "Strike into open ground enemies dodge.",
                "Wasted on single targets.",
            ],
            "held_too_long_threshold": 40,
        },
        "storm_arrow": {
            "optimal_use": [
                "Burst tank or grouped enemies.",
                "Combo with primary for instant pick.",
                "Self-defense against diver.",
            ],
            "common_mistakes": [
                "Wasted long range.",
                "Spammed instead of aimed.",
            ],
        },
        "sonic_arrow": {
            "optimal_use": [
                "Reveal flank enemies.",
                "Before team commits to push.",
                "Post-pick to find next target.",
            ],
            "common_mistakes": [
                "Thrown in open area without intel value.",
                "Forgetting on cooldown.",
            ],
        },
        "lunge": {
            "optimal_use": [
                "Reach high ground.",
                "Escape diver.",
                "Reposition between shots.",
            ],
            "common_mistakes": [
                "Lunge into enemy team.",
                "Burning out of fight.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Long sightlines + high ground.",
            "Climb walls for unexpected angles.",
            "Lunge ready for escape.",
        ],
        "common_positioning_mistakes": [
            "Front line with bow.",
            "Lunge into enemy backline solo.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Storm arrow ready and target in sight.",
            "Sonic arrow gives team info.",
        ],
        "when_not_to_fight": [
            "Tracer/Genji hunting.",
            "Anti-naded.",
        ],
    },
}

MATCHUPS = {
    "tracer": {"difficulty": "hard", "key_threat": "Closes distance.",
               "advice": ["Storm arrow on engage.", "Lunge out of blink."]},
    "genji": {"difficulty": "hard", "key_threat": "Deflect returns storm arrows.",
              "advice": ["Don't storm arrow deflect.", "Primary arrows Genji."]},
    "sombra": {"difficulty": "hard", "key_threat": "Hack disables lunge.",
               "advice": ["Position near walls.", "Storm arrow Sombra on hack."]},
    "widowmaker": {"difficulty": "medium", "key_threat": "Out-snipes hitscan.",
                   "advice": ["Take projectile-only angles.", "Storm arrow Widow scoped."]},
    "winston": {"difficulty": "easy", "key_threat": "Beam at melee.",
                "advice": ["Storm arrow Winston bubble.", "Lunge out of bubble."]},
    "reinhardt": {"difficulty": "easy", "key_threat": "Shield denies.",
                  "advice": ["Body shot over/around shield.", "Storm arrow when shield down."]},
}

SYNERGIES = {
    "ana": {"rating": "A", "win_condition": "Anti + storm arrow confirms tank kill.",
            "coordination": ["Anti before storm arrow.", "Nano Hanzo for sustained pressure."]},
    "mercy": {"rating": "A", "win_condition": "Boosted body shots one-shot.",
              "coordination": ["Damage boost on scope.", "GA off Hanzo."]},
    "zarya": {"rating": "S", "win_condition": "Grav + Dragonstrike wipes.",
              "coordination": ["Grav before strike.", "Bubble Hanzo on dive."]},
    "sigma": {"rating": "A", "win_condition": "Sigma covers Hanzo angle.",
              "coordination": ["Barrier Hanzo sightline.", "Grav into strike."]},
}
