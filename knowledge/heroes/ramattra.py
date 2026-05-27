"""Ramattra: hybrid tank, Nemesis form for brawl, ranged void for poke."""

HERO = {
    "role": "tank",
    "difficulty": "medium",
    "win_condition": "Swap between Omnic form (shield + ranged poke) and Nemesis form (close brawl). Annihilation locks them down for team kills.",
    "abilities": {
        "annihilation": {
            "optimal_use": [
                "On 3+ enemies grouped (extends with each hit).",
                "Combo with team burst.",
                "Force enemy off objective during overtime.",
            ],
            "common_mistakes": [
                "Casting on single targets.",
                "Casting too far from enemies (drops fast).",
            ],
            "held_too_long_threshold": 35,
        },
        "ravenous_vortex": {
            "optimal_use": [
                "Zone enemies away from cover.",
                "Combine with shatter, grav, or rampage.",
                "Slow a diver entering your backline.",
            ],
            "common_mistakes": [
                "Throwing in open area where enemies walk around.",
                "Wasted on single targets.",
            ],
        },
        "nemesis_form": {
            "optimal_use": [
                "Engage at melee, gain DR plus block.",
                "Walk through enemy ults safely.",
                "Tank a key sniper shot.",
            ],
            "common_mistakes": [
                "Holding Nemesis form too long (you lose ranged poke).",
                "Burning the timer when not in fight.",
            ],
        },
        "void_barrier": {
            "optimal_use": [
                "Cover support angle.",
                "Block enemy push lane.",
            ],
            "common_mistakes": [
                "Wasting on incoming spam.",
                "Placing where it blocks your team's damage.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Swap forms based on range.",
            "Omnic for poke, Nemesis for commit.",
            "Use Vortex to control terrain.",
        ],
        "common_positioning_mistakes": [
            "Brawling in Omnic form (low HP).",
            "Standing in your own Vortex.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Nemesis available and enemy is grouped.",
            "Annihilation up and team has follow-up.",
        ],
        "when_not_to_fight": [
            "Nemesis on cooldown and enemy DPS focus is on you.",
            "Antied without Nemesis up.",
        ],
    },
}

MATCHUPS = {
    "ana": {"difficulty": "medium", "key_threat": "Anti melts your sustain in Nemesis.",
            "advice": ["Block anti incoming with void barrier.", "Engage when sleep is on cooldown."]},
    "reaper": {"difficulty": "hard", "key_threat": "Shotguns shred Nemesis form.",
               "advice": ["Vortex Reaper to slow.", "Stay Omnic form for poke."]},
    "sigma": {"difficulty": "medium", "key_threat": "Out-pokes Omnic form.",
              "advice": ["Vortex his cover.", "Force Nemesis range with Vortex pulls."]},
    "sombra": {"difficulty": "hard", "key_threat": "Hack disables form swap.",
               "advice": ["Stay near walls.", "Pre-Nemesis before hack lands."]},
    "tracer": {"difficulty": "medium", "key_threat": "Picks before Annihilation lands.",
               "advice": ["Nemesis block her blink angle.", "Vortex her engage path."]},
    "winston": {"difficulty": "medium", "key_threat": "Beam ignores Nemesis DR.",
                "advice": ["Vortex Winston jump.", "Engage Winston bubble close range."]},
}

SYNERGIES = {
    "ana": {"rating": "S", "win_condition": "Nano Nemesis form is one of the strongest 1v1 setups.",
            "coordination": ["Nano just before Annihilation.", "Anti the Vortex cluster."]},
    "lucio": {"rating": "A", "win_condition": "Speed brawl into Nemesis range.",
              "coordination": ["Speed amp on form swap.", "Sound barrier the commit."]},
    "junkerqueen": {"rating": "A", "win_condition": "Brawl duo with anti-heal pressure.",
                    "coordination": ["JQ engages, Ram annihilates.", "Anti-heal stack."]},
    "kiriko": {"rating": "S", "win_condition": "Suzu cleanses anti during Nemesis. Kitsune amps brawl.",
               "coordination": ["Suzu Annihilation anti.", "Kitsune on form swap."]},
}
