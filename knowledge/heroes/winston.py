"""Winston: dive anchor, bubble denies space, jump pack isolates picks."""

HERO = {
    "role": "tank",
    "difficulty": "medium",
    "win_condition": "Dive an isolated support, escape with jump pack. You enable a flank DPS more than you brawl.",
    "abilities": {
        "primal_rage": {
            "optimal_use": [
                "When team is committed and you need to finish their squishies.",
                "To escape after engaging in unwinnable position.",
                "To deny a key enemy ult by booping the user out of position.",
            ],
            "common_mistakes": [
                "Using to engage with no team follow-up.",
                "Using offensively from full health when you don't need the HP boost.",
                "Failing to boop the enemy support into your team.",
            ],
            "held_too_long_threshold": 35,
        },
        "barrier_projector": {
            "optimal_use": [
                "Drop on yourself after leap to deny burst damage.",
                "Bubble a teammate getting focused while you reposition.",
                "Use it AS you leap so you land already protected.",
            ],
            "common_mistakes": [
                "Bubble used early before you commit. It expires before the fight.",
                "Bubble on the wrong target. Should be on the one taking damage right now.",
            ],
        },
        "jump_pack": {
            "optimal_use": [
                "Engage isolated support from off-angle.",
                "Disengage when down to 30 percent and team is dead.",
                "Boop an enemy off ledges (Lijiang, Ilios).",
            ],
            "common_mistakes": [
                "Leaping into the entire enemy team alone.",
                "Leaping with no escape after target dies.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Look for the enemy support who is one step out of position.",
            "Always plan your jump back before you commit.",
            "High ground gives you better leap angles.",
        ],
        "common_positioning_mistakes": [
            "Diving into a 1v5 because no one followed.",
            "Failing to reset between fights, dying with no jump pack.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Their support is alone or low.",
            "Your DPS is ready to dive with you.",
        ],
        "when_not_to_fight": [
            "Enemy has Brig + Cass + Sombra (anti-dive).",
            "Your team is regrouping and can't follow.",
        ],
    },
}

MATCHUPS = {
    "reaper": {"difficulty": "very_hard", "key_threat": "Shotguns shred you while you channel beam.",
               "advice": ["Don't dive a Reaper holding cooldowns.", "Bubble offensively or disengage."]},
    "brigitte": {"difficulty": "very_hard", "key_threat": "Stuns and whip shot deny your dives.",
                 "advice": ["Don't dive Brig directly. Bait her cooldowns first.", "Target the OTHER support."]},
    "sombra": {"difficulty": "very_hard", "key_threat": "Hack disables jump and bubble mid-dive.",
               "advice": ["Pre-jump before hack lands.", "Bubble through hack windows for survival."]},
    "zarya": {"difficulty": "hard", "key_threat": "Bubble feeds her charge while you beam her.",
              "advice": ["Don't beam Zarya bubbles.", "Pick a different angle target."]},
    "tracer": {"difficulty": "medium", "key_threat": "Out-mobiles you in 1v1.",
               "advice": ["Bubble and AOE her at melee range.", "Don't chase. Return to your team."]},
    "ana": {"difficulty": "easy", "key_threat": "Sleep dart stops your dive cold.",
            "advice": ["Bubble Ana sleep angle.", "Dive Ana when her sleep is on cooldown."]},
}

SYNERGIES = {
    "tracer": {"rating": "S", "win_condition": "Classic dive duo. Winston bubbles, Tracer finishes.",
               "coordination": ["Engage together.", "Pulse stick to seal kills Winston started."]},
    "genji": {"rating": "S", "win_condition": "Both dive, both escape; supports get isolated.",
              "coordination": ["Coordinate dash + jump timing.", "Blade after Winston commits."]},
    "kiriko": {"rating": "S", "win_condition": "TP cleanse and suzu enable aggressive dives.",
               "coordination": ["Suzu Winston anti-nade.", "TP to Winston when bubbled mid-fight."]},
    "lucio": {"rating": "A", "win_condition": "Speed amplifies dive entry and exit.",
              "coordination": ["Speed amp on commit.", "Sound barrier the dive."]},
}
