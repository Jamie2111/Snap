"""Liquid memory layer.

The functions here read and write rich session context so future sessions can
reason over past sessions. The goal is not stats. It is a model of this
specific human's play that compounds over time.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from collections import Counter, defaultdict
from dataclasses import asdict, is_dataclass
from typing import Any, Optional

from memory.database import session as db_session

log = logging.getLogger(__name__)


def _json(value: Any) -> str:
    if is_dataclass(value):
        value = asdict(value)
    return json.dumps(value, default=str)


def _load(text: str) -> Any:
    if not text:
        return {}
    try:
        return json.loads(text)
    except Exception:
        return {}


def write_session(
    session_id: str,
    timestamp: float,
    hero: Optional[str],
    duration_minutes: float,
    deaths: int,
    ult_efficiency_score: int,
    raw_event: dict,
    feedback_given: dict,
    allies: list[str],
    enemies: list[str],
    your_comp: Optional[str],
    enemy_comp: Optional[str],
    map_name: Optional[str] = None,
    game_result: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> None:
    payload = (
        session_id, timestamp, hero, duration_minutes, deaths, ult_efficiency_score,
        _json(raw_event), _json(feedback_given), None, map_name, game_result,
        _json(allies), _json(enemies), your_comp, enemy_comp,
    )
    if conn is not None:
        conn.execute(
            """INSERT OR REPLACE INTO sessions (
                id, timestamp, hero, duration_minutes, deaths, ult_efficiency_score,
                raw_event_json, feedback_given_json, player_response, map, game_result,
                allies_json, enemies_json, your_comp, enemy_comp
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            payload,
        )
        conn.commit()
        return
    with db_session() as c:
        c.execute(
            """INSERT OR REPLACE INTO sessions (
                id, timestamp, hero, duration_minutes, deaths, ult_efficiency_score,
                raw_event_json, feedback_given_json, player_response, map, game_result,
                allies_json, enemies_json, your_comp, enemy_comp
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            payload,
        )


def write_match(
    session_id: str,
    match_index: int,
    started_at: float,
    ended_at: Optional[float],
    duration_seconds: float,
    map_name: Optional[str],
    result: str,
    hero: Optional[str],
    allies: list[str],
    enemies: list[str],
    your_comp: Optional[str],
    enemy_comp: Optional[str],
    deaths: int,
    ult_efficiency_score: int,
    aim_on_target_pct: float,
    raw_event: dict,
    feedback_given: dict,
    conn: Optional[sqlite3.Connection] = None,
) -> None:
    payload = (
        session_id, match_index, started_at, ended_at, duration_seconds, map_name, result,
        hero, _json(allies), _json(enemies), your_comp, enemy_comp,
        deaths, ult_efficiency_score, aim_on_target_pct,
        _json(raw_event), _json(feedback_given),
    )

    def _do(c: sqlite3.Connection) -> None:
        c.execute(
            """INSERT INTO matches (
                session_id, match_index, started_at, ended_at, duration_seconds, map_name, result,
                hero, allies_json, enemies_json, your_comp, enemy_comp,
                deaths, ult_efficiency_score, aim_on_target_pct,
                raw_event_json, feedback_given_json
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            payload,
        )

    if conn is not None:
        _do(conn)
        conn.commit()
        return
    with db_session() as c:
        _do(c)


def get_matches_for_session(session_id: str, conn: Optional[sqlite3.Connection] = None) -> list[dict]:
    def _do(c: sqlite3.Connection) -> list[dict]:
        cur = c.execute(
            "SELECT * FROM matches WHERE session_id = ? ORDER BY match_index",
            (session_id,),
        )
        return [dict(r) for r in cur.fetchall()]

    if conn is not None:
        return _do(conn)
    with db_session() as c:
        return _do(c)


def get_map_history(map_name: str, conn: Optional[sqlite3.Connection] = None) -> dict:
    """Per-map lifetime stats. Useful once the player has 3+ matches on a map."""

    def _do(c: sqlite3.Connection) -> dict:
        cur = c.execute(
            "SELECT result, COUNT(*) c, AVG(deaths) avg_deaths, AVG(ult_efficiency_score) avg_score "
            "FROM matches WHERE map_name = ? GROUP BY result",
            (map_name,),
        )
        rollup = {r["result"]: dict(r) for r in cur.fetchall()}
        total = sum(r["c"] for r in rollup.values())
        wins = rollup.get("win", {}).get("c", 0)
        return {
            "map_name": map_name,
            "matches": total,
            "wins": wins,
            "winrate": wins / total if total else 0.0,
            "by_result": rollup,
        }

    if conn is not None:
        return _do(conn)
    with db_session() as c:
        return _do(c)


def write_mistakes_from_events(
    session_id: str,
    events,
    conn: Optional[sqlite3.Connection] = None,
) -> int:
    """Convert detected events into mistake rows so future sessions can reason
    over them. Returns the number of rows written."""

    written = 0
    now = time.time()
    for d in events.deaths:
        if d.ult_pct_at_death >= 0.80:
            write_mistake(
                session_id=session_id,
                mistake_type="died_holding_ult",
                ability=None,
                timestamp_in_session=d.timestamp,
                context={"ult_pct": d.ult_pct_at_death, "cooldowns_available": d.cooldowns_available},
                severity="critical",
                now=now,
                conn=conn,
            )
            written += 1
        if d.cooldowns_available:
            write_mistake(
                session_id=session_id,
                mistake_type="died_holding_cooldowns",
                ability=",".join(d.cooldowns_available),
                timestamp_in_session=d.timestamp,
                context={"abilities": d.cooldowns_available},
                severity="critical",
                now=now,
                conn=conn,
            )
            written += 1
    for ch in events.cooldowns_held:
        if ch.context == "used_late":
            write_mistake(
                session_id=session_id,
                mistake_type="cooldown_held_late",
                ability=ch.ability,
                timestamp_in_session=0.0,
                context={"duration": ch.held_ready_duration},
                severity="improvement",
                now=now,
                conn=conn,
            )
            written += 1
    return written


def write_mistake(
    session_id: str,
    mistake_type: str,
    ability: Optional[str],
    timestamp_in_session: float,
    context: dict,
    severity: str,
    now: float,
    conn: Optional[sqlite3.Connection] = None,
) -> None:
    """Insert a new mistake row. The trajectory and recurrence count are
    recomputed by update_player_model."""
    row = (
        session_id, mistake_type, ability, timestamp_in_session,
        _json(context), severity, 1, now, now, "stable", None, None,
    )

    def _do(c: sqlite3.Connection) -> None:
        c.execute(
            """INSERT INTO mistakes (
                session_id, mistake_type, ability, timestamp_in_session, context_json,
                severity, recurrence_count, first_seen, last_seen, improvement_trajectory,
                feedback_given, was_acted_on
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            row,
        )

    if conn is not None:
        _do(conn)
        conn.commit()
        return
    with db_session() as c:
        _do(c)


def update_player_model(new_session_id: str, conn: Optional[sqlite3.Connection] = None) -> dict:
    """Recompute the player model after a session has been written.

    Walks recent mistakes, updates per-mistake-type recurrence and trajectory,
    classifies persistent patterns. Returns the updated model dict."""

    def _do(c: sqlite3.Connection) -> dict:
        cur = c.execute(
            "SELECT mistake_type, ability, severity, timestamp_in_session, last_seen, session_id "
            "FROM mistakes ORDER BY last_seen"
        )
        rows = cur.fetchall()

        by_type: dict[str, list[sqlite3.Row]] = defaultdict(list)
        for r in rows:
            by_type[r["mistake_type"]].append(r)

        persistent: dict[str, dict] = {}
        for mtype, items in by_type.items():
            sessions = list({r["session_id"] for r in items})
            persistent[mtype] = {
                "count": len(items),
                "sessions": len(sessions),
                "last_seen": items[-1]["last_seen"],
                "trajectory": _classify_trajectory(items),
            }

        sessions_cur = c.execute(
            "SELECT hero, deaths, ult_efficiency_score FROM sessions ORDER BY timestamp"
        )
        session_rows = sessions_cur.fetchall()
        learning_velocity = _learning_velocity(session_rows, by_type)
        pressure = _pressure_profile(session_rows)
        coaching_style = _adapt_style(session_rows, persistent)

        model = {
            "persistent_patterns": persistent,
            "learning_velocity": learning_velocity,
            "pressure_profile": pressure,
            "coaching_style_preference": coaching_style,
        }

        c.execute(
            """UPDATE player_model SET
                updated_at = ?,
                pressure_profile_json = ?,
                learning_velocity_json = ?,
                persistent_patterns_json = ?,
                coaching_style_preference = ?,
                current_focus_areas_json = ?,
                sessions_until_improvement_json = ?
               WHERE id = 1""",
            (
                time.time(),
                _json(pressure),
                _json(learning_velocity),
                _json(persistent),
                coaching_style,
                _json(_current_focus(persistent)),
                _json({}),
            ),
        )
        return model

    if conn is not None:
        out = _do(conn)
        conn.commit()
        return out
    with db_session() as c:
        return _do(c)


def get_session_context(
    current_hero: Optional[str],
    current_mistake_types: list[str],
    conn: Optional[sqlite3.Connection] = None,
) -> dict:
    """Return rich context the feedback engine pulls from when generating
    advice. Includes per-hero history and per-mistake-type history."""

    def _do(c: sqlite3.Connection) -> dict:
        ctx: dict[str, Any] = {}
        if current_hero:
            cur = c.execute(
                "SELECT id, timestamp, deaths, ult_efficiency_score FROM sessions "
                "WHERE hero = ? ORDER BY timestamp DESC LIMIT 10",
                (current_hero,),
            )
            ctx["recent_sessions_on_hero"] = [dict(r) for r in cur.fetchall()]
            ctx["sessions_on_hero_total"] = len(ctx["recent_sessions_on_hero"])
        else:
            ctx["recent_sessions_on_hero"] = []
            ctx["sessions_on_hero_total"] = 0

        per_type: dict[str, dict] = {}
        for mtype in current_mistake_types:
            cur = c.execute(
                "SELECT COUNT(*) AS cnt, MAX(last_seen) AS last_seen FROM mistakes "
                "WHERE mistake_type = ?",
                (mtype,),
            )
            row = cur.fetchone()
            per_type[mtype] = {
                "lifetime_count": row["cnt"] if row else 0,
                "last_seen": row["last_seen"] if row and row["last_seen"] else 0.0,
            }
        ctx["mistake_history"] = per_type

        cur = c.execute("SELECT persistent_patterns_json, coaching_style_preference FROM player_model WHERE id=1")
        row = cur.fetchone()
        ctx["persistent_patterns"] = _load(row["persistent_patterns_json"]) if row else {}
        ctx["coaching_style_preference"] = row["coaching_style_preference"] if row else "direct"

        return ctx

    if conn is not None:
        return _do(conn)
    with db_session() as c:
        return _do(c)


def get_matchup_history(your_hero: str, enemy_hero: str, conn: Optional[sqlite3.Connection] = None) -> dict:
    """How many times did you play your_hero vs a team containing enemy_hero?
    How many of those sessions did you die? Lifetime numbers, used by the
    feedback engine to surface matchup-specific patterns."""

    def _do(c: sqlite3.Connection) -> dict:
        cur = c.execute(
            "SELECT enemies_json, deaths FROM sessions WHERE hero = ?",
            (your_hero,),
        )
        sessions_against = 0
        deaths_against = 0
        for row in cur.fetchall():
            enemies = _load(row["enemies_json"])
            if enemy_hero in enemies:
                sessions_against += 1
                deaths_against += int(row["deaths"] or 0)
        return {
            "your_hero": your_hero,
            "enemy_hero": enemy_hero,
            "sessions_against": sessions_against,
            "deaths_against": deaths_against,
        }

    if conn is not None:
        return _do(conn)
    with db_session() as c:
        return _do(c)


def get_coach_quotes_for(
    hero: Optional[str],
    mistake_types: list[str],
    limit: int = 3,
    conn: Optional[sqlite3.Connection] = None,
) -> list[dict]:
    """Return up to `limit` ingested coach quotes that are relevant to the
    current session: quotes that mention this hero AND any of the detected
    mistake concepts. Correlated quotes (proven coach-on-event hits in past
    VODs) are ranked higher than generic quotes.

    Used by the feedback engine to surface a 'Coach said' tier."""

    def _do(c: sqlite3.Connection) -> list[dict]:
        if not mistake_types and not hero:
            return []
        rows = c.execute(
            "SELECT q.id, q.start_seconds, q.text, q.heroes_json, q.concepts_json, "
            "       v.source, v.title, "
            "       COALESCE(MAX(cor.score), 0.0) AS best_score "
            "FROM vod_quotes q "
            "JOIN vod_reviews v ON v.id = q.review_id "
            "LEFT JOIN vod_correlations cor ON cor.quote_id = q.id "
            "GROUP BY q.id "
            "ORDER BY best_score DESC, q.id DESC "
        ).fetchall()

        scored: list[tuple[float, dict]] = []
        for r in rows:
            heroes = _load(r["heroes_json"])
            concepts = _load(r["concepts_json"])
            score = float(r["best_score"] or 0.0)
            relevance = 0.0
            if hero and hero in heroes:
                relevance += 1.0
            if mistake_types:
                overlap = set(concepts) & set(mistake_types)
                relevance += 0.5 * len(overlap)
            if relevance == 0.0:
                continue
            scored.append((
                score + relevance,
                {
                    "text": r["text"],
                    "source": r["source"],
                    "title": r["title"] or "",
                    "timestamp": float(r["start_seconds"]),
                    "heroes": heroes,
                    "concepts": concepts,
                    "correlation_score": score,
                },
            ))
        scored.sort(key=lambda kv: kv[0], reverse=True)
        return [item for _, item in scored[:limit]]

    if conn is not None:
        return _do(conn)
    with db_session() as c:
        return _do(c)


def get_comp_performance(your_comp: str, conn: Optional[sqlite3.Connection] = None) -> dict:
    def _do(c: sqlite3.Connection) -> dict:
        cur = c.execute("SELECT deaths, ult_efficiency_score FROM sessions WHERE your_comp = ?", (your_comp,))
        rows = cur.fetchall()
        if not rows:
            return {"your_comp": your_comp, "sessions": 0, "avg_deaths": 0.0, "avg_ult_score": 0.0}
        deaths = [r["deaths"] for r in rows]
        scores = [r["ult_efficiency_score"] for r in rows]
        return {
            "your_comp": your_comp,
            "sessions": len(rows),
            "avg_deaths": sum(deaths) / len(deaths),
            "avg_ult_score": sum(scores) / len(scores),
        }

    if conn is not None:
        return _do(conn)
    with db_session() as c:
        return _do(c)


def detect_pressure_patterns(conn: Optional[sqlite3.Connection] = None) -> dict:
    """Analyze whether performance degrades on specific heroes / comps / long
    sessions. Needs 5+ sessions to produce useful signal."""

    def _do(c: sqlite3.Connection) -> dict:
        cur = c.execute("SELECT hero, duration_minutes, deaths FROM sessions ORDER BY timestamp")
        rows = cur.fetchall()
        if len(rows) < 5:
            return {"insufficient_data": True}

        per_hero_deaths: dict[str, list[int]] = defaultdict(list)
        long_session_deaths: list[int] = []
        for r in rows:
            if r["hero"]:
                per_hero_deaths[r["hero"]].append(r["deaths"])
            if (r["duration_minutes"] or 0) > 15.0:
                long_session_deaths.append(r["deaths"])

        worst_hero = max(
            ((h, sum(d) / len(d)) for h, d in per_hero_deaths.items() if d),
            key=lambda kv: kv[1],
            default=(None, 0.0),
        )
        return {
            "insufficient_data": False,
            "worst_hero": worst_hero[0],
            "worst_hero_avg_deaths": worst_hero[1],
            "long_session_avg_deaths": (sum(long_session_deaths) / len(long_session_deaths)) if long_session_deaths else 0.0,
        }

    if conn is not None:
        return _do(conn)
    with db_session() as c:
        return _do(c)


def generate_weekly_summary(conn: Optional[sqlite3.Connection] = None) -> dict:
    """One-week rollup. Returns empty payload if there are <7 days of history."""

    def _do(c: sqlite3.Connection) -> dict:
        now = time.time()
        week_ago = now - (7 * 24 * 3600)
        cur = c.execute(
            "SELECT hero, deaths, ult_efficiency_score, your_comp, enemy_comp FROM sessions WHERE timestamp >= ?",
            (week_ago,),
        )
        rows = cur.fetchall()
        if len(rows) < 3:
            return {"insufficient_data": True, "sessions_this_week": len(rows)}

        heroes = Counter(r["hero"] for r in rows if r["hero"])
        comps_played = Counter(r["your_comp"] for r in rows if r["your_comp"])
        return {
            "insufficient_data": False,
            "sessions_this_week": len(rows),
            "heroes_played": dict(heroes),
            "comps_played": dict(comps_played),
            "avg_deaths_this_week": sum(r["deaths"] for r in rows) / len(rows),
            "avg_ult_score_this_week": sum(r["ult_efficiency_score"] for r in rows) / len(rows),
        }

    if conn is not None:
        return _do(conn)
    with db_session() as c:
        return _do(c)


def _classify_trajectory(items: list[sqlite3.Row]) -> str:
    if len(items) < 3:
        return "stable"
    timestamps = [r["last_seen"] for r in items]
    mid = len(items) // 2
    first_half = len(items[:mid])
    second_half = len(items[mid:])
    if second_half < first_half * 0.6:
        return "getting_better"
    if second_half > first_half * 1.4:
        return "getting_worse"
    return "stable"


def _learning_velocity(session_rows: list[sqlite3.Row], by_type: dict[str, list[sqlite3.Row]]) -> dict[str, Any]:
    velocity: dict[str, Any] = {}
    if not session_rows:
        return velocity
    total_sessions = len(session_rows)
    for mtype, items in by_type.items():
        first_session_seen = items[0]["session_id"]
        first_idx = next((i for i, r in enumerate(session_rows) if r["hero"] == first_session_seen), None)
        velocity[mtype] = {
            "first_appeared": first_idx,
            "total_occurrences": len(items),
            "occurrence_rate": len(items) / total_sessions,
        }
    return velocity


def _pressure_profile(session_rows: list[sqlite3.Row]) -> dict[str, Any]:
    if not session_rows:
        return {}
    deaths_per_session = [r["deaths"] for r in session_rows]
    return {
        "avg_deaths": sum(deaths_per_session) / len(deaths_per_session),
        "max_deaths": max(deaths_per_session),
        "session_count": len(deaths_per_session),
    }


def _adapt_style(session_rows: list[sqlite3.Row], persistent: dict[str, dict]) -> str:
    """Coaching style heuristic. Direct works for players who respond fast,
    explanatory works for slow trajectories. Default is direct."""
    if not persistent:
        return "direct"
    worsening = sum(1 for p in persistent.values() if p.get("trajectory") == "getting_worse")
    improving = sum(1 for p in persistent.values() if p.get("trajectory") == "getting_better")
    if improving >= worsening:
        return "direct"
    return "explanatory"


def _current_focus(persistent: dict[str, dict]) -> list[str]:
    """Pick the top 3 mistake types that have not improved as the current
    focus areas. Items in 'getting_better' are excluded."""
    candidates = sorted(
        (
            (mtype, p) for mtype, p in persistent.items()
            if p.get("trajectory") != "getting_better"
        ),
        key=lambda kv: kv[1].get("count", 0),
        reverse=True,
    )
    return [c[0] for c in candidates[:3]]
