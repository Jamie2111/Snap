"""VOD review ingestion: learn from coach commentary on YouTube reviews.

Three layers:
  1. Transcript    Whisper transcribes the audio to timestamped segments.
  2. Tagging       Each segment is scanned for hero, ability, and concept mentions.
  3. Correlation   Coach quotes are matched against in-video game events (detected
                   by the same extractor pipeline used on live play) by time
                   proximity + topic overlap. High-scoring pairs become
                   high-confidence coaching signals that the feedback engine
                   surfaces in future sessions.
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Optional

# time is used by transcribe() for progress logging

import config
from extractor.events import SessionEvents
from knowledge.overwatch import HERO_COACHING

log = logging.getLogger(__name__)


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str


@dataclass
class TaggedQuote:
    start: float
    end: float
    text: str
    heroes: list[str] = field(default_factory=list)
    abilities: list[str] = field(default_factory=list)
    concepts: list[str] = field(default_factory=list)


@dataclass
class VodCorrelation:
    event_type: str
    event_timestamp: float
    quote: TaggedQuote
    score: float
    delta_seconds: float


CONCEPT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "died_holding_ult": (
        "held ult", "holding ult", "held the ult", "sat on ult", "sat on the ult",
        "wasted ult", "wasted the ult", "ulted too late", "should have ulted",
        "had ult", "ult was up", "ult is up", "ult ready",
    ),
    "died_holding_cooldowns": (
        "had abilities", "had cooldowns", "cooldowns up", "ability was up",
        "should have used", "could have used", "saved cooldown", "wasted cooldown",
    ),
    "engaging_low_health": (
        "low health", "low hp", "no hp", "below half", "half hp",
        "should have reset", "should have backed", "back off",
    ),
    "no_escape": (
        "no escape", "no exit", "no way out", "trapped", "should have had an escape",
        "no escape plan", "no out",
    ),
    "fight_timing": (
        "bad timing", "timing was off", "wrong timing", "should have waited",
        "good timing", "perfect timing", "right timing", "force a fight",
        "forced fight",
    ),
    "positioning": (
        "positioning", "out of position", "wrong angle", "bad angle",
        "off angle", "off-angle", "bad position", "good position",
        "needed cover", "no cover",
    ),
    "ult_economy": (
        "ult economy", "ult diff", "ult difference", "ult advantage",
        "ult disadvantage", "behind on ults", "ahead on ults",
    ),
    "comp_mismatch": (
        "wrong hero", "should have swapped", "comp doesn't work",
        "your comp is", "their comp is",
    ),
    "support_isolation": (
        "support alone", "isolated support", "support out of position",
        "kill the support", "go for support",
    ),
    "tank_diff": (
        "tank diff", "tank was winning", "tank lost", "tank was good",
    ),
    "focus_fire": (
        "focus fire", "focus this target", "everyone shoot", "shoot the same target",
    ),
    "engage_callout": (
        "engage", "go in", "commit", "dive in", "push it",
    ),
    "disengage_callout": (
        "disengage", "back up", "pull back", "regroup", "reset",
    ),
}


def transcribe(video_path: Path, model_size: str = "base") -> list[TranscriptSegment]:
    """Run Whisper on the video's audio track. Returns timestamped segments.

    First call downloads the model (~150MB for 'base'). Requires ffmpeg
    installed system-wide (brew install ffmpeg on Mac).

    Logs progress every 50 segments and every ~30 seconds of audio processed
    so long files do not look hung."""

    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise ImportError(
            "faster-whisper is not installed. Run: pip install faster-whisper"
        ) from exc

    log.info("Loading Whisper model '%s' (first run downloads ~150MB)", model_size)
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    log.info("Transcribing %s ...", video_path)
    start = time.monotonic()
    segments_gen, info = model.transcribe(str(video_path), beam_size=1)
    duration = float(getattr(info, "duration", 0.0))
    log.info("Audio duration: %.0fs, language=%s", duration, info.language)
    segments: list[TranscriptSegment] = []
    last_log_at = 0.0
    for seg in segments_gen:
        segments.append(TranscriptSegment(start=float(seg.start), end=float(seg.end), text=seg.text.strip()))
        elapsed = time.monotonic() - start
        if len(segments) % 50 == 0 or (elapsed - last_log_at) > 30.0:
            pct = (100.0 * float(seg.end) / duration) if duration else 0.0
            log.info(
                "Transcribe: %d segments, audio pos %.0fs/%.0fs (%.0f%%), %.0fs elapsed",
                len(segments), float(seg.end), duration, pct, elapsed,
            )
            last_log_at = elapsed
    log.info("Transcript complete: %d segments, %.0fs to process", len(segments), time.monotonic() - start)
    return segments


HOLDING_VERBS = ("held", "holding", "sat on", "saved", "wasted", "sitting on")

# Ult abilities specifically (subset of all abilities). Used to infer the
# died_holding_ult concept when a coach references a specific ult name
# instead of saying the generic word "ult".
ULT_ABILITIES = {
    "pulse_bomb", "dragonblade", "earthshatter", "primal_rage", "self_destruct",
    "graviton_surge", "nano_boost", "valkyrie", "resurrect", "transcendence",
    "sound_barrier", "death_blossom", "dragonstrike", "tactical_visor",
    "deadeye", "riptire", "infra_sight", "configuration_artillery",
    "captive_sun", "protection_suzu", "kitsune_rush", "annihilation",
    "terra_surge", "rampage", "whole_hog", "minefield", "meteor_strike",
    "overclock", "barrage", "molten_core", "blizzard", "amplification_matrix",
    "orbital_ray", "tree_of_life", "duplicate", "bob", "tectonic_shock",
    "aerodynamic_strike", "coalescence", "rally", "gravitic_flux", "cage_fight",
}


def tag_segments(segments: Iterable[TranscriptSegment]) -> list[TaggedQuote]:
    """Tag each transcript segment with hero/ability/concept mentions.

    Heroes come from config.KNOWN_HEROES. Abilities come from every
    HERO_COACHING[*].abilities dict. Concepts come from CONCEPT_KEYWORDS,
    plus an inference rule: if an ult ability is named alongside a holding
    verb ('held pulse', 'sat on blade'), tag died_holding_ult."""

    ability_names: set[str] = set()
    for data in HERO_COACHING.values():
        ability_names.update(data.get("abilities", {}).keys())
    ability_phrases = [(a, a.replace("_", " ")) for a in sorted(ability_names)]

    out: list[TaggedQuote] = []
    for seg in segments:
        lower = seg.text.lower()
        heroes = sorted({h for h in config.KNOWN_HEROES if _word_in(h, lower)})
        abilities = sorted({a for a, phrase in ability_phrases if phrase in lower})
        concepts = {c for c, patterns in CONCEPT_KEYWORDS.items() if any(p in lower for p in patterns)}
        # Inference: specific ult name + holding verb => died_holding_ult
        if any(a in ULT_ABILITIES for a in abilities) and any(v in lower for v in HOLDING_VERBS):
            concepts.add("died_holding_ult")
        if not (heroes or abilities or concepts):
            continue
        out.append(TaggedQuote(
            start=seg.start, end=seg.end, text=seg.text,
            heroes=heroes, abilities=abilities, concepts=sorted(concepts),
        ))
    log.info("Tagged %d quote(s) with at least one hero/ability/concept", len(out))
    return out


def _word_in(needle: str, haystack: str) -> bool:
    """True if needle appears as a whole word in haystack. Avoids 'ana' matching
    inside 'banana' or 'analyze'."""
    pattern = r"\b" + re.escape(needle) + r"\b"
    return re.search(pattern, haystack) is not None


def _event_to_concepts(event_type: str) -> set[str]:
    """Map a detected game-event type to coaching concepts it relates to."""
    return {
        "died_holding_ult": {"died_holding_ult", "ult_economy"},
        "died_holding_cooldowns": {"died_holding_cooldowns"},
        "engaging_low_health": {"engaging_low_health", "no_escape"},
        "cooldown_held_late": {"died_holding_cooldowns"},
        "ult_wasted": {"died_holding_ult", "ult_economy"},
        "fight_lost": {"fight_timing", "engaging_low_health"},
    }.get(event_type, set())


def correlate(
    quotes: list[TaggedQuote],
    events: SessionEvents,
    window_seconds: float = 6.0,
) -> list[VodCorrelation]:
    """Find quote / event pairs that share a topic AND occur within
    `window_seconds` of each other. Score is higher for tighter time proximity
    and richer topic overlap."""

    correlations: list[VodCorrelation] = []

    flat_events: list[tuple[str, float, set[str]]] = []
    for d in events.deaths:
        if d.ult_pct_at_death >= 0.80:
            flat_events.append(("died_holding_ult", d.timestamp, _event_to_concepts("died_holding_ult")))
        if d.cooldowns_available:
            flat_events.append(("died_holding_cooldowns", d.timestamp, _event_to_concepts("died_holding_cooldowns")))
    for u in events.ults_wasted:
        flat_events.append(("ult_wasted", u.timestamp, _event_to_concepts("ult_wasted")))
    for ch in events.cooldowns_held:
        if ch.context == "used_late":
            flat_events.append(("cooldown_held_late", 0.0, _event_to_concepts("cooldown_held_late")))

    for event_type, ts, event_concepts in flat_events:
        for quote in quotes:
            delta = abs(quote.start - ts)
            if delta > window_seconds:
                continue
            overlap = event_concepts & set(quote.concepts)
            if not overlap:
                continue
            time_score = 1.0 - (delta / window_seconds)
            topic_score = min(1.0, len(overlap) / 2.0)
            score = round(0.6 * time_score + 0.4 * topic_score, 3)
            correlations.append(VodCorrelation(
                event_type=event_type,
                event_timestamp=ts,
                quote=quote,
                score=score,
                delta_seconds=round(delta, 2),
            ))
    log.info("Found %d quote/event correlations within %.0fs window", len(correlations), window_seconds)
    return correlations


def ingest_vod(
    video_path: Path,
    events: SessionEvents,
    conn: sqlite3.Connection,
    source_url: Optional[str] = None,
    title: Optional[str] = None,
    model_size: str = "base",
) -> dict:
    """Top-level: transcribe + tag + correlate + persist. Returns a summary
    dict for the CLI to print."""

    review_id = uuid.uuid4().hex[:12]
    segments = transcribe(video_path, model_size=model_size)
    quotes = tag_segments(segments)
    correlations = correlate(quotes, events)

    duration = segments[-1].end if segments else 0.0
    conn.execute(
        """INSERT INTO vod_reviews (id, source, title, ingested_at, duration_seconds, transcript_json, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            review_id, source_url or str(video_path), title, time.time(),
            duration, json.dumps([asdict(s) for s in segments]), None,
        ),
    )

    quote_ids: dict[int, int] = {}  # index in quotes -> rowid
    for idx, q in enumerate(quotes):
        cur = conn.execute(
            """INSERT INTO vod_quotes (review_id, start_seconds, end_seconds, text,
                                       heroes_json, abilities_json, concepts_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                review_id, q.start, q.end, q.text,
                json.dumps(q.heroes), json.dumps(q.abilities), json.dumps(q.concepts),
            ),
        )
        quote_ids[idx] = cur.lastrowid or 0

    quote_to_index = {id(q): i for i, q in enumerate(quotes)}
    for corr in correlations:
        idx = quote_to_index.get(id(corr.quote))
        if idx is None:
            continue
        conn.execute(
            """INSERT INTO vod_correlations (review_id, quote_id, event_type, event_timestamp,
                                             score, delta_seconds, context_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                review_id, quote_ids[idx], corr.event_type, corr.event_timestamp,
                corr.score, corr.delta_seconds, json.dumps({}),
            ),
        )
    conn.commit()

    return {
        "review_id": review_id,
        "segments": len(segments),
        "tagged_quotes": len(quotes),
        "correlations": len(correlations),
        "duration_seconds": duration,
    }
