"""Feedback engine.

Inputs: SessionEvents + MatchContext + player history + knowledge + ecosystem.
Output: a structured feedback object the UI renders.

The engine enforces the coaching philosophy from the plan: critical-tier
feedback always includes specific moment, match context, recurrence (if any),
principle, and next step. The voice linter is consulted on every critical.
"""

from __future__ import annotations

import logging
import sqlite3
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

import config
from extractor.events import SessionEvents
from extractor.match_context import MatchContext
from feedback import templates
from feedback.voice import CriticalFeedback, check_critical, sanitize_text
from knowledge import ecosystem
from knowledge.overwatch import (
    GAME_SENSE_RULES,
    HERO_COACHING,
    MATCHUPS,
    SYNERGIES,
)
from memory import player_profile

log = logging.getLogger(__name__)


@dataclass
class SessionSummary:
    hero: Optional[str]
    ult_efficiency_score: int
    deaths: int
    estimated_avoidable_deaths: int
    session_grade: str


@dataclass
class ImprovementItem:
    pattern: str
    frequency: int
    historical_trend: str
    suggestion: str


@dataclass
class InsightItem:
    observation: str
    evidence: str
    principle: str
    graph_context: str = ""


@dataclass
class CoachQuote:
    text: str
    source: str
    timestamp: float
    relevance: str = ""


@dataclass
class MechanicsItem:
    metric: str
    value: str
    interpretation: str


@dataclass
class MatchSummary:
    """Summary card for one match within a multi-match session."""
    match_index: int
    map_name: Optional[str]
    result: str
    duration_minutes: float
    hero: Optional[str]
    enemies: list[str]
    deaths: int
    ult_efficiency_score: int
    aim_on_target_pct: float


@dataclass
class StatItem:
    """One measured hero-specific stat for the Stats panel."""
    label: str
    value: float
    unit: str
    benchmark: Optional[float]
    delta_pct: Optional[float]
    status: str  # above | on_target | below | unknown


@dataclass
class Feedback:
    session_summary: SessionSummary
    critical: list[CriticalFeedback] = field(default_factory=list)
    improvement: list[ImprovementItem] = field(default_factory=list)
    insight: list[InsightItem] = field(default_factory=list)
    coach_said: list[CoachQuote] = field(default_factory=list)
    mechanics: list[MechanicsItem] = field(default_factory=list)
    stats: list[StatItem] = field(default_factory=list)
    one_thing_to_focus_on: str = ""
    progress_acknowledgment: str = ""
    match_context: Optional[MatchContext] = None
    matches: list["Feedback"] = field(default_factory=list)
    match_summaries: list[MatchSummary] = field(default_factory=list)


def _score_ult_efficiency(events: SessionEvents) -> int:
    score = 100
    score -= events.stats.deaths_with_ult_above_80pct * 12
    score -= int(events.stats.avg_ult_hold_time_after_full * 1.5)
    score -= events.stats.ults_wasted * 6
    return max(0, min(100, score))


def _estimate_avoidable_deaths(events: SessionEvents) -> int:
    return max(
        events.stats.deaths_with_ult_above_80pct,
        events.stats.deaths_with_available_cooldowns,
    )


def _grade(ult_score: int, deaths: int) -> str:
    if ult_score >= 85 and deaths <= 3:
        return "A"
    if ult_score >= 70 and deaths <= 5:
        return "B"
    if ult_score >= 50 and deaths <= 8:
        return "C"
    return "D"


def _critical_from_ult_deaths(
    events: SessionEvents,
    match: MatchContext,
    history: dict,
) -> list[CriticalFeedback]:
    out: list[CriticalFeedback] = []
    if not events.deaths:
        return out
    hero = match.your_hero
    coach = HERO_COACHING.get(hero or "", {})
    win = coach.get("win_condition", "")
    for d in events.deaths:
        if d.ult_pct_at_death < 0.80:
            continue
        ts = d.timestamp
        ctx = _context_phrase(match)
        principle = win or "Holding an ult into death is the single highest-cost mistake in Overwatch."
        next_step = "Use ult when you have above 80 percent. A used ult creates pressure. A held ult creates nothing."
        prior = history.get("mistake_history", {}).get("died_holding_ult", {})
        recurrence = prior.get("lifetime_count", 0) + 1
        out.append(
            CriticalFeedback(
                issue=sanitize_text(f"Died with ult at {int(d.ult_pct_at_death * 100)} percent."),
                timestamp=ts,
                context=sanitize_text(ctx),
                historical_context="" if recurrence <= 1 else f"You have died with ult above 80 percent {recurrence} times.",
                recurrence=recurrence,
                principle=sanitize_text(principle),
                next_step=sanitize_text(next_step),
            )
        )
    return out


