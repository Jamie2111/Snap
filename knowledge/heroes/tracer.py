"""Tracer: flanker, pick supports, escape with recall."""

HERO = {
    "role": "dps",
    "difficulty": "high",
    "win_condition": "Pick isolated supports and escape. You win by getting 2 to 3 picks per fight, not by brawling with the whole team.",
    "abilities": {
        "pulse_bomb": {
            "optimal_use": [
                "Stuck to an isolated support with no escape.",
                "Enemy using a channeled ult (sound barrier, etc.).",
                "Stuck to a tank that is separated from their team.",
            ],
            "common_mistakes": [
                "Holding too long waiting for a perfect moment that never comes. Good is better than perfect.",
                "Throwing at tanks who can walk away or have self-healing to survive it.",
                "Using while Recalled. Save Recall as your escape after the ult lands.",
                "Using when low health with no escape. You die before it detonates.",
            ],
            "timing_threshold_seconds": 5,
            "held_too_long_threshold": 8,
            "feedback_templates": {
                "held_too_long": "You had pulse bomb for {duration:.1f}s before using or dying. Tracer's window is 3 to 5 seconds after getting position. After that the enemy resets.",
                "died_holding": "You died with pulse bomb at {pct:.0%} charge. At that charge level you could have used it in the fight you just lost.",
            },
        },
        "blink": {
            "optimal_use": [
                "Approach from unexpected angles. Never blink straight at an enemy.",
                "Blink toward cover when low, not toward enemies.",
                "Save one charge minimum when in a fight.",
            ],
            "common_mistakes": [
                "Using all 3 charges on engage with no escape route.",
                "Blinking in straight lines enemies can predict.",
                "Not tracking blink cooldown during fights.",
            ],
        },
        "recall": {
            "optimal_use": [
                "Taking burst damage above 60 percent of your health.",
                "After landing pulse bomb to escape.",
                "When repositioning has failed and you need a reset.",
            ],
            "common_mistakes": [
                "Using aggressively to re-engage. It's an escape.",
                "Not using it when about to die.",
                "Using when blinks are available. Blinks are faster.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Your flank angle must isolate one target. If you can see more than 2 enemies, you're too exposed.",
            "Always identify your escape route before engaging.",
            "High ground is not your friend. You need cover, not height.",
            "Stay at blink range from your target, not melee range.",
        ],
        "common_positioning_mistakes": [
            "Fighting in the open with no cover nearby.",
            "Engaging the tank first instead of going around.",
            "Staying in the backline too long. In and out quickly.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Enemy support is isolated or out of position.",
            "Enemy tank is using cooldowns on your team.",
            "Your team is winning a fight and diverting attention.",
        ],
        "when_not_to_fight": [
            "Enemy has area denial ults (Zarya, Graviton, etc.).",
            "You're below 60 percent health with no Recall.",
            "Enemy team is stacked and watching flanks.",
        ],
    },
}

MATCHUPS = {
    "brigitte": {
        "difficulty": "very_hard",
        "key_threat": "Whip shot two-shots you, shield bash stuns and chains a melee combo.",
        "advice": [
            "Don't engage at below 60 percent health. You have zero margin against Brig.",
            "Stay outside whip-shot range. Kite with blinks rather than dueling.",
            "If Brig commits to you, recall away. Don't try to trade.",
        ],
    },
    "sombra": {
        "difficulty": "hard",
        "key_threat": "Hack disables blinks and recall.",
        "advice": [
            "Always know where Sombra is before committing.",
            "Don't blink to engage if Sombra has not been visible for 6+ seconds.",
            "Recall is your panic button. Don't use it before the hack lands.",
        ],
    },
    "cassidy": {
        "difficulty": "hard",
        "key_threat": "Magnetic grenade auto-locks and bursts you with one fan.",
        "advice": [
            "Stay outside mag-grenade range when in line of sight.",
            "Use buildings to break grenade tracking.",
            "Never duel Cassidy in the open at any health.",
        ],
    },
    "winston": {
        "difficulty": "medium",
        "key_threat": "Bubble denies your damage, lightning chews you instantly.",
        "advice": [
            "Don't fight inside the bubble. Wait for it to expire.",
            "If Winston dives your backline you can chip him from behind, then peel back to support.",
        ],
    },
    "moira": {
        "difficulty": "easy",
        "key_threat": "Fade saves her from one death, beam outputs serious sustain.",
        "advice": [
            "Bait fade with a blink-in, then disengage to reload.",
            "Re-engage after fade is spent. She is helpless without it.",
        ],
    },
    "zenyatta": {
        "difficulty": "easy",
        "key_threat": "Discord on you melts you fast if hit.",
        "advice": [
            "Force discord by showing yourself, then disengage so the discord follows you, not your tank.",
            "Zen has no mobility. Pulse bomb on him almost always lands.",
        ],
    },
}

SYNERGIES = {
    "ana": {"rating": "S", "win_condition": "Anti-nade their support, you secure the pick.",
            "coordination": ["Time engages with Ana sleep on their tank.",
                             "Call for nano when you have pulse ready."]},
    "lucio": {"rating": "A", "win_condition": "Speed boost into a flank, sound barrier on your engage.",
              "coordination": ["Wall ride together for unexpected angles.", "Lucio boops support into your kill range."]},
    "kiriko": {"rating": "A", "win_condition": "Suzu cleanses anti so you can dive without setup.",
               "coordination": ["TP target priority: you, when you're caught.", "Kunai picks chain with your damage."]},
    "winston": {"rating": "S", "win_condition": "Dive comp: Winston bubbles support, you finish.",
                "coordination": ["Commit on his leap, not before.", "Bait their cooldowns first, then dive together."]},
}
