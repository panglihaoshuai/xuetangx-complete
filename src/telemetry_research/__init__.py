"""Public entry point for the research harness."""

from .evidence import (
    Evidence,
    EvidenceLevel,
    Verdict,
    redact_text,
    tag,
)
from .models import HeartbeatEvent, HeartbeatSequence, MockResponse
from .sequence_builder import (
    ET_ENDED,
    ET_HEARTBEAT,
    ET_PLAY,
    InvalidParameterError,
    build_sequence,
)

__all__ = [
    "ET_ENDED",
    "ET_HEARTBEAT",
    "ET_PLAY",
    "Evidence",
    "EvidenceLevel",
    "HeartbeatEvent",
    "HeartbeatSequence",
    "InvalidParameterError",
    "MockResponse",
    "Verdict",
    "build_sequence",
    "redact_text",
    "tag",
]