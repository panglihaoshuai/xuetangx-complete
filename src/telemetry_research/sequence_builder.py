"""Heartbeat sequence construction.

The original code at ``archived/legacy-research-notes/heartbeat.py`` uses
``time.sleep(0.05 + random.random() * 0.1)`` while forging
``ts = timestamp + i * 5000`` — a wall-clock rate that has no relationship
to the forged ``ts`` rate. The audit flagged this as P1-4.

This module separates the two concerns:

* :func:`build_sequence` constructs a sequence of heartbeat *events*.
  It does not sleep, it does not post to any server, and it does not
  touch any browser. It is pure-data construction.
* :class:`HeartbeatSequence.implied_speed` exposes the cp/ts slope so
  future engineers can see the disguise (or lack thereof) explicitly.

There is no entrypoint that calls a real HTTP endpoint. The audit
mandates that this module remain side-effect-free.
"""

from __future__ import annotations

from .models import HeartbeatEvent, HeartbeatSequence


class InvalidParameterError(ValueError):
    """Raised when sequence parameters are out of range."""


ET_PLAY = "play"
ET_HEARTBEAT = "heartbeat"
ET_ENDED = "ended"


def _validate(duration: float, count: int, interval_ms: int) -> None:
    if not isinstance(duration, (int, float)):
        raise InvalidParameterError(f"duration must be numeric, got {type(duration).__name__}")
    if duration <= 0:
        raise InvalidParameterError(f"duration must be positive, got {duration}")
    if not isinstance(count, int):
        raise InvalidParameterError(f"count must be int, got {type(count).__name__}")
    if count < 2:
        raise InvalidParameterError(f"count must be >= 2 (need at least play and ended), got {count}")
    if not isinstance(interval_ms, int):
        raise InvalidParameterError(f"interval_ms must be int, got {type(interval_ms).__name__}")
    if interval_ms <= 0:
        raise InvalidParameterError(f"interval_ms must be positive, got {interval_ms}")


def build_sequence(
    duration: float,
    count: int,
    interval_ms: int,
    video_id: int,
    *,
    sp: int = 1,
    ts_start_ms: int = 1_700_000_000_000,
) -> HeartbeatSequence:
    """Construct a heartbeat sequence.

    Parameters
    ----------
    duration:
        Total length of the video in seconds. Must be positive.
    count:
        Total number of events. Must be at least 2 (one ``play`` and one
        ``ended``).
    interval_ms:
        Milliseconds between successive events. Must be positive.
    video_id:
        Synthetic identifier for the target video. The harness treats this
        as opaque.
    sp:
        ``sp`` field on every event. Defaults to 1, matching the design
        assumption in the audit. Non-1 values are allowed but documented
        so reviewers can see when they occur.
    ts_start_ms:
        Initial ts in epoch milliseconds. Default is a synthetic 2023-11
        timestamp, not any real captured value.
    """
    _validate(duration, count, interval_ms)

    events: list[HeartbeatEvent] = []
    for i in range(count):
        et = (
            ET_PLAY if i == 0
            else ET_ENDED if i == count - 1
            else ET_HEARTBEAT
        )
        cp = round(duration * i / (count - 1), 3)
        ts_ms = ts_start_ms + i * interval_ms
        sq = i + 1
        events.append(
            HeartbeatEvent(
                video_id=video_id,
                seq=sq,
                et=et,
                cp=cp,
                ts_ms=ts_ms,
                sp=sp,
            )
        )
    return HeartbeatSequence(
        video_id=video_id,
        duration=duration,
        count=count,
        interval_ms=interval_ms,
        events=events,
    )