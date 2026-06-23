"""Tests for heartbeat sequence construction.

These tests intentionally fail before src/telemetry_research/sequence_builder.py
is implemented (TDD red phase).
"""
from __future__ import annotations

import pytest

from telemetry_research.sequence_builder import (
    HeartbeatSequence,
    InvalidParameterError,
    build_sequence,
)


def test_build_sequence_returns_n_events():
    seq = build_sequence(duration=120.0, count=80, interval_ms=5000, video_id=1)
    assert isinstance(seq, HeartbeatSequence)
    assert len(seq.events) == 80


@pytest.mark.parametrize("duration", [30.0, 120.0, 395.0, 600.0, 1800.0])
def test_build_sequence_timestamps_strictly_monotonic(duration):
    seq = build_sequence(duration=duration, count=80, interval_ms=5000, video_id=1)
    timestamps = [e.ts_ms for e in seq.events]
    assert all(b > a for a, b in zip(timestamps, timestamps[1:])), (
        f"timestamps not strictly monotonic for duration={duration}"
    )


@pytest.mark.parametrize("duration", [30.0, 120.0, 395.0, 600.0, 1800.0])
def test_build_sequence_cp_non_decreasing(duration):
    seq = build_sequence(duration=duration, count=80, interval_ms=5000, video_id=1)
    cps = [e.cp for e in seq.events]
    assert all(b >= a for a, b in zip(cps, cps[1:])), (
        f"cp not non-decreasing for duration={duration}"
    )


@pytest.mark.parametrize("duration", [30.0, 120.0, 395.0, 600.0, 1800.0])
def test_build_sequence_cp_within_duration(duration):
    seq = build_sequence(duration=duration, count=80, interval_ms=5000, video_id=1)
    assert seq.events[0].cp == 0.0
    assert seq.events[-1].cp == pytest.approx(duration, abs=0.01)


def test_build_sequence_event_types_play_then_heartbeat_then_ended():
    seq = build_sequence(duration=120.0, count=80, interval_ms=5000, video_id=1)
    assert seq.events[0].et == "play"
    assert seq.events[-1].et == "ended"
    assert all(e.et == "heartbeat" for e in seq.events[1:-1])


def test_build_sequence_sq_starts_at_one_and_increments_by_one():
    seq = build_sequence(duration=120.0, count=80, interval_ms=5000, video_id=1)
    sqs = [e.seq for e in seq.events]
    assert sqs[0] == 1
    assert sqs == list(range(1, 81))


def test_build_sequence_rejects_count_less_than_two():
    with pytest.raises(InvalidParameterError):
        build_sequence(duration=120.0, count=1, interval_ms=5000, video_id=1)


def test_build_sequence_rejects_zero_duration():
    with pytest.raises(InvalidParameterError):
        build_sequence(duration=0.0, count=80, interval_ms=5000, video_id=1)


def test_build_sequence_rejects_negative_duration():
    with pytest.raises(InvalidParameterError):
        build_sequence(duration=-1.0, count=80, interval_ms=5000, video_id=1)


def test_build_sequence_rejects_zero_interval():
    with pytest.raises(InvalidParameterError):
        build_sequence(duration=120.0, count=80, interval_ms=0, video_id=1)


def test_build_sequence_first_event_sp_must_be_one():
    """sp=1 is the documented 'disguise' assumption. Document, don't enforce."""
    seq = build_sequence(
        duration=120.0, count=80, interval_ms=5000, video_id=1, sp=1
    )
    assert all(e.sp == 1 for e in seq.events)