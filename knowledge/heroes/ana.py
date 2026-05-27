"""Ana: anti-heal and sleep darts win team fights more than her healing output."""

HERO = {
    "role": "support",
    "difficulty": "very_high",
    "win_condition": "Keep your tank alive through every fight. Your sleep dart and anti-heal win or lose team fights more than your healing output.",
    "abilities": {
        "sleep_dart": {
            "optimal_use": [
                "Canceling an enemy ult mid-cast.",
                "Stopping a diver that is about to kill your tank.",
                "Isolating a flanker targeting you or your team.",
                "Buying time when your team is regrouping.",
            ],
            "common_mistakes": [
                "Sleeping enemies your team isn't focusing. They just wake up and fight again.",
                "Panic sleeping the first threat instead of waiting for the highest-value target.",
                "Missing because you rushed. Take 0.5s to aim.",
                "Using when Nano or Grenade would win the fight faster.",
            ],
            "timing_threshold_seconds": 8,
            "held_too_long_threshold": 15,
            "feedback_templates": {
                "held_too_long": "Sleep dart was available for {duration:.1f}s. Ana's sleep wins fights. It shouldn't sit unused for more than 10 to 12 seconds in an active fight.",
                "died_holding": "You died with sleep dart available. In the fight before your death, sleep dart on the target killing you would likely have changed the outcome.",
            },
        },
        "biotic_grenade": {
            "optimal_use": [
                "On your tank during heavy burst damage.",
                "On a grouped enemy cluster to anti-heal.",
                "To deny a Lucio or Moira from healing during a fight.",
                "To secure a kill on a low health enemy.",
            ],
            "common_mistakes": [
                "Saving grenade instead of using it on cooldown.",
                "Using on one enemy instead of a cluster.",
                "Not using it on yourself when being dived.",
            ],
        },
        "nano_boost": {
            "optimal_use": [
                "On a tank or DPS that is already mid-fight and winning. Amplify a winning position.",
                "To counter an enemy ult that your team can't avoid.",
                "Coordinated with your tank's ult (Nano-Blade, Nano-Shatter, etc.).",
            ],
            "common_mistakes": [
                "Nanoing into a lost fight hoping to turn it.",
                "Nanoing a player who is out of position.",
                "Holding nano too long waiting for the perfect combo. A good nano now beats a perfect nano never.",
                "Nanoing without communicating to the target.",
            ],
            "timing_threshold_seconds": 20,
            "held_too_long_threshold": 40,
        },
    },
    "positioning": {
        "principles": [
            "You should be able to see your tank at all times.",
            "High ground gives you sightlines and safety. Use it.",
            "Stay behind your tank, not beside them.",
            "Always have a wall or corner within one step.",
        ],
        "common_positioning_mistakes": [
            "Standing in the open within the enemy DPS line of sight.",
            "Following your tank into the enemy team instead of holding back.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Your tank initiated and is winning.",
            "Your team has key ults available and theirs do not.",
        ],
        "when_not_to_fight": [
            "Dived without escape. Save sleep for self-defense, not engage.",
            "Tank is dead. The fight is already lost.",
        ],
    },
}

MATCHUPS = {
    "winston": {
        "difficulty": "very_hard",
        "key_threat": "Bubble blocks sleep, leap closes distance instantly, beam shreds you.",
        "advice": [
            "Pre-position near cover. Always have a wall within one step.",
            "Sleep him as he leaps, not after he lands.",
            "Anti-nade yourself when bubbled if you can't get the sleep.",
        ],
    },
    "tracer": {
        "difficulty": "very_hard",
        "key_threat": "Blink mobility makes sleep darts miss, pulse bomb one-shots you.",
        "advice": [
            "Anti-nade yourself when she engages. Removes her pulse-bomb-kill threat.",
            "Don't try to lead sleep on a blinking Tracer. Wait for her to commit.",
            "Stay close to your team and a wall.",
        ],
    },
    "genji": {
        "difficulty": "hard",
        "key_threat": "Dash + deflect punishes both your sleep and your nade.",
        "advice": [
            "Don't sleep into deflect. Wait for him to deflect first, then sleep.",
            "Aim slightly off-center to bait dash, then re-aim.",
        ],
    },
    "sombra": {
        "difficulty": "hard",
        "key_threat": "Hack disables sleep dart and nade.",
        "advice": [
            "Position with line of sight on flanks she might come from.",
            "Anti-nade her on hack cast to interrupt.",
        ],
    },
    "doomfist": {
        "difficulty": "medium",
        "key_threat": "Slam and rocket punch instantly close distance.",
        "advice": [
            "Sleep him mid-slam or mid-punch. The cast is long enough.",
            "Don't stand next to walls he can pin you against.",
        ],
    },
    "reinhardt": {
        "difficulty": "easy",
        "key_threat": "Shatter wipes your team if you don't sleep it.",
        "advice": [
            "Sleep dart on shatter cast is your single highest-leverage shot.",
            "Discord-anti combo on Rein melts him through the shield's downtime.",
        ],
    },
}

SYNERGIES = {
    "reinhardt": {"rating": "S", "win_condition": "Nano shatter wins fights outright.",
                  "coordination": ["Call shatter timing so you nano on cast.", "Anti-nade their backline when Rein commits."]},
    "tracer": {"rating": "S", "win_condition": "Anti-nade their support so Tracer secures the pick.",
               "coordination": ["Anti the target Tracer dives.", "Nano Tracer for a pulse-bomb-guaranteed teamfight."]},
    "winston": {"rating": "A", "win_condition": "Nano dive comp: Winston jumps in nanoed, you cleanup.",
                "coordination": ["Sleep their peel target as Winston commits.", "Anti the squishy target Winston dives."]},
    "genji": {"rating": "S", "win_condition": "Nano-blade is one of the strongest combos in the game.",
              "coordination": ["Sleep their support before blade.", "Anti-nade the cluster Genji dives through."]},
}
