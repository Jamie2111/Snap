"""Junkrat: spam DPS, area denial, RIP-Tire instant pick."""

HERO = {
    "role": "dps",
    "difficulty": "low",
    "win_condition": "Force chokepoint damage with grenades. Trap key flank route. RIP-Tire wins teamfights.",
    "abilities": {
        "riptire": {
            "optimal_use": [
                "Drive into enemy backline cluster.",
                "Combo with grav or hack.",
                "Force enemy off objective.",
            ],
            "common_mistakes": [
                "Tire shot down before reaching enemy.",
                "Driving into shields.",
            ],
            "held_too_long_threshold": 40,
        },
        "concussion_mine": {
            "optimal_use": [
                "Boop self to high ground.",
                "Burst enemy at chokepoint.",
                "Defend yourself from diver.",
            ],
            "common_mistakes": [
                "Mining open ground without enemy nearby.",
                "Forgetting mine for vertical movement.",
            ],
        },
        "steel_trap": {
            "optimal_use": [
                "Cover flank route.",
                "Trap diver path.",
                "Combo with mine for burst kill.",
            ],
            "common_mistakes": [
                "Trap in open spam zones.",
                "Forgetting trap on cooldown.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Mid range, behind cover.",
            "High ground for arc shots.",
            "Trap your back angles.",
        ],
        "common_positioning_mistakes": [
            "Front line with frags.",
            "No mine for mobility.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Enemy grouped at choke.",
            "Tire up and team commits.",
        ],
        "when_not_to_fight": [
            "Enemy spread out.",
            "Dive comp targeting you.",
        ],
    },
}

MATCHUPS = {
    "pharah": {"difficulty": "very_hard", "key_threat": "Aerial out of arc range.",
               "advice": ["Switch off Junkrat into Pharah.", "Concussion to high ground."]},
    "widowmaker": {"difficulty": "hard", "key_threat": "Picks you long range.",
                   "advice": ["Trap her flank route.", "Concussion to off-angle."]},
    "tracer": {"difficulty": "medium", "key_threat": "Closes range.",
               "advice": ["Trap your back.", "Mine + frag for burst."]},
    "winston": {"difficulty": "medium", "key_threat": "Dives, beam shreds.",
                "advice": ["Trap Winston jump.", "Concussion out of bubble."]},
    "reinhardt": {"difficulty": "easy", "key_threat": "Shield denies frags.",
                  "advice": ["Arc over shield.", "Trap behind shield."]},
    "ana": {"difficulty": "easy", "key_threat": "Anti melts you.",
            "advice": ["Spam Ana sightline.", "Tire her angle."]},
}

SYNERGIES = {
    "zarya": {"rating": "S", "win_condition": "Grav + Tire wipes.",
              "coordination": ["Tire on grav cluster.", "Bubble Junkrat on Tire cast."]},
    "ana": {"rating": "A", "win_condition": "Anti the Tire cluster.",
            "coordination": ["Anti before Tire.", "Sleep diver Junkrat sees."]},
    "lucio": {"rating": "B", "win_condition": "Speed to choke positioning.",
              "coordination": ["Speed to high ground.", "Sound barrier Tire."]},
    "mercy": {"rating": "B", "win_condition": "Pocketed spam zoning.",
              "coordination": ["Damage boost frags.", "GA off Junkrat angles."]},
}
