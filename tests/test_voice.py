"""Coach voice linter tests."""

from __future__ import annotations

from feedback.voice import CriticalFeedback, check_critical, sanitize_text


def test_well_formed_critical_passes() -> None:
    fb = CriticalFeedback(
        issue="Died holding pulse",
        timestamp=504.0,
        context="Tracer vs Brigitte.",
        historical_context="11 times across 8 sessions.",
        recurrence=11,
        principle="Tracer pulse window is 3 to 5 seconds.",
        next_step="Use within 5 seconds of getting position.",
    )
    res = check_critical(fb)
    assert res.ok
    assert res.missing == []


def test_malformed_critical_flagged() -> None:
    fb = CriticalFeedback(issue="bad", timestamp=0, context="", historical_context="", recurrence=0, principle="", next_step="")
    res = check_critical(fb)
    assert not res.ok
    assert set(res.missing) == {"moment", "context", "principle", "next_step"}


def test_sanitize_strips_em_dash() -> None:
    assert "—" not in sanitize_text("hello — world")
    assert "–" not in sanitize_text("range 2–4")
