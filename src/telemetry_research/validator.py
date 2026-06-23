"""Validator: re-exports and additional rule helpers."""

from __future__ import annotations

from .models import HeartbeatEvent, HeartbeatSequence


class ValidationFailure(AssertionError):
    """Raised when a sequence violates an invariant."""


def check_ts_strictly_monotonic(events: list[HeartbeatEvent]) -> None:
    timestamps = [e.ts_ms for e in events]
    for a, b in zip(timestamps, timestamps[1:]):
        if not (b > a):
            raise ValidationFailure(
                f"timestamp not strictly increasing: {a} -> {b}"
            )


def check_cp_non_decreasing(events: list[HeartbeatEvent]) -> None:
    cps = [e.cp for e in events]
    for a, b in zip(cps, cps[1:]):
        if b < a:
            raise ValidationFailure(f"cp decreased: {a} -> {b}")


def check_cp_within_duration(sequence: HeartbeatSequence) -> list[tuple[int, float]]:
    """Return a list of (index, cp) for any event whose cp exceeds the
    sequence's duration. An empty list means clean."""
    return [
        (i, e.cp)
        for i, e in enumerate(sequence.events)
        if e.cp > sequence.duration + 1e-6
    ]


def check_event_types(events: list[HeartbeatEvent]) -> None:
    if not events:
        raise ValidationFailure("empty event list")
    if events[0].et != "play":
        raise ValidationFailure(f"first event must be 'play', got {events[0].et!r}")
    if events[-1].et != "ended":
        raise ValidationFailure(f"last event must be 'ended', got {events[-1].et!r}")
    for e in events[1:-1]:
        if e.et != "heartbeat":
            raise ValidationFailure(
                f"middle event has non-heartbeat et={e.et!r} at seq={e.seq}"
            )