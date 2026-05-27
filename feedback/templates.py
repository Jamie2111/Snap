"""Text templates for feedback generation. Centralized so tone tweaks are
one-file edits."""

CRITICAL_DIED_HOLDING_ULT = (
    "Died with ult at {pct:.0%} charge. "
    "{hero_note}"
)

CRITICAL_DIED_HOLDING_COOLDOWNS = (
    "Died with {abilities} available. "
    "Cooldowns are insurance against bad fights. Use the weakest one to confirm engages."
)

CRITICAL_HARD_COUNTER_DEATHS = (
    "You died to {enemy} {count} times. "
    "{enemy} is your hardest matchup on {hero}. {threat}"
)

IMPROVEMENT_ULT_HOLD = (
    "Ult hold time {trend}. Average {current:.1f}s this session "
    "vs {prior:.1f}s previously."
)

IMPROVEMENT_FIGHT_SURVIVAL = (
    "Fight survival rate {trend}. {current:.0%} this session vs {prior:.0%} previously."
)

INSIGHT_COMP_MISMATCH = (
    "Your team ran {comp} comp, but {hero} is a mismatch for {comp}. "
    "{principle}"
)

INSIGHT_PRESSURE_TILT = (
    "Your deaths cluster after early-game losses. "
    "The data suggests aggression spikes after dying. Reset mentally between deaths."
)

INSIGHT_FIRST_SESSION = (
    "This is your first tracked session. Future feedback will get sharper as Snap "
    "builds a model of your specific play. Patterns surface around session 5."
)

FOCUS_PERSISTENT = (
    "{mistake_label}. This has been your top issue for {sessions} sessions running "
    "and is not improving. Single highest priority."
)

FOCUS_FRESH = (
    "{mistake_label}. Highest-impact issue from this session."
)

PROGRESS_PATTERN_IMPROVING = (
    "{mistake_label} is improving across recent sessions. Keep the same approach."
)

PROGRESS_NONE = "No prior data to compare against."

WIN_CONDITION_BY_COMP = {
    "dive": "Coordinated cooldown burns on isolated supports. Commit and escape together.",
    "brawl": "Shield uptime, group movement, slow push to choke control.",
    "poke": "Hold long sightlines, force their team to engage uphill.",
    "anti_dive": "Layer peel so divers cannot isolate your backline. Punish commitment then push.",
    "rush": "Group up and push together with speed + sustain. Chain ults to deny resets.",
    "hold": "Defensive setup. Force the enemy into your sightlines. Stall to extend the round.",
    "bunker": "Concentrated fortified position. Force teamfights into your zone of control.",
    "pirate_ship": "Mobile fortified payload push.",
    "hybrid": "Adapt fight by fight. Read the enemy comp first.",
}
