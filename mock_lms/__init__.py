"""Local mock LMS for the telemetry-trust-boundary research harness.

This package implements a tiny HTTP server and an in-process state machine
that *only* exist to test client behavior against a *documented* protocol
model. See ``../docs/protocol-research-method.md``.

This server is not a clone of any vendor. It is a reference implementation
of the rules we are willing to study. If the real platform enforces
different rules, the harness's value is in showing exactly where the
client's assumptions diverge — not in claiming to bypass anything.
"""

from .app import MockLMSServer
from .state_machine import (
    ALLOWED_EVENT_TYPES,
    ET_ENDED,
    ET_HEARTBEAT,
    ET_PLAY,
    HeartbeatEvent,
    ServerState,
    process_event,
)

__all__ = [
    "ALLOWED_EVENT_TYPES",
    "ET_ENDED",
    "ET_HEARTBEAT",
    "ET_PLAY",
    "HeartbeatEvent",
    "MockLMSServer",
    "ServerState",
    "process_event",
]