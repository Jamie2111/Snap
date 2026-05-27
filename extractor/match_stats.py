"""Internal per-hero stat computation.

Snap computes stats internally from event data (cooldown transitions, ult
uses, deaths, fight outcomes) rather than OCR'ing the OW2 post-match
scoreboard. This is cleaner: stats are available in real-time, work on any
video that Snap can extract events from, and don't depend on the player
clicking through the post-match cards quickly.

Per-hero ability labels and benchmarks live in knowledge.hero_stats.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from extractor.events import SessionEvents
from knowledge.hero_stats import HERO_ABILITY_LABELS, benchmark_for


@dataclass
class StatLine:
    """One measured stat with its benchmark comparison."""
    label: str
    value: float
    unit: str = ""
    benchmark: Optional[float] = None
    tier: str = "diamond"
    lower_is_better: bool = False
    sample_size: int = 0           # raw count of observations (e.g. uses, deaths)
    enough_data: bool = True       # if False, benchmark comparison is suppressed

    @property
    def has_benchmark(self) -> bool:
        return self.benchmark is not None and self.enough_data

    @property
    def delta_pct(self) -> Optional[float]:
        """Percentage above/below the benchmark. None when sample is too small
        to be meaningful or no benchmark exists."""
        if not self.has_benchmark or self.benchmark == 0:
            return None
        return ((self.value - self.benchmark) / self.benchmark) * 100.0

    @property
    def status(self) -> str:
        """One of 'above', 'on_target', 'below', 'unknown'. 'unknown' covers
        the no-benchmark case AND the not-enough-data case."""
        if not self.has_benchmark:
            return "unknown"
        d = self.delta_pct or 0
        if self.lower_is_better:
            d = -d
        if d >= 15:
            return "above"
        if d <= -20:
            return "below"
        return "on_target"


# Minimum data required before benchmark comparison is meaningful.
# A 30-second session can't fairly compare Pulse Bomb uses to a 10-minute rate.
MIN_DURATION_FOR_ABILITY_BENCH = 120.0   # 2 min for slot-based ability usage
MIN_DURATION_FOR_ULT_BENCH     = 300.0   # 5 min for ult throughput
MIN_DURATION_FOR_SURVIVAL_BENCH = 180.0  # 3 min for deaths / survival rate
MIN_FIGHTS_FOR_SURVIVAL_BENCH = 3        # need real engagements to grade survival


@dataclass
class MatchStats:
    """All hero-specific stats Snap computed for one match."""
    hero: Optional[str]
    duration_seconds: float
    stats: list[StatLine] = field(default_factory=list)


def _per_10min(count: int, duration_seconds: float) -> float:
    if duration_seconds <= 0:
        return 0.0
    return (count / duration_seconds) * 600.0


def _slot_uses(events: SessionEvents, slot: str) -> int:
    """Count how many times an ability slot transitioned ready -> cooldown.
    The event detector records this in cooldown_hold_durations[slot]
    every time the slot was used (each hold ends with a use)."""
    holds = events.stats.cooldown_hold_durations.get(slot, [])
    return len(holds)


def compute_stats(hero: Optional[str], events: SessionEvents, duration_seconds: float, tier: str = "diamond") -> MatchStats:
    """Compute hero-specific stats from the match's event stream."""
    out = MatchStats(hero=hero, duration_seconds=duration_seconds)
    if not hero or duration_seconds <= 0:
        return out

    s = events.stats
    labels = HERO_ABILITY_LABELS.get(hero, {})

    # Ult metrics (apply to every hero)
    ult_label = labels.get("ult", "ult")
    ult_enough = duration_seconds >= MIN_DURATION_FOR_ULT_BENCH and s.ults_used > 0
    out.stats.append(StatLine(
        label=f"{ult_label.replace('_', ' ').title()} uses per 10 min",
        value=round(_per_10min(s.ults_used, duration_seconds), 2),
        unit="/10m",
        benchmark=benchmark_for(hero, "ult_uses_per_10min", tier),
        tier=tier,
        sample_size=s.ults_used,
        enough_data=ult_enough,
    ))
    if s.ult_hold_durations:
        avg_hold = sum(s.ult_hold_durations) / len(s.ult_hold_durations)
        out.stats.append(StatLine(
            label=f"{ult_label.replace('_', ' ').title()} hold time",
            value=round(avg_hold, 1),
            unit="s",
            benchmark=benchmark_for(hero, "ult_avg_hold_seconds", tier),
            tier=tier,
            lower_is_better=True,
            sample_size=len(s.ult_hold_durations),
            enough_data=len(s.ult_hold_durations) >= 2,
        ))

    # Per-ability-slot throughput
    for slot_key in ("slot1", "slot2", "slot3", "slot4"):
        label = labels.get(slot_key)
        if not label:
            continue
        slot_id = "ability_" + slot_key[-1]
        uses = _slot_uses(events, slot_id)
        bench = benchmark_for(hero, f"{slot_key}_uses_per_10min", tier)
        if uses == 0 and bench is None:
            continue
        out.stats.append(StatLine(
            label=f"{label.replace('_', ' ').title()} uses per 10 min",
            value=round(_per_10min(uses, duration_seconds), 1),
            unit="/10m",
            benchmark=bench,
            tier=tier,
            sample_size=uses,
            enough_data=(duration_seconds >= MIN_DURATION_FOR_ABILITY_BENCH and uses > 0),
        ))

    # Universal survival metrics
    out.stats.append(StatLine(
        label="Deaths per 10 min",
        value=round(_per_10min(s.deaths_total, duration_seconds), 2),
        unit="/10m",
        benchmark=benchmark_for(hero, "deaths_per_10min", tier),
        tier=tier,
        lower_is_better=True,
        sample_size=s.deaths_total,
        enough_data=(duration_seconds >= MIN_DURATION_FOR_SURVIVAL_BENCH and s.deaths_total > 0),
    ))
    if s.fights_engaged_total > 0:
        out.stats.append(StatLine(
            label="Fight survival rate",
            value=round(s.fight_survival_rate * 100, 1),
            unit="%",
            benchmark=(benchmark_for(hero, "fight_survival_rate", tier) or 0) * 100 or None,
            tier=tier,
            sample_size=s.fights_engaged_total,
            enough_data=s.fights_engaged_total >= MIN_FIGHTS_FOR_SURVIVAL_BENCH,
        ))

    return out


def aggregate(matches_stats: list[MatchStats]) -> MatchStats:
    """Roll multiple per-match MatchStats into one session-level rollup.
    Averages each named stat across matches."""

    if not matches_stats:
        return MatchStats(hero=None, duration_seconds=0)

    primary_hero = matches_stats[-1].hero
    total_seconds = sum(m.duration_seconds for m in matches_stats)
    out = MatchStats(hero=primary_hero, duration_seconds=total_seconds)

    # Gather all unique stat labels
    by_label: dict[str, list[StatLine]] = {}
    for m in matches_stats:
        for sl in m.stats:
            by_label.setdefault(sl.label, []).append(sl)

    for label, lines in by_label.items():
        values = [sl.value for sl in lines]
        if not values:
            continue
        first = lines[0]
        avg = sum(values) / len(values)
        out.stats.append(StatLine(
            label=label,
            value=round(avg, 2),
            unit=first.unit,
            benchmark=first.benchmark,
            tier=first.tier,
            lower_is_better=first.lower_is_better,
        ))

    return out
