"""Pure-Python state machine for heartbeat acceptance.

This is the local mock-LMS server's decision core. It is intentionally
small, dependency-free, and deterministic so that tests can pin behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Event type constants. Names match the field observed in the audit.
ET_PLAY = "play"
ET_HEARTBEAT = "heartbeat"
ET_ENDED = "ended"

ALLOWED_EVENT_TYPES = {ET_PLAY, ET_HEARTBEAT, ET_ENDED}


@dataclass(frozen=True)
class HeartbeatEvent:
    """A single heartbeat event submitted by the client."""

    video_id: int
    seq: int
    et: str
    cp: float
    ts_ms: int
    sp: int


@dataclass
class ServerState:
    """Per-video server state."""

    video_id: int
    duration: float
    expected_count: int
    accepted: int = 0
    rejected: int = 0
    last_ts_ms: int | None = None
    last_cp: float | None = None
    last_reason: str = ""
    seen_sq: set = field(default_factory=set)
    business_completed: bool = False

    def reset(self) -> None:
        self.accepted = 0
        self.rejected = 0
        self.last_ts_ms = None
        self.last_cp = None
        self.last_reason = ""
        self.seen_sq = set()
        self.business_completed = False


def process_event(
    state: ServerState, event: HeartbeatEvent
) -> tuple[bool, bool, str]:
    """Apply a single event to the state machine.

    Returns ``(accepted, http_ok, reason)``:

    * ``accepted`` is the *business* decision (True/False).
    * ``http_ok`` is the transport decision. The mock returns 200 for any
      well-formed event, including rejected ones. This separation is the
      whole point of the harness — clients must distinguish the two.
    * ``reason`` is a stable string code useful for assertions; empty when
      ``accepted`` is True.
    """
    # Transport-layer check is independent: malformed events are not even
    # transport-valid. For well-formed inputs we always report http_ok=True.
    http_ok = _transport_valid(event)
    if not http_ok:
        state.rejected += 1
        state.last_reason = "transport_invalid"
        return False, False, state.last_reason

    if event.et not in ALLOWED_EVENT_TYPES:
        state.rejected += 1
        state.last_reason = "unknown_event_type"
        return False, True, state.last_reason

    if event.video_id != state.video_id:
        state.rejected += 1
        state.last_reason = "video_id_mismatch"
        return False, True, state.last_reason

    if event.seq in state.seen_sq:
        state.rejected += 1
        state.last_reason = "duplicate_sq"
        return False, True, state.last_reason

    if state.last_ts_ms is not None and event.ts_ms <= state.last_ts_ms:
        state.rejected += 1
        state.last_reason = "ts_not_monotonic"
        return False, True, state.last_reason

    if state.last_cp is not None and event.cp < state.last_cp:
        state.rejected += 1
        state.last_reason = "cp_not_monotonic"
        return False, True, state.last_reason

    if event.cp > state.duration + 1e-6:
        state.rejected += 1
        state.last_reason = "cp_exceeds_duration"
        return False, True, state.last_reason

    if event.sp != 1:
        state.rejected += 1
        state.last_reason = "sp_must_be_one"
        return False, True, state.last_reason

    if event.et == ET_ENDED:
        # An "ended" event must be the *final* event in the contract.
        # If the client sends it earlier than expected, the server rejects.
        if event.seq < state.expected_count:
            state.rejected += 1
            state.last_reason = "ended_too_early"
            return False, True, state.last_reason
        if event.cp < state.duration - 1e-6:
            state.rejected += 1
            state.last_reason = "ended_below_duration"
            return False, True, state.last_reason

    # Acceptance: update state.
    state.accepted += 1
    state.seen_sq.add(event.seq)
    state.last_ts_ms = event.ts_ms
    state.last_cp = event.cp
    state.last_reason = ""

    if (
        event.et == ET_ENDED
        and state.accepted == state.expected_count
        and abs(event.cp - state.duration) <= 1e-6
    ):
        state.business_completed = True

    return True, True, ""


def _transport_valid(event: HeartbeatEvent) -> bool:
    """Minimum transport-shape checks. Not a real HTTP parser."""
    return event.seq > 0 and event.ts_ms > 0 and event.cp >= 0


# A test-friendly bulk helper. Not used by the harness HTTP layer.
def process_many(
    state: ServerState, events: list[HeartbeatEvent]
) -> list[tuple[bool, bool, str]]:
    return [process_event(state, e) for e in events]