def _critical_from_held_cooldowns(events: SessionEvents, match: MatchContext) -> list[CriticalFeedback]:
    out: list[CriticalFeedback] = []
    by_ability = Counter()
    for ch in events.cooldowns_held:
        if ch.context == "died_holding" and ch.held_ready_duration > 4.0:
            by_ability[ch.ability] += 1
    if not by_ability:
        return out
    abilities = ", ".join(by_ability.keys())
    out.append(
        CriticalFeedback(
            issue=f"Died with cooldowns available ({abilities}).",
            timestamp=events.deaths[-1].timestamp if events.deaths else 0.0,
            context=_context_phrase(match),
            historical_context="",
            recurrence=sum(by_ability.values()),
            principle="Cooldowns are insurance against losing fights. A held cooldown into death is a free fight for the enemy.",
            next_step="Use the weakest cooldown to confirm engages. Save the best for the decisive moment.",
        )
    )
    return out


def _critical_from_hard_counters(
    match: MatchContext,
    events: SessionEvents,
    db_conn: Optional[sqlite3.Connection] = None,
) -> list[CriticalFeedback]:
    out: list[CriticalFeedback] = []
    if not match.your_hero or not match.enemies:
        return out
    hard_counters = []
    for enemy in match.enemies:
        profile = MATCHUPS.get(match.your_hero, {}).get(enemy)
        if profile and profile.get("difficulty") in ("very_hard", "hard"):
            hard_counters.append((enemy, profile))
    if not hard_counters:
        return out

    enemy, profile = hard_counters[0]
    history = player_profile.get_matchup_history(match.your_hero, enemy, conn=db_conn)
    deaths_total = history.get("deaths_against", 0) + events.stats.deaths_total
    threat = profile.get("key_threat", "")
    advice = profile.get("advice", [])
    next_step = advice[0] if advice else "Stay outside the enemy threat range when on cooldown."
    historical = ""
    if history.get("sessions_against", 0) >= 1:
        historical = f"You've now played against {enemy} in {history['sessions_against'] + 1} sessions on {match.your_hero}."
    out.append(
        CriticalFeedback(
            issue=f"Hard matchup against {enemy} this game.",
            timestamp=events.deaths[0].timestamp if events.deaths else 0.0,
            context=_context_phrase(match),
            historical_context=historical,
            recurrence=history.get("sessions_against", 0) + 1,
            principle=f"{enemy} threat: {threat}",
            next_step=next_step,
        )
    )
    return out


def _improvements(events: SessionEvents, history: dict) -> list[ImprovementItem]:
    out: list[ImprovementItem] = []
    if events.stats.fights_engaged_total >= 3:
        out.append(
            ImprovementItem(
                pattern="Fight survival rate",
                frequency=events.stats.fights_engaged_total,
                historical_trend=(
                    "Survival rate is " + ("solid" if events.stats.fight_survival_rate >= 0.5 else "low")
                ),
                suggestion=(
                    "Disengage at sub-50 percent health. Forced fights compound losses."
                    if events.stats.fight_survival_rate < 0.5
                    else "Keep selecting your fights this carefully."
                ),
            )
        )
    if events.stats.avg_ult_hold_time_after_full > 0:
        out.append(
            ImprovementItem(
                pattern="Ult hold time",
                frequency=len(events.stats.ult_hold_durations),
                historical_trend=(
                    "Hold time " + ("acceptable" if events.stats.avg_ult_hold_time_after_full < 12 else "long")
                ),
                suggestion=(
                    "Aim to use ults within 8 seconds of full charge or hold for a coordinated setup."
                ),
            )
        )
    return out


def _insights(events: SessionEvents, match: MatchContext, history: dict) -> list[InsightItem]:
    out: list[InsightItem] = []
    if match.your_hero and match.your_comp:
        warnings = ecosystem.get_comp_mismatch_warnings(match.your_hero, match.your_comp)
        for w in warnings:
            out.append(
                InsightItem(
                    observation=w,
                    evidence=f"Your team: {', '.join([match.your_hero] + match.allies)}",
                    principle=templates.WIN_CONDITION_BY_COMP.get(match.your_comp, ""),
                    graph_context=f"comp:{match.your_comp}",
                )
            )

    if match.your_hero and match.allies:
        best_synergy: tuple[Optional[str], str] = (None, "")
        for ally in match.allies:
            profile = SYNERGIES.get(match.your_hero, {}).get(ally)
            if profile and profile.get("rating") == "S":
                best_synergy = (ally, profile.get("win_condition", ""))
                break
        if best_synergy[0]:
            out.append(
                InsightItem(
                    observation=f"S-tier synergy with your {best_synergy[0]}.",
                    evidence=best_synergy[1],
                    principle="Synergy advantages compound when you coordinate ult and cooldown timing.",
                    graph_context=f"synergy:{match.your_hero}->{best_synergy[0]}",
                )
            )

    if events.stats.deaths_total >= 2 and events.stats.fights_engaged_low_health >= 2:
        out.append(
            InsightItem(
                observation="Multiple fights engaged below 50 percent health.",
                evidence=f"{events.stats.fights_engaged_low_health} low-health engagements this session.",
                principle="Reset awareness. Half-health engages compound losses. Pull back, full HP, then engage.",
            )
        )

    if history.get("sessions_on_hero_total", 0) == 0:
        out.append(
            InsightItem(
                observation=templates.INSIGHT_FIRST_SESSION,
                evidence="No prior tracked sessions.",
                principle="Snap gets meaningfully sharper around session 5 as patterns emerge.",
            )
        )

    return out


