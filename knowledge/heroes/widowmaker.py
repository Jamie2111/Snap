"""Widowmaker: pick supports before fights begin, change angles every 2-3 shots."""

HERO = {
    "role": "dps",
    "difficulty": "very_high",
    "win_condition": "Pick the enemy support before fights start. One pick before a fight begins is worth three kills during it.",
    "abilities": {
        "infra_sight": {
            "optimal_use": [
                "When your team is about to push and needs wallhack information.",
                "To find hiding supports before a fight.",
            ],
            "common_mistakes": [
                "Using it during a fight instead of before one.",
                "Holding it. It's a short cooldown. Use it freely.",
            ],
            "held_too_long_threshold": 20,
        },
        "grappling_hook": {
            "optimal_use": [
                "Reach high ground positions enemies can't easily contest.",
                "Escape after a pick when enemies rush you.",
            ],
            "common_mistakes": [
                "Grappling into a fight instead of away from one.",
                "Not having an escape grapple planned before taking a shot.",
            ],
        },
        "venom_mine": {
            "optimal_use": [
                "Cover a flank route enemies use to reach you.",
                "On a doorway to alert you to flankers.",
            ],
            "common_mistakes": [
                "Throwing on the floor in the open. It gets shot.",
                "Not replacing it on cooldown.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "You need sightlines, not proximity.",
            "Change positions after every 2 to 3 shots. Enemies will find you.",
            "Your off-angle should let you see their supports without being seen by their tank.",
        ],
        "common_positioning_mistakes": [
            "Holding the same angle for a whole fight.",
            "Scoping in long enough for the enemy hitscan to lock on.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Enemy support is in your sightline with no cover.",
            "Your team is pushing and you can provide info plus picks.",
        ],
        "when_not_to_fight": [
            "Enemy dive is hunting you. Disengage to a safer angle.",
            "You have no escape grapple ready.",
        ],
    },
}

MATCHUPS = {
    "tracer": {"difficulty": "very_hard", "key_threat": "Closes distance in 2 seconds.",
               "advice": ["Always have grapple ready before scoping.", "Don't hold the same angle. Reposition each shot."]},
    "genji": {"difficulty": "very_hard", "key_threat": "Climbs to your angle and dashes through your team.",
              "advice": ["Stay where Genji can't climb to without exposing himself.", "If Genji starts climbing your angle, leave immediately."]},
    "sombra": {"difficulty": "very_hard", "key_threat": "Hack removes your grapple escape.",
               "advice": ["Take angles with a teammate covering Sombra's likely route."]},
    "winston": {"difficulty": "hard", "key_threat": "Bubbles you on high ground and isolates.",
                "advice": ["If Winston commits, grapple to a different angle and reset."]},
    "pharah": {"difficulty": "medium", "key_threat": "Aerial threat your team can't always deal with.",
               "advice": ["Prioritize Pharah picks. Two shots usually kill."]},
    "mercy": {"difficulty": "easy", "key_threat": "Pocketed enemy DPS gets stronger.",
              "advice": ["Kill Mercy first if she pockets a high-impact DPS."]},
}

SYNERGIES = {
    "ana": {"rating": "S", "win_condition": "Picks before engages, anti seals the deal.",
            "coordination": ["Call your shot timing for ana to anti the followup.", "Nano you for sustained damage on Infra-sight."]},
    "mercy": {"rating": "A", "win_condition": "Damage-boosted body shots one-shot squishies.",
              "coordination": ["Communicate your scope so Mercy pre-boosts.", "GA chain off you for repositioning."]},
    "reinhardt": {"rating": "B", "win_condition": "Shield gives you safe high ground angles.",
                  "coordination": ["Shoot from behind Rein's shield.", "Reposition when shield drops."]},
    "kiriko": {"rating": "A", "win_condition": "Kitsune lets you spam shots and reload faster.",
               "coordination": ["Position high during Kitsune.", "Suzu you when dove."]},
}
