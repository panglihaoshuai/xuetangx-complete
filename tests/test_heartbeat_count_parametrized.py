"""Heartbeat-specific parametrized invariants.

These pin down behaviors that the audit calls out as fragile.
"""
from __future__ import annotations

import pytest

from telemetry_research.sequence_builder import build_sequence


@pytest.mark.parametrize(
    "duration,count",
    [
        (30.0, 80),
        (120.0, 80),
        (395.0, 80),
        (600.0, 80),
        (1800.0, 80),
    ],
)
def test_each_canonical_duration_yields_monotonic_progress(duration, count):
    seq = build_sequence(duration=duration, count=count, interval_ms=5000, video_id=1)
    cps = [e.cp for e in seq.events]
    # Strict monotonic at the boundaries, non-decreasing in general.
    assert cps[0] == 0.0
    assert cps[-1] == pytest.approx(duration, abs=0.01)
    for a, b in zip(cps, cps[1:]):
        assert b >= a


@pytest.mark.parametrize(
    "duration,count,expected_slope",
    [
        (30.0, 80, 30.0 / 395.0),
        (120.0, 80, 120.0 / 395.0),
        (395.0, 80, 1.0),
        (600.0, 80, 600.0 / 395.0),
        (1800.0, 80, 1800.0 / 395.0),
    ],
)
def test_implied_speed_exposed_for_each_canonical_duration(
    duration, count, expected_slope
):
    """The cp/ts slope is the parameter the audit demands be made visible.
    It is the *only* number that tells you what 'disguise' the design buys."""
    seq = build_sequence(duration=duration, count=count, interval_ms=5000, video_id=1)
    span_ms = seq.events[-1].ts_ms - seq.events[0].ts_ms
    span_s = span_ms / 1000.0
    cp_slope = (seq.events[-1].cp - seq.events[0].cp) / span_s
    assert cp_slope == pytest.approx(expected_slope, rel=1e-6)


def test_count_can_be_changed_to_keep_implied_speed_at_one():
    """If the user wants a 1x disguise, count must equal duration / interval_seconds.
    The harness exposes this rather than hiding it behind a magic 80."""
    target = 1.0
    duration = 600.0
    interval_s = 5.0
    count = int(round(duration / (target * interval_s))) + 1
    seq = build_sequence(duration=duration, count=count, interval_ms=5000, video_id=1)
    span_ms = seq.events[-1].ts_ms - seq.events[0].ts_ms
    span_s = span_ms / 1000.0
    cp_slope = (seq.events[-1].cp - seq.events[0].cp) / span_s
    assert cp_slope == pytest.approx(1.0, rel=1e-3)