def _pick_focus(critical: list[CriticalFeedback], improvements: list[ImprovementItem]) -> str:
    if critical:
        # Pick the highest-recurrence critical
        critical_sorted = sorted(critical, key=lambda c: c.recurrence, reverse=True)
        top = critical_sorted[0]
        return sanitize_text(top.issue + " " + top.next_step)
    if improvements:
        return sanitize_text(improvements[0].suggestion)
    return "Keep playing. Snap is building your baseline."


def _progress_ack(history: dict, events: SessionEvents) -> str:
    patterns = history.get("persistent_patterns", {})
    improving = [m for m, p in patterns.items() if p.get("trajectory") == "getting_better"]
    if improving:
        return sanitize_text(f"Improving: {', '.join(improving)}. Keep the same approach.")
    if not patterns:
        return ""
    return ""


def _context_phrase(match: MatchContext) -> str:
    if not match.your_hero:
        return ""
    parts = [f"{match.your_hero.title()}"]
    if match.your_comp:
        parts.append(f"in {match.your_comp} comp")
    if match.enemies:
        parts.append(f"vs {'/'.join(match.enemies[:3])}")
    return " ".join(parts) + "."


def generate(
    events: SessionEvents,
    match: MatchContext,
    db_conn: Optional[sqlite3.Connection] = None,
) -> Feedback:
    mistake_types = []
    if events.stats.deaths_with_ult_above_80pct:
        mistake_types.append("died_holding_ult")
    if events.stats.deaths_with_available_cooldowns:
        mistake_types.append("died_holding_cooldowns")

    history = player_profile.get_session_context(match.your_hero, mistake_types, conn=db_conn)

    ult_score = _score_ult_efficiency(events)
    avoidable = _estimate_avoidable_deaths(events)
    grade = _grade(ult_score, events.stats.deaths_total)
    summary = SessionSummary(
        hero=match.your_hero,
        ult_efficiency_score=ult_score,
        deaths=events.stats.deaths_total,
        estimated_avoidable_deaths=avoidable,
        session_grade=grade,
    )

    critical: list[CriticalFeedback] = []
    critical.extend(_critical_from_ult_deaths(events, match, history))
    critical.extend(_critical_from_held_cooldowns(events, match))
    critical.extend(_critical_from_hard_counters(match, events, db_conn=db_conn))

    # Lint criticals. Fully-malformed ones are dropped; partial ones surface with a degraded note.
    linted: list[CriticalFeedback] = []
    for c in critical:
        res = check_critical(c)
        if res.ok:
            linted.append(c)
        else:
            log.debug("Critical degraded (missing %s): %s", res.missing, c.issue)
            if {"moment", "context"} - set(res.missing):
                # Tolerate missing principle/next_step, but require moment + context
                linted.append(c)

    improvements = _improvements(events, history)
    insights = _insights(events, match, history)
    coach_said = _coach_quotes(match.your_hero, mistake_types, db_conn)
    mechanics = _mechanics(events)
    focus = _pick_focus(linted, improvements)
    progress = _progress_ack(history, events)

    return Feedback(
        session_summary=summary,
        critical=linted,
        improvement=improvements,
        insight=insights,
        coach_said=coach_said,
        mechanics=mechanics,
        one_thing_to_focus_on=focus,
        progress_acknowledgment=progress,
        match_context=match,
    )


def _mechanics(events: SessionEvents) -> list[MechanicsItem]:
    out: list[MechanicsItem] = []
    s = events.stats
    if s.aim_frames_with_enemy > 0:
        on_target_pct = s.aim_frames_on_target / s.aim_frames_with_enemy
        interpretation = (
            "Tight tracking under pressure." if on_target_pct >= 0.30
            else "Aim drifts off-target. Practice tracking drills."
            if on_target_pct < 0.15
            else "Tracking is workable; consistency is the gap."
        )
        out.append(MechanicsItem(
            metric="Aim on target",
            value=f"{on_target_pct:.0%} of frames an enemy was in sight",
            interpretation=interpretation,
        ))
        out.append(MechanicsItem(
            metric="Avg miss distance",
            value=f"{s.aim_avg_miss_px:.0f}px from crosshair",
            interpretation=(
                "Most misses are reflick distance; mechanical."
                if s.aim_avg_miss_px < 80
                else "Misses are large; positioning gives you bad angles."
            ),
        ))
    if s.ability_glow_counts:
        top = max(s.ability_glow_counts.items(), key=lambda kv: kv[1])
        out.append(MechanicsItem(
            metric="Most visible ult effect",
            value=f"{top[0]} ({top[1]} frames)",
            interpretation="Either you used this ult or an enemy did; useful for ult-economy review.",
        ))
    return out


