"""Ecosystem brain. A NetworkX DiGraph that connects heroes, abilities,
mechanics, mistakes, and concepts. The feedback engine traverses this graph
to enrich advice with relational context, not just lookup.

Node attribute 'kind' is one of: HERO, ABILITY, MECHANIC, CONCEPT, MISTAKE, COUNTER, COMP.
Edge attribute 'relation' is one of:
    counters, hard_counter, combos_with, punishes, requires,
    improves_with, common_after, prevents, synergizes_with, mismatches_with
"""

from __future__ import annotations

from typing import Iterable

import networkx as nx

from knowledge.overwatch import HERO_COACHING, HERO_ROLES, MATCHUPS, SYNERGIES


def _add_node_safe(g: nx.DiGraph, name: str, kind: str) -> None:
    if name not in g:
        g.add_node(name, kind=kind)


def build_graph() -> nx.DiGraph:
    g: nx.DiGraph = nx.DiGraph()

    for hero, role in HERO_ROLES.items():
        g.add_node(hero, kind="HERO", role=role)

    # Comp nodes
    for comp in ("dive", "brawl", "poke", "hybrid"):
        g.add_node(f"{comp}_comp", kind="COMP")

    seed_edges = [
        # Hero counters (from spec)
        ("tracer", "ana", "counters"),
        ("widowmaker", "support_on_highground", "counters"),
        ("reinhardt", "close_range_heroes", "counters"),
        ("ana", "self_healing_heroes", "counters"),
        ("lucio", "burst_damage_ults", "counters"),
        ("zenyatta", "tanks", "counters"),
        ("genji", "isolated_supports", "counters"),

        # Ability combos (from spec)
        ("nano_boost", "dragonblade", "combos_with"),
        ("nano_boost", "earthshatter", "combos_with"),
        ("graviton_surge", "earthshatter", "combos_with"),
        ("graviton_surge", "dragonblade", "combos_with"),
        ("sleep_dart", "team_focus_fire", "combos_with"),
        ("sound_barrier", "aggressive_push", "combos_with"),
        ("discord_orb", "team_dps_focus", "combos_with"),

        # Mechanic requirements
        ("pulse_bomb", "flank_position", "requires"),
        ("pulse_bomb", "target_isolation", "requires"),
        ("dragonblade", "team_fighting_simultaneously", "requires"),
        ("earthshatter", "enemy_grouping", "requires"),
        ("sleep_dart", "target_priority_read", "requires"),

        # Mistake chains
        ("holding_ult_too_long", "lost_fight", "common_after"),
        ("engaging_low_health", "cooldown_waste", "common_after"),
        ("fighting_full_team", "flanker_positioning", "punishes"),
        ("no_escape_route", "aggressive_engage", "punishes"),
        ("barrier_overextension", "reinhardt_play", "punishes"),

        # Concept requirements and improvements
        ("ult_economy", "team_communication", "requires"),
        ("fight_timing", "cooldown_tracking", "requires"),
        ("positioning", "map_knowledge", "improves_with"),
        ("dive_comp", "support_isolation", "requires"),
        ("brawl_comp", "shield_uptime", "requires"),
        ("dive_comp", "coordinated_engage", "requires"),
        ("brawl_comp", "grouped_play", "requires"),
        ("poke_comp", "long_sightlines", "requires"),
    ]

    for src, dst, rel in seed_edges:
        kind_s = "HERO" if src in HERO_ROLES else ("ABILITY" if "_" in src else "CONCEPT")
        kind_d = "HERO" if dst in HERO_ROLES else "CONCEPT"
        _add_node_safe(g, src, kind_s)
        _add_node_safe(g, dst, kind_d)
        g.add_edge(src, dst, relation=rel)

    # Mine MATCHUPS for counter / hard_counter edges
    for your_hero, vs in MATCHUPS.items():
        for enemy, profile in vs.items():
            _add_node_safe(g, your_hero, "HERO")
            _add_node_safe(g, enemy, "HERO")
            diff = profile.get("difficulty", "medium")
            rel = "hard_counter" if diff == "very_hard" else (
                "counters" if diff in ("hard", "medium") else "easy_matchup"
            )
            # Edge direction: enemy -> your_hero means enemy counters you
            if diff in ("very_hard", "hard"):
                g.add_edge(enemy, your_hero, relation=rel, difficulty=diff)

    # Mine SYNERGIES for synergizes_with edges
    for your_hero, allies in SYNERGIES.items():
        for ally, profile in allies.items():
            _add_node_safe(g, your_hero, "HERO")
            _add_node_safe(g, ally, "HERO")
            g.add_edge(your_hero, ally, relation="synergizes_with", rating=profile.get("rating", "B"))

    # Mine HERO_COACHING for ability nodes and mistake nodes
    for hero, data in HERO_COACHING.items():
        for ability, ability_data in data.get("abilities", {}).items():
            _add_node_safe(g, ability, "ABILITY")
            g.add_edge(hero, ability, relation="has_ability")
            for mistake_text in ability_data.get("common_mistakes", []):
                mistake_node = f"{hero}_{ability}_mistake_{hash(mistake_text) & 0xfff}"
                g.add_node(mistake_node, kind="MISTAKE", description=mistake_text)
                g.add_edge(ability, mistake_node, relation="prevents")

    # Comp mismatch warnings
    g.add_edge("tracer", "brawl_comp", relation="mismatches_with")
    g.add_edge("widowmaker", "dive_comp", relation="mismatches_with")
    g.add_edge("reinhardt", "poke_comp", relation="mismatches_with")
    g.add_edge("mercy", "dive_comp", relation="mismatches_with")

    return g


