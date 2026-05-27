"""Coaching voice rules.

A real coach does not say 'you died too much.' They produce a paragraph that
contains: specific moment, match context, cross-session pattern, root cause
principle, concrete next step. This module enforces that shape for critical-tier
feedback. Improvement and insight tiers are guided but not strictly linted.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass
class CriticalFeedback:
    issue: str
    timestamp: float
    context: str
    historical_context: str
    recurrence: int
    principle: str
    next_step: str

    def render(self) -> str:
        parts = []
        if self.timestamp:
            mm, ss = divmod(int(self.timestamp), 60)
            parts.append(f"[{mm:d}:{ss:02d}] {self.issue}")
        else:
            parts.append(self.issue)
        if self.context:
            parts.append(self.context)
        if self.recurrence and self.recurrence > 1:
            parts.append(f"This is the {_ordinal(self.recurrence)} time across your tracked sessions.")
        if self.historical_context:
            parts.append(self.historical_context)
        if self.principle:
            parts.append(self.principle)
        if self.next_step:
            parts.append(f"Next: {self.next_step}")
        return " ".join(parts)


@dataclass
class VoiceCheckResult:
    ok: bool
    missing: list[str]
    text: str


REQUIRED_COMPONENTS = ("moment", "context", "principle", "next_step")


def check_critical(feedback: CriticalFeedback) -> VoiceCheckResult:
    """Verify a CriticalFeedback meets the voice contract.

    Missing components are listed. The caller can decide whether to surface the
    feedback anyway (degraded) or hold it back."""

    missing: list[str] = []
    if not feedback.timestamp and "[" not in feedback.issue:
        missing.append("moment")
    if not feedback.context:
        missing.append("context")
    if not feedback.principle:
        missing.append("principle")
    if not feedback.next_step:
        missing.append("next_step")
    text = feedback.render()
    return VoiceCheckResult(ok=not missing, missing=missing, text=text)


def lint_all(feedbacks: Iterable[CriticalFeedback]) -> list[VoiceCheckResult]:
    return [check_critical(f) for f in feedbacks]


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


_DECIMAL_RANGE_RE = re.compile(r"\b\d+([\-–—])\d+\b")


def sanitize_text(text: str) -> str:
    """Strip em-dashes and en-dashes from any feedback string. The user has a
    durable preference against these characters. This is a belt-and-braces
    safety net in case a template slips one through."""
    text = text.replace("—", ". ").replace("–", "-")
    return text