def _stats_to_items(match_stats) -> list[StatItem]:
    """Convert MatchStats to a list of StatItems for the UI."""
    return [
        StatItem(
            label=sl.label,
            value=sl.value,
            unit=sl.unit,
            benchmark=sl.benchmark,
            delta_pct=sl.delta_pct,
            status=sl.status,
        )
        for sl in match_stats.stats
    ]


def generate_for_matches(
    matches: list,
    db_conn: Optional[sqlite3.Connection] = None,
) -> Feedback:
    """Multi-match session feedback. Generates per-match Feedback objects plus
    an aggregated session-overview Feedback that contains MatchSummary cards
    for the UI to render."""

    from extractor.match_stats import aggregate as aggregate_stats, compute_stats
    from extractor.match_tracker import Match, aggregate_session_stats

    per_match: list[Feedback] = []
    per_match_stats = []
    summaries: list[MatchSummary] = []
    for m in matches:
        fb = generate(m.events, m.match_context, db_conn=db_conn)
        ms = compute_stats(m.match_context.your_hero, m.events, m.duration_seconds)
        per_match_stats.append(ms)
        fb.stats = _stats_to_items(ms)
        per_match.append(fb)
        aim_pct = (
            fb.session_summary.ult_efficiency_score  # placeholder if no aim data
            if not m.events.stats.aim_frames_with_enemy
            else round(100.0 * m.events.stats.aim_frames_on_target / m.events.stats.aim_frames_with_enemy)
        )
        summaries.append(MatchSummary(
            match_index=m.match_index,
            map_name=m.map_name,
            result=m.result,
            duration_minutes=round(m.duration_seconds / 60.0, 1),
            hero=m.match_context.your_hero,
            enemies=list(m.match_context.enemies),
            deaths=m.events.stats.deaths_total,
            ult_efficiency_score=fb.session_summary.ult_efficiency_score,
            aim_on_target_pct=(
                m.events.stats.aim_frames_on_target / m.events.stats.aim_frames_with_enemy
                if m.events.stats.aim_frames_with_enemy else 0.0
            ),
        ))

    # Aggregate stats for a session-level overview.
    agg_events = aggregate_session_stats(matches)
    if matches:
        # Use the most-recent match's context for session-level synergies/insights.
        recent_ctx = matches[-1].match_context
    else:
        recent_ctx = MatchContext()
    session_fb = generate(agg_events, recent_ctx, db_conn=db_conn)
    session_fb.matches = per_match
    session_fb.match_summaries = summaries
    if per_match_stats:
        session_fb.stats = _stats_to_items(aggregate_stats(per_match_stats))
        # Emit a critical for any stat that's significantly below benchmark.
        below = [s for s in session_fb.stats if s.status == "below" and s.benchmark is not None]
        for st in below[:2]:
            session_fb.critical.append(CriticalFeedback(
                issue=f"{st.label}: {st.value}{st.unit} (target {st.benchmark}{st.unit})",
                timestamp=0.0,
                context=f"Below {st.tier if hasattr(st, 'tier') else 'diamond'} benchmark by "
                        f"{abs(int(st.delta_pct or 0))} percent.",
                historical_context="",
                recurrence=1,
                principle="Hero kit throughput is a leading indicator. Heroes that under-use their kit under-perform.",
                next_step=f"Track this stat next session and aim to close the gap by 5 to 10 percent.",
            ))
    return session_fb


def _coach_quotes(hero: Optional[str], mistake_types: list[str], db_conn) -> list[CoachQuote]:
    raw = player_profile.get_coach_quotes_for(hero, mistake_types, limit=3, conn=db_conn)
    out: list[CoachQuote] = []
    for q in raw:
        relevance_bits = []
        if hero and hero in q.get("heroes", []):
            relevance_bits.append(f"matches {hero}")
        overlap = set(mistake_types) & set(q.get("concepts", []))
        if overlap:
            relevance_bits.append(f"discusses {', '.join(sorted(overlap))}")
        out.append(CoachQuote(
            text=sanitize_text(q["text"].strip()),
            source=q.get("title") or q.get("source", ""),
            timestamp=q.get("timestamp", 0.0),
            relevance="; ".join(relevance_bits),
        ))
    return out
