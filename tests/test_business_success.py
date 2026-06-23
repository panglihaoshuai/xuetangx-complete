"""Tests proving that http_ok != business success.

Driven by a local in-process state machine (mock_lms.state_machine.StateMachine).
"""
from __future__ import annotations

import pytest

from mock_lms.state_machine import (
    HeartbeatEvent,
    ServerState,
    process_event,
)
from telemetry_research.models import MockResponse


def _mk_event(seq: int, et: str, cp: float, ts_ms: int, video_id: int = 1) -> HeartbeatEvent:
    return HeartbeatEvent(
        video_id=video_id,
        seq=seq,
        et=et,
        cp=cp,
        ts_ms=ts_ms,
        sp=1,
    )


def test_valid_sequence_results_in_business_success():
    state = ServerState(video_id=1, duration=120.0, expected_count=80)
    accepted = 0
    for i in range(80):
        et = "play" if i == 0 else ("ended" if i == 79 else "heartbeat")
        cp = round(120.0 * i / 79, 3)
        ts_ms = 1700000000000 + i * 5000
        ok, _, _ = process_event(state, _mk_event(i + 1, et, cp, ts_ms))
        if ok:
            accepted += 1
    assert accepted == 80
    assert state.business_completed is True


def test_inverted_timestamp_returns_business_rejected_with_http_ok_shape():
    """http_ok is at the transport layer. Even if the transport returns 200,
    the business layer must report a rejection."""
    state = ServerState(video_id=2, duration=60.0, expected_count=10)
    accepted = 0
    rejected = 0
    # Build the per-iteration ts explicitly so the inversion is unambiguous.
    ts_sequence = [
        1700000000000,  # i=0 play
        1700000005000,  # i=1
        1700000010000,  # i=2
        1700000015000,  # i=3
        1700000014000,  # i=4 BACKWARDS (must reject)
        1700000020000,  # i=5
        1700000025000,  # i=6
        1700000030000,  # i=7
        1700000035000,  # i=8
        1700000040000,  # i=9 ended
    ]
    for i, ts_ms in enumerate(ts_sequence):
        et = "play" if i == 0 else ("ended" if i == 9 else "heartbeat")
        cp = round(60.0 * i / 9, 3)
        ok, http_ok, reason = process_event(
            state, _mk_event(i + 1, et, cp, ts_ms, video_id=2)
        )
        if ok:
            accepted += 1
        else:
            rejected += 1

    # The first 4 events accepted, the 5th (backwards ts) rejected, then accepted again.
    assert rejected == 1
    assert accepted == 9
    assert state.business_completed is False  # never reached ended cleanly


def test_cp_backwards_returns_rejected():
    state = ServerState(video_id=3, duration=60.0, expected_count=6)
    ok, http_ok, reason = process_event(
        state, _mk_event(1, "play", 0.0, 1700000000000, video_id=3)
    )
    assert ok is True
    ok, http_ok, reason = process_event(
        state, _mk_event(2, "heartbeat", 12.0, 1700000005000, video_id=3)
    )
    assert ok is True
    ok, http_ok, reason = process_event(
        state, _mk_event(3, "heartbeat", 24.0, 1700000010000, video_id=3)
    )
    assert ok is True
    # now backwards
    ok, http_ok, reason = process_event(
        state, _mk_event(4, "heartbeat", 18.0, 1700000015000, video_id=3)
    )
    assert ok is False
    assert http_ok is True
    assert reason == "cp_not_monotonic"


def test_mock_response_model_separates_http_ok_and_business_accepted():
    """The mock response object must expose http_ok and business_accepted as
    independent boolean fields. Treating one as a substitute for the other is
    exactly the failure mode the audit flagged."""
    resp = MockResponse(
        http_ok=True,
        business_accepted=False,
        progress_updated=False,
        reason="invalid_sequence",
    )
    assert resp.http_ok is True
    assert resp.business_accepted is False
    # The combination is a legitimate outcome: 200 OK, business rejected.
    assert (resp.http_ok, resp.business_accepted) == (True, False)


def test_replay_of_same_sq_returns_rejected():
    state = ServerState(video_id=4, duration=60.0, expected_count=5)
    ok, _, _ = process_event(
        state, _mk_event(1, "play", 0.0, 1700000000000, video_id=4)
    )
    assert ok is True
    ok, _, _ = process_event(
        state, _mk_event(1, "play", 0.0, 1700000005000, video_id=4)
    )
    assert ok is False
    assert state.last_reason == "duplicate_sq"


def test_ended_before_canonical_completion_returns_rejected():
    """The state machine must not accept 'ended' unless enough progress has
    actually been reported and the count meets the contract."""
    state = ServerState(video_id=5, duration=600.0, expected_count=80)
    ok, _, _ = process_event(
        state, _mk_event(1, "play", 0.0, 1700000000000, video_id=5)
    )
    assert ok is True
    ok, _, reason = process_event(
        state, _mk_event(2, "ended", 600.0, 1700000005000, video_id=5)
    )
    assert ok is False
    assert reason == "ended_too_early"


@pytest.mark.parametrize("duration", [30.0, 120.0, 395.0, 600.0, 1800.0])
def test_fixed_count_parametrization_makes_implied_speed_explicit(duration):
    """For each canonical duration, compute the cp/ts slope the server would
    observe. This is *not* a server decision; it's a property of the chosen
    count. The harness exposes it so future engineers can see what 'disguise'
    the design actually buys."""
    from telemetry_research.sequence_builder import build_sequence

    seq = build_sequence(duration=duration, count=80, interval_ms=5000, video_id=1)
    cp_slope = (seq.events[-1].cp - seq.events[0].cp) / (
        (seq.events[-1].ts_ms - seq.events[0].ts_ms) / 1000.0
    )
    # cp_slope has units 'cp-units per real-second-of-ts'
    # When cp_slope == 1.0, the design claims '1x disguise'.
    assert cp_slope == pytest.approx(duration / 395.0, rel=1e-6)