"""Lucio: speed boost dictates fight pace, sound barrier wins rounds outright."""

HERO = {
    "role": "support",
    "difficulty": "high",
    "win_condition": "Speed boost your team onto objectives and out of danger. Sound barrier at the right moment wins rounds outright.",
    "abilities": {
        "sound_barrier": {
            "optimal_use": [
                "When you see an enemy ult cast beginning. Sound Barrier counters most damage ults.",
                "Before your team commits to a high-ground push.",
                "When your team is grouped and about to take burst damage.",
            ],
            "common_mistakes": [
                "Using reactively after your team is already dead.",
                "Using when your team is spread out. The shields are wasted.",
                "Holding it all game waiting for the perfect moment.",
            ],
            "timing_threshold_seconds": 30,
            "held_too_long_threshold": 60,
        },
        "amp_it_up": {
            "optimal_use": [
                "Speed boost on attack to create momentum.",
                "Heal boost when a teammate is taking burst damage.",
                "Speed boost to escape a lost fight.",
            ],
            "common_mistakes": [
                "Staying on heal aura when not in danger. Speed aura creates more value in most situations.",
                "Not using amp during critical moments.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "You need to be near your team to affect them. Don't roam alone.",
            "Wall ride to stay mobile and hard to hit.",
            "Position to boop enemies off high ground or into your team's damage.",
        ],
        "common_positioning_mistakes": [
            "Wall riding into enemy sightlines without cover.",
            "Pushing solo into the enemy team without a way out.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Your team has speed and momentum.",
            "Enemy is grouped and a sound barrier can swing the fight.",
        ],
        "when_not_to_fight": [
            "Your team is fractured. Pull back, group, then push.",
            "You're alone and enemy DPS has line of sight.",
        ],
    },
}

MATCHUPS = {
    "junkrat": {"difficulty": "hard", "key_threat": "Spam denies wall riding lanes; trap punishes mobility.",
                "advice": ["Switch to heal aura when in spam zones.", "Wall ride only when actively closing or escaping."]},
    "sombra": {"difficulty": "hard", "key_threat": "Hack disables wall ride.",
               "advice": ["Stay near walls and corners she can't watch.", "Boop her off ledges or into your team."]},
    "pharah": {"difficulty": "medium", "key_threat": "Aerial threat your team can't always hit.",
               "advice": ["Boop Pharah when she lands or rocket-jumps low.", "Heal aura up when Pharah barrage is incoming if sound barrier is unavailable."]},
    "winston": {"difficulty": "medium", "key_threat": "Dives your backline and isolates you.",
                "advice": ["Boop Winston off ledges or onto a chokepoint.", "Wall ride to disengage when bubbled."]},
    "reinhardt": {"difficulty": "easy", "key_threat": "Shatter still wipes if your team is grouped low.",
                  "advice": ["Sound barrier counters shatter if both teams are committed.", "Speed boost into off-angles around the shield."]},
    "zarya": {"difficulty": "medium", "key_threat": "Bubbles deny your damage, graviton enables ult combos.",
              "advice": ["Sound barrier the team when grav is incoming.", "Don't shoot bubbles. You give her free charge."]},
}

SYNERGIES = {
    "reinhardt": {"rating": "S", "win_condition": "Speed boost the brawl, sound barrier the engage.",
                  "coordination": ["Speed Rein onto choke for shatter angles.", "Sound barrier the moment shatter or shield-break occurs."]},
    "winston": {"rating": "A", "win_condition": "Speed dive, sound barrier dive escape.",
                "coordination": ["Boost Winston into their backline.", "Sound barrier when Winston commits without bubble."]},
    "junkerqueen": {"rating": "A", "win_condition": "Brawl with constant speed and sustain.",
                    "coordination": ["Speed when JQ commands.", "Heal aura the moment Adrenaline rush ends."]},
    "tracer": {"rating": "A", "win_condition": "Speed flank, sound barrier the team commit.",
               "coordination": ["Boost Tracer into the flank angle.", "Sound barrier just as Tracer pulses."]},
}
