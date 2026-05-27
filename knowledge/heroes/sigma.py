"""Sigma: poke tank with shield, kinetic grasp, accretion stun. Hybrid threat at range."""

HERO = {
    "role": "tank",
    "difficulty": "high",
    "win_condition": "Out-poke at mid range, stun with accretion to set up team kills. Shield uptime is secondary to damage output.",
    "abilities": {
        "gravitic_flux": {
            "optimal_use": [
                "On 3 or more enemies grouped with no escape.",
                "Combo with Earthshatter, Graviton, or Blade for guaranteed kills.",
                "After enemy uses their key escape ult (e.g. Recall, Fade).",
            ],
            "common_mistakes": [
                "Using on single targets without followup.",
                "Lifting enemies into safety.",
                "Casting in line of sight of multiple sniper angles.",
            ],
            "held_too_long_threshold": 35,
        },
        "accretion": {
            "optimal_use": [
                "Stun a key target before your team focuses (Ana, Mercy).",
                "Cancel enemy ult cast (Cassidy deadeye, Bastion config).",
                "Confirm a kill on a low HP enemy.",
            ],
            "common_mistakes": [
                "Throwing into shields.",
                "Wasting on full HP tanks.",
                "Missing because target moved. Lead it.",
            ],
        },
        "kinetic_grasp": {
            "optimal_use": [
                "Absorb a major projectile (Hanzo storm arrows, Junkrat ult).",
                "Eat damage during enemy push to charge your shield.",
            ],
            "common_mistakes": [
                "Using preemptively against hitscan (it doesn't absorb beam).",
                "Wasting on tickle damage.",
            ],
        },
        "experimental_barrier": {
            "optimal_use": [
                "Block a key enemy ult cast (Soldier visor, Pharah barrage).",
                "Hold off a sniper angle for your supports.",
            ],
            "common_mistakes": [
                "Holding it constantly. Sigma damages best when shield is recharging.",
                "Placing barrier in a spot that blocks your own team's damage.",
            ],
        },
    },
    "positioning": {
        "principles": [
            "Mid range. Not melee, not sniper distance.",
            "Stay where you can shoot but enemy must commit to push you.",
            "Use your barrier to deny key angles, not to absorb all damage.",
        ],
        "common_positioning_mistakes": [
            "Walking into Rein's hammer range.",
            "Standing static while enemy hitscan locks in.",
        ],
    },
    "game_sense": {
        "when_to_fight": [
            "Long sightline maps where poke wins.",
            "Your team has Ana to anti the dive target.",
        ],
        "when_not_to_fight": [
            "Brawl comp on choke and you have no Ana.",
            "Enemy Sombra is healthy and hunting you.",
        ],
    },
}

MATCHUPS = {
    "reinhardt": {"difficulty": "easy", "key_threat": "Pin disrupts your aim.",
                  "advice": ["Kite back. Don't let Rein close.", "Accretion mid-pin if he goes for a teammate."]},
    "winston": {"difficulty": "hard", "key_threat": "Dives your backline while you're slow.",
                "advice": ["Accretion Winston as he leaps to deny dive.", "Barrier your support's angle, not yourself."]},
    "tracer": {"difficulty": "hard", "key_threat": "Hard to hit, picks your supports.",
               "advice": ["Don't chase Tracer. Accretion when she commits.", "Trust your team peel."]},
    "ana": {"difficulty": "medium", "key_threat": "Anti-nade burst kills you under focus.",
            "advice": ["Use kinetic grasp on incoming projectiles before fight.", "Don't extend past your team when anti-nade is up."]},
    "sombra": {"difficulty": "hard", "key_threat": "Hack stops accretion and barrier.",
               "advice": ["Stay near walls.", "Use kinetic grasp during hack to mitigate virus."]},
    "zarya": {"difficulty": "medium", "key_threat": "Bubble denies your damage.",
              "advice": ["Don't shoot bubbles.", "Accretion past her bubble onto her support."]},
}

SYNERGIES = {
    "ana": {"rating": "S", "win_condition": "Anti + accretion is a free pick.",
            "coordination": ["Sleep their dive target, accretion the support.", "Anti on grav for a 4-kill ult."]},
    "junkerqueen": {"rating": "A", "win_condition": "Brawl with poke threat behind.",
                    "coordination": ["JQ engages, Sigma covers escape.", "Grav + Rampage = team wipe."]},
    "ashe": {"rating": "S", "win_condition": "Two long-range threats force enemy team to split focus.",
             "coordination": ["Coordinate Coach Gun + accretion combo.", "Both poke same target."]},
    "baptiste": {"rating": "A", "win_condition": "Immortality field protects you during grav cast.",
                 "coordination": ["Cast grav inside Bap window.", "Bap amp your team's damage on grav cluster."]},
}
