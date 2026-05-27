"""Mercy: pocket the highest-impact player, amplify their damage, resurrect to swing fights."""

HERO = {
    "role": "support",
    "difficulty": "medium",
    "win_condition": "Keep your best player alive and amplify their damage at the right moment. Your resurrect changes fights. Use it on the right target.",
    "abilities": {
        "valkyrie": {
            "optimal_use": [
                "When your team is winning a fight to amplify and finish it.",
                "When your team is spread and needs simultaneous healing.",
            ],
            "common_mistakes": [
                "Using defensively when your team is losing. It won't turn a lost fight.",
                "Holding too long.",
            ],
            "held_too_long_threshold": 45,
        },
        "resurrect": {
            "optimal_use": [
                "On your highest-impact player when it's safe.",
                "After the main fight is won and you have cover.",
            ],
            "common_mistakes": [
                "Ressing in an active fight. You and the rezzed player both die.",
                "Ressing a player in a bad position.",
                "Ressing a tank instead of a DPS when both are down.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Guardian Angel target should be your most mobile or highest-ground ally.",
            "Never be caught without a GA target nearby.",
            "Stay behind the fight, not in it.",
        ],
        "common_positioning_mistakes": [
            "Flying into the enemy team to res. You die too.",
            "Pocketing a player who is out of position.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Your DPS is winning a duel. Pocket and amplify.",
            "Your team has a power play after a pick.",
        ],
        "when_not_to_fight": [
            "Your DPS is dead. Disengage; don't pocket the tank uselessly.",
            "Enemy dive comp is targeting you. Stay near your team and group.",
        ],
    },
}

MATCHUPS = {
    "tracer": {"difficulty": "very_hard", "key_threat": "One-shots you with pulse if she gets close.",
               "advice": ["Never be without a Guardian Angel target.", "Position high so Tracer must commit blinks to reach you."]},
    "genji": {"difficulty": "very_hard", "key_threat": "Dash + blade kills you in one combo.",
              "advice": ["Stay grouped with a peel hero (Brig, Cass).", "Don't fly to a low ally in the open. You die together."]},
    "sombra": {"difficulty": "hard", "key_threat": "Hack disables GA, virus melts you.",
               "advice": ["Stay near walls so hack can't get LoS.", "Pre-emptive GA before hack cast."]},
    "widowmaker": {"difficulty": "hard", "key_threat": "One-shots you from any sightline.",
                   "advice": ["Use cover. Don't pocket a DPS in open ground.", "Be unpredictable with GA pathing."]},
    "reinhardt": {"difficulty": "easy", "key_threat": "Negligible. Stay behind shield.",
                  "advice": ["Pocket your tank or damage-boost the duel-winning DPS."]},
    "winston": {"difficulty": "medium", "key_threat": "Dive can isolate you in the backline.",
                "advice": ["Stick close to your team during Winston dives.", "GA to high ground when bubbled."]},
}

SYNERGIES = {
    "soldier76": {"rating": "S", "win_condition": "Pocketed Soldier outputs lethal sustained damage.",
                  "coordination": ["Damage boost during Tac Visor.", "Stay behind Soldier biotic field."]},
    "ashe": {"rating": "S", "win_condition": "Damage-boosted Ashe one-shots most squishies.",
             "coordination": ["Damage boost during scoped shots.", "Pocket Ashe high ground angles."]},
    "pharah": {"rating": "S", "win_condition": "Pharmercy: aerial control of the match.",
               "coordination": ["GA chain off Pharah at all times.", "Damage boost during Barrage."]},
    "reinhardt": {"rating": "B", "win_condition": "Pocket the tank for safe brawl extension.",
                  "coordination": ["Damage boost charged firestrike for snipes.", "GA from teammate to Rein when shield breaks."]},
}
