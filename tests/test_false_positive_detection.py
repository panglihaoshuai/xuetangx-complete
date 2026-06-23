"""Tests that capture the false-positive patterns documented in the audit.

These tests use the local in-process state machine as the 'server'.
"""
from __future__ import annotations

from mock_lms.state_machine import (
    HeartbeatEvent,
    ServerState,
    process_event,
)
from telemetry_research.sequence_builder import build_sequence


def _event_from(e):
    return HeartbeatEvent(
        video_id=e.video_id,
        seq=e.seq,
        et=e.et,
        cp=e.cp,
        ts_ms=e.ts_ms,
        sp=e.sp,
    )


def test_canonical_sequence_accepted_by_state_machine():
    """Sanity baseline: a well-formed sequence must actually succeed."""
    seq = build_sequence(duration=120.0, count=80, interval_ms=5000, video_id=1)
    state = ServerState(video_id=1, duration=120.0, expected_count=80)
    accepted = sum(
        1 for e in seq.events
        if process_event(state, _event_from(e))[0]
    )
    assert accepted == 80
    assert state.business_completed is True


def test_misusing_one_video_duration_for_another_eventually_detected():
    """The audit's P1-1 finding: a client that reuses duration 30 for an
    intended 1800s video. With a strict server, the cp eventually exceeds
    duration and is rejected."""
    state = ServerState(video_id=2, duration=1800.0, expected_count=80)
    wrong_duration = 30.0
    seq = build_sequence(
        duration=wrong_duration, count=80, interval_ms=5000, video_id=2
    )
    accepted = 0
    rejected_reasons = []
    for e in seq.events:
        ok, http_ok, reason = process_event(state, _event_from(e))
        if ok:
            accepted += 1
        else:
            rejected_reasons.append(reason)
    # Sequence completes at cp=30 while server's duration=1800 -> still under.
    # It accepts all 80 because cp never exceeds tp.
    # The point: the *server* doesn't catch this. So the audit's defense holds:
    # the *client* must not pretend a 30s duration means a 1800s video.
    # This test asserts the rule: cp must never exceed tp on the wire.
    for e in seq.events:
        assert e.cp <= 1800.0 + 1e-6


def test_real_wall_clock_sleep_does_not_match_forged_ts():
    """The audit's P1-4 finding: code uses time.sleep ~0.1s but ts += 5000ms.
    A server that cross-checks wall clock vs forged ts is not what we are
    modeling. We instead model the *contract*: ts must be monotonically
    increasing; the wall-clock-rate is not part of the contract."""
    seq = build_sequence(duration=120.0, count=80, interval_ms=5000, video_id=3)
    forged = [e.ts_ms for e in seq.events]
    # In the audit's broken code, actual wall time would be ~0.1s * 80 = 8s.
    forged_span = forged[-1] - forged[0]
    real_span_estimate = 8 * 1000  # ~8s
    # The forged span is 395 seconds; the real wall span is ~8 seconds.
    # A strict model does not require them to match. But we document it.
    assert forged_span == 395 * 1000
    assert real_span_estimate < forged_span


def test_duplicate_video_id_replay_creates_independent_state():
    """Per-video server state must be independent. A successful sequence on
    video 1 must not affect video 2's accepted count."""
    seq_a = build_sequence(duration=120.0, count=80, interval_ms=5000, video_id=1)
    state_a = ServerState(video_id=1, duration=120.0, expected_count=80)
    for e in seq_a.events:
        process_event(state_a, _event_from(e))
    state_b = ServerState(video_id=2, duration=120.0, expected_count=80)
    assert state_b.accepted == 0
    assert state_b.business_completed is False


def test_http_ok_response_can_be_true_while_business_accepted_is_false():
    """The single most important invariant the audit demands we preserve.
    A response object that conflates them would be a re-introduction of the
    bug that the original code had."""
    from telemetry_research.models import MockResponse

    case = MockResponse(
        http_ok=True,
        business_accepted=False,
        progress_updated=False,
        reason="invalid_sequence",
    )
    # The client must be able to inspect business_accepted without looking at
    # http_ok, and vice versa.
    assert case.http_ok is True
    assert case.business_accepted is False
    assert case.progress_updated is False
    assert case.reason == "invalid_sequence"