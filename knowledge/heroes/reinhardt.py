"""Reinhardt: shield-led brawl tank, Earthshatter wins teamfights when grouped."""

HERO = {
    "role": "tank",
    "difficulty": "medium",
    "win_condition": "Create space for your team with your shield and win brawls with Earthshatter. Your team plays behind you. You set the pace of every fight.",
    "abilities": {
        "earthshatter": {
            "optimal_use": [
                "When 3 or more enemies are grouped with no cover.",
                "After a Zarya Graviton Surge to guarantee kills.",
                "When the enemy team is distracted or pushing.",
            ],
            "common_mistakes": [
                "Using through barriers that block it.",
                "Using when enemies are spread out.",
                "Not communicating it to your team beforehand.",
            ],
            "held_too_long_threshold": 30,
        },
        "barrier_field": {
            "optimal_use": [
                "Hold barrier up when your team needs cover.",
                "Drop barrier to charge or use abilities, then re-raise.",
            ],
            "common_mistakes": [
                "Holding barrier up until it breaks. Manage its health.",
                "Turning your back to protect a flank. You lose sightlines.",
            ],
        },
        "charge": {
            "optimal_use": [
                "Pin a squishy into a wall for a guaranteed kill.",
                "Disrupt an enemy ult cast (Cass deadeye, Bastion config).",
            ],
            "common_mistakes": [
                "Charging into the enemy team alone. You die after the pin.",
                "Charging when your team isn't ready to follow up.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "You should be the first thing enemies see.",
            "Angle your shield to protect your supports, not just yourself.",
            "Choke points are your friend. Force the enemy to come to you.",
        ],
        "common_positioning_mistakes": [
            "Charging through the line of sight of your supports. They cannot heal you.",
            "Walking past cover into open ground.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Your supports have ult or healing cooldowns ready.",
            "You can shatter or pin in the next 5 seconds.",
        ],
        "when_not_to_fight": [
            "Shield is sub-30 percent and supports are out of position.",
            "Enemy has anti-shield (Sigma, Sombra hack, anti-grenade).",
        ],
    },
}

MATCHUPS = {
    "sigma": {"difficulty": "very_hard", "key_threat": "Range and shield uptime out-poke you, accretion stuns shatter setups.",
              "advice": ["Force chokepoints he can't poke through.", "Bait accretion before charging or shattering."]},
    "orisa": {"difficulty": "hard", "key_threat": "Javelin throw stuns, fortify negates pin and shatter.",
              "advice": ["Pin only when fortify is on cooldown.", "Save shatter for a moment Orisa is fortified out (you can't shatter through it)."]},
    "pharah": {"difficulty": "hard", "key_threat": "Aerial poke through your shield.",
               "advice": ["Don't extend with a shield she's chipping. Wait for hitscan to deal with her."]},
    "zarya": {"difficulty": "medium", "key_threat": "Bubbles deny shatter and pin damage.",
              "advice": ["Don't pin a bubbled target. You waste the cooldown.", "Shatter after both Zarya bubbles are gone."]},
    "ana": {"difficulty": "hard", "key_threat": "Sleep dart cancels shatter, anti-nade melts you.",
            "advice": ["Don't shatter in Ana sightlines without team peel.", "Bait the sleep with a fake shatter cancel."]},
    "winston": {"difficulty": "easy", "key_threat": "Bubble can block your fire-strike.",
                "advice": ["Force Winston to drop bubble early, then commit.", "Pin into terrain if he leaps in alone."]},
}

SYNERGIES = {
    "lucio": {"rating": "S", "win_condition": "Speed your brawl into shatter range.",
              "coordination": ["Push when Lucio amps speed.", "Sound barrier the shatter."]},
    "zarya": {"rating": "S", "win_condition": "Bubble Rein on shatter cast, graviton+shatter wipes.",
              "coordination": ["Bubble Rein when ana sleep is up.", "Coordinate grav+shatter timing."]},
    "ana": {"rating": "S", "win_condition": "Nano shatter is the strongest tank ult combo.",
            "coordination": ["Hold shatter until Ana has nano.", "Anti-nade their backline as you shatter."]},
    "kiriko": {"rating": "S", "win_condition": "Suzu cleanses anti on shatter; Kitsune amplifies brawl.",
               "coordination": ["Suzu Rein when anti-nade lands.", "Push during Kitsune Rush."]},
}
