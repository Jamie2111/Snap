"""Doomfist: dive tank, punch confirmation, Meteor Strike repositions."""

HERO = {
    "role": "tank",
    "difficulty": "very_high",
    "win_condition": "Slam to apply pressure, Punch to confirm picks, escape with Power Block. Meteor Strike for cleanup or escape.",
    "abilities": {
        "meteor_strike": {
            "optimal_use": [
                "Cleanup low HP targets.",
                "Escape lost fight.",
                "Reposition to flank angle.",
            ],
            "common_mistakes": [
                "Strike with no follow-up.",
                "Strike landed in open area enemies walk out of.",
            ],
            "held_too_long_threshold": 35,
        },
        "rocket_punch": {
            "optimal_use": [
                "Knock low HP enemy into your team.",
                "Pin into wall for guaranteed kill.",
                "Cancel cast ults (Cass deadeye).",
            ],
            "common_mistakes": [
                "Punching full HP tanks.",
                "Missing because target dodged. Hold punch for confirmation.",
            ],
        },
        "power_block": {
            "optimal_use": [
                "Charge empowered punch on enemy fire.",
                "Survive burst damage windows.",
                "Bait enemy ult into block.",
            ],
            "common_mistakes": [
                "Blocking no incoming damage.",
                "Forgetting to release empowered punch.",
            ],
        },
        "seismic_slam": {
            "optimal_use": [
                "Engage from off-angle.",
                "Confirm punch combo.",
                "Boop enemies off ledges.",
            ],
            "common_mistakes": [
                "Slam into the entire enemy team.",
                "Not using to gain altitude before punch.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "High-ground angles for slam.",
            "Always have punch + slam combo ready.",
            "Block on incoming damage to set up empowered.",
        ],
        "common_positioning_mistakes": [
            "Diving without escape ult.",
            "Punching into bubble or DM.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Isolated support with no peel.",
            "Empowered punch ready.",
        ],
        "when_not_to_fight": [
            "Sombra healthy on enemy team.",
            "Brig + Cass sitting on enemy support.",
        ],
    },
}

MATCHUPS = {
    "ana": {"difficulty": "hard", "key_threat": "Sleep dart cancels everything.",
            "advice": ["Punch unpredictably, not directly.", "Slam toward Ana from blind angle."]},
    "brigitte": {"difficulty": "very_hard", "key_threat": "Stun denies all combos.",
                 "advice": ["Don't engage with Brig peeling.", "Bait whip + bash, then commit."]},
    "sombra": {"difficulty": "very_hard", "key_threat": "Hack removes punch + slam.",
               "advice": ["Engage from blind angles.", "Pre-block on hack incoming."]},
    "moira": {"difficulty": "medium", "key_threat": "Fade escapes punch combo.",
              "advice": ["Engage after fade used.", "Punch toward wall to deny fade."]},
    "zenyatta": {"difficulty": "easy", "key_threat": "Discord melts you.",
                 "advice": ["Slam + punch Zen first.", "Don't extended dive when discorded."]},
    "winston": {"difficulty": "medium", "key_threat": "Bubble blocks punch wall pin.",
                "advice": ["Wait for bubble.", "Punch Winston into your team."]},
}

SYNERGIES = {
    "tracer": {"rating": "S", "win_condition": "Both dive supports.",
               "coordination": ["Doom commits, Tracer finishes.", "Pulse stick after Doom pin."]},
    "ana": {"rating": "A", "win_condition": "Anti the punch target for guaranteed kill.",
            "coordination": ["Anti pre-punch.", "Nano Doom for survival in dive."]},
    "kiriko": {"rating": "S", "win_condition": "Suzu cleanses sleep, Kitsune speeds dive.",
               "coordination": ["Suzu Doom on engage.", "TP Doom out of bad dive."]},
    "lucio": {"rating": "A", "win_condition": "Speed dive sustain.",
              "coordination": ["Speed amp on slam.", "Sound barrier Meteor."]},
}
