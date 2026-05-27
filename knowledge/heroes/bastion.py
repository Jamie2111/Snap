"""Bastion: high DPS in configuration, mobile in recon, Artillery for zoning."""

HERO = {
    "role": "dps",
    "difficulty": "low",
    "win_condition": "Configuration form melts tanks. Mobile recon for repositioning. Artillery zones enemies.",
    "abilities": {
        "configuration_artillery": {
            "optimal_use": [
                "On grouped enemies with no escape.",
                "Combo with grav or shatter.",
                "Stall objective from safe angle.",
            ],
            "common_mistakes": [
                "Artillery without team follow-up.",
                "Casting in open sightline.",
            ],
            "held_too_long_threshold": 40,
        },
        "configuration_assault": {
            "optimal_use": [
                "Burst tank or grouped enemies.",
                "Combo with team setup (bubble, suzu, Bap).",
                "Defend objective from siege.",
            ],
            "common_mistakes": [
                "Config in open ground.",
                "Config without support.",
            ],
        },
        "a36_tactical_grenade": {
            "optimal_use": [
                "Cluster damage on chokepoint.",
                "Boop diver away.",
                "Confirm kill on low HP.",
            ],
            "common_mistakes": [
                "Wasted long range.",
                "Forgetting on cooldown.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Cover for config.",
            "Behind tank or shield.",
            "High ground in recon form.",
        ],
        "common_positioning_mistakes": [
            "Config in open ground.",
            "Config without team peel.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Support and tank holding for you.",
            "Enemy committed at choke.",
        ],
        "when_not_to_fight": [
            "Sombra healthy.",
            "Dive comp targeting you.",
        ],
    },
}

MATCHUPS = {
    "sombra": {"difficulty": "very_hard", "key_threat": "Hack ends config.",
               "advice": ["Stay near walls.", "Don't config without Sombra info."]},
    "genji": {"difficulty": "hard", "key_threat": "Deflect returns config rounds.",
              "advice": ["Don't config Genji deflect.", "Tactical grenade post-deflect."]},
    "reinhardt": {"difficulty": "easy", "key_threat": "Pin disrupts config.",
                  "advice": ["Config from behind your tank.", "Tactical grenade Rein post-pin."]},
    "tracer": {"difficulty": "medium", "key_threat": "Picks you in recon.",
               "advice": ["Tactical grenade Tracer.", "Config when she's not on you."]},
    "ana": {"difficulty": "medium", "key_threat": "Anti melts config.",
            "advice": ["Don't config anti-naded.", "Config when Ana sleep used."]},
    "zarya": {"difficulty": "hard", "key_threat": "Bubble denies config.",
              "advice": ["Don't config bubbled.", "Tactical grenade past bubble."]},
}

SYNERGIES = {
    "orisa": {"rating": "S", "win_condition": "Pirate ship: Orisa front, Bastion bursts.",
              "coordination": ["Fortify on Bastion config.", "Surge during Bastion ult."]},
    "baptiste": {"rating": "S", "win_condition": "Amp matrix doubles Bastion damage.",
                 "coordination": ["Amp matrix Bastion config.", "Immortality during config."]},
    "mercy": {"rating": "S", "win_condition": "Pocketed Bastion shreds.",
              "coordination": ["Damage boost config.", "Stay behind Bastion."]},
    "ana": {"rating": "A", "win_condition": "Anti + Bastion config = team wipe.",
            "coordination": ["Anti the config target.", "Nano Bastion."]},
}
