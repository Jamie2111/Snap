"""Zenyatta: discord amplifies team damage, no mobility means careful positioning."""

HERO = {
    "role": "support",
    "difficulty": "medium",
    "win_condition": "Discord the tank, Orb of Harmony on your most pressured teammate. Your damage output matters as much as your healing.",
    "abilities": {
        "transcendence": {
            "optimal_use": [
                "When your team is grouped and taking a burst damage ult (RIP-Tire, Barrage, etc.).",
                "When your tank is about to die in a critical fight.",
            ],
            "common_mistakes": [
                "Using it early before the enemy ult lands.",
                "Using it when your team is already dead.",
                "Holding it all game. Zen's ult has low charge cost. Use it more.",
            ],
            "held_too_long_threshold": 45,
        },
        "orb_of_discord": {
            "optimal_use": [
                "Always on the tank to amplify your team's damage.",
                "Switch to supports when your team is diving them.",
            ],
            "common_mistakes": [
                "Leaving discord on a dead enemy.",
                "Not switching discord when the priority target changes.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "You have no mobility. Stay behind cover.",
            "High ground gives you sightlines for both orbs and damage.",
            "Never stand in the open. You will die.",
        ],
        "common_positioning_mistakes": [
            "Following a Lucio speed boost into open ground.",
            "Staying static when enemy Widowmaker has angles on you.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Your tank is pressuring and discord is sticking.",
            "You have line of sight and a Mercy or Lucio nearby for protection.",
        ],
        "when_not_to_fight": [
            "Enemy dive is healthy and targeting you.",
            "No cover within 3 steps.",
        ],
    },
}

MATCHUPS = {
    "winston": {"difficulty": "very_hard", "key_threat": "Bubble + jump dive isolates you.",
                "advice": ["Stay near cover so leap angle is blocked.", "Discord Winston the second he commits."]},
    "tracer": {"difficulty": "very_hard", "key_threat": "Blinks past your shots, pulse bomb one-shots.",
               "advice": ["Don't stand in the open. Hide behind your tank.", "Volley two charged orbs the moment she blinks in."]},
    "genji": {"difficulty": "hard", "key_threat": "Dragonblade kills you in one slash.",
              "advice": ["Trans on blade if your team is grouped.", "Discord Genji to amplify your team's kill speed."]},
    "sombra": {"difficulty": "hard", "key_threat": "Hack removes discord and trans.",
               "advice": ["Position with a teammate between you and likely Sombra angles."]},
    "reinhardt": {"difficulty": "easy", "key_threat": "Shatter wipes if you stand in open ground.",
                  "advice": ["Discord Rein for massive amplification.", "High ground keeps shatter from reaching you."]},
    "moira": {"difficulty": "medium", "key_threat": "Beam shreds you in melee range.",
              "advice": ["Volley orbs from max range.", "Discord her tank to force her to peel."]},
}

SYNERGIES = {
    "reinhardt": {"rating": "A", "win_condition": "Discord Rein behind shield = team wipe.",
                  "coordination": ["Discord their main tank constantly.", "Stay behind Rein shield."]},
    "ana": {"rating": "S", "win_condition": "Discord + anti = instant tank kill.",
            "coordination": ["Discord priority target Ana is shooting.", "Trans the moment ana is dived."]},
    "lucio": {"rating": "A", "win_condition": "Speed amplifies your kiting + boop synergy.",
              "coordination": ["Position with Lucio peel.", "Trans + sound barrier counters big ults."]},
    "winston": {"rating": "S", "win_condition": "Discord on the dove target ends fights in 2 seconds.",
                "coordination": ["Discord Winston jumps to.", "Trans when Winston commits without escape."]},
}
