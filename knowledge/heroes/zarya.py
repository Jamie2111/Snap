"""Zarya: bubble tank, charges damage into beam threat, Graviton wins fights."""

HERO = {
    "role": "tank",
    "difficulty": "high",
    "win_condition": "Bubble incoming damage to charge energy, then melt their team with beam. Graviton sets up the round-winning kill.",
    "abilities": {
        "graviton_surge": {
            "optimal_use": [
                "On 3 or more enemies, with team ult follow-up ready.",
                "Combo with Dragonblade, Earthshatter, RIP-Tire, Barrage.",
                "Force a fight you're winning into a wipe.",
            ],
            "common_mistakes": [
                "Solo grav with no followup.",
                "Grav inside enemy shields.",
                "Grav when your team has no cooldowns.",
            ],
            "held_too_long_threshold": 30,
        },
        "particle_barrier": {
            "optimal_use": [
                "Eat a big damage source (DM, Sigma rock, Soldier mag).",
                "Bubble on engagement to charge energy fast.",
                "Self-bubble during retreat to survive.",
            ],
            "common_mistakes": [
                "Bubbling tickle damage instead of big shots.",
                "Bubble timing too early or too late.",
            ],
        },
        "projected_barrier": {
            "optimal_use": [
                "Bubble a diving teammate.",
                "Bubble your DPS during their key engage.",
                "Save Genji from anti-nade.",
            ],
            "common_mistakes": [
                "Wasting on a teammate already safe.",
                "Bubbling a teammate already at low HP under burst.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Close range. You need beam range to convert charge.",
            "Bubble on commit, not on retreat.",
            "Stay with your team to share bubbles.",
        ],
        "common_positioning_mistakes": [
            "Diving alone with both bubbles.",
            "Hiding behind a Rein who burns your bubbles.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "High charge (60+ energy) with team behind you.",
            "Enemy is grouped for Graviton.",
        ],
        "when_not_to_fight": [
            "Low charge, bubbles on cooldown.",
            "Anti-nade landed on your tank during commit.",
        ],
    },
}

MATCHUPS = {
    "winston": {"difficulty": "very_hard", "key_threat": "Beam ignores bubble damage.",
                "advice": ["Don't bubble Winston beam.", "Push close so HE has to play melee with you."]},
    "reaper": {"difficulty": "hard", "key_threat": "Shotgun damage shreds even with bubble.",
               "advice": ["Bubble pre-engage to deny his charge.", "Don't beam him if he's full HP."]},
    "moira": {"difficulty": "hard", "key_threat": "Beam locks on through bubble breaks.",
              "advice": ["Bubble teammates Moira is beaming, not yourself.", "Bait fade with bubble down."]},
    "ana": {"difficulty": "medium", "key_threat": "Anti melts your sustain.",
            "advice": ["Bubble pre-anti read.", "Don't engage anti-naded."]},
    "sombra": {"difficulty": "hard", "key_threat": "Hack disables bubble and grav.",
               "advice": ["Bubble before hack lands.", "Stay near walls."]},
    "junkrat": {"difficulty": "easy", "key_threat": "Spam denies positioning.",
                "advice": ["Bubble through spam to charge.", "Beam Junkrat at range."]},
}

SYNERGIES = {
    "reinhardt": {"rating": "S", "win_condition": "Bubble Rein on shatter cast for guaranteed pin damage.",
                  "coordination": ["Bubble before Ana sleep timing.", "Grav + Shatter is round-winning."]},
    "genji": {"rating": "S", "win_condition": "Grav + Blade is meta-defining combo.",
              "coordination": ["Bubble Genji on commit.", "Grav before Blade."]},
    "ana": {"rating": "S", "win_condition": "Nano grav user = team wipe.",
            "coordination": ["Anti the grav cluster.", "Nano you for sustained beam."]},
    "tracer": {"rating": "A", "win_condition": "Bubble Tracer's pulse-bomb engage.",
               "coordination": ["Bubble her in. She pulses. You graviton the cluster."]},
}