_GRAPH: nx.DiGraph | None = None


def graph() -> nx.DiGraph:
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_graph()
    return _GRAPH


def get_counter_advice(hero: str, situation: str = "") -> list[str]:
    """Return short advice strings for heroes that counter `hero`."""
    g = graph()
    out = []
    for src, _, data in g.in_edges(hero, data=True):
        if data.get("relation") in {"counters", "hard_counter"}:
            out.append(f"{src} {data.get('relation')} {hero}")
    return out


def get_combo_opportunities(hero: str, available_ults: Iterable[str]) -> list[str]:
    g = graph()
    out = []
    available = set(available_ults)
    for _, dst, data in g.out_edges(data=True):
        if data.get("relation") == "combos_with":
            out.append(dst)
    out = [c for c in out if c in available]
    return out


def get_matchup_advice(your_hero: str, enemy_hero: str) -> dict | None:
    profile = MATCHUPS.get(your_hero, {}).get(enemy_hero)
    return profile


def get_synergy_advice(your_hero: str, ally_hero: str) -> dict | None:
    profile = SYNERGIES.get(your_hero, {}).get(ally_hero)
    return profile


def get_comp_mismatch_warnings(your_hero: str, your_comp: str) -> list[str]:
    g = graph()
    warnings = []
    comp_node = f"{your_comp}_comp"
    if g.has_edge(your_hero, comp_node) and g[your_hero][comp_node].get("relation") == "mismatches_with":
        warnings.append(
            f"Your hero ({your_hero}) is a mismatch for {your_comp} comp. "
            f"Either swap heroes or play with the team."
        )
    return warnings


def get_related_concepts(mistake: str) -> list[str]:
    g = graph()
    if mistake not in g:
        return []
    return [n for n in g.successors(mistake)]


def find_pattern_chain(event_keywords: list[str]) -> list[str]:
    """Walk the graph from event keywords to find connected nodes that might
    explain a chain of mistakes. Returns a flat list of suspect nodes."""
    g = graph()
    seen: set[str] = set()
    out: list[str] = []
    frontier = [k for k in event_keywords if k in g]
    while frontier:
        node = frontier.pop()
        if node in seen:
            continue
        seen.add(node)
        out.append(node)
        for _, dst, data in g.out_edges(node, data=True):
            if data.get("relation") in {"common_after", "punishes", "requires"}:
                frontier.append(dst)
    return out
