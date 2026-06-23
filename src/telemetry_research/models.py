"""Data models for the research harness.

These are deliberately small, dependency-free dataclasses so that fixtures
can be loaded with stdlib ``json`` and compared with ``dataclasses.asdict``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class HeartbeatEvent:
    """A single heartbeat event as the *client* would construct it.

    Field names match the protocol model documented in
    ``docs/protocol-research-method.md``. They do not match any real
    vendor's wire format and are not derived from server-side reverse
    engineering.
    """

    video_id: int
    seq: int
    et: str
    cp: float
    ts_ms: int
    sp: int = 1

    def to_form(self) -> dict[str, str]:
        """Encode as application/x-www-form-urlencoded values."""
        return {
            "video_id": str(self.video_id),
            "seq": str(self.seq),
            "et": self.et,
            "cp": str(self.cp),
            "ts_ms": str(self.ts_ms),
            "sp": str(self.sp),
        }


@dataclass(frozen=True)
class HeartbeatSequence:
    """A complete heartbeat sequence built by ``build_sequence``."""

    video_id: int
    duration: float
    count: int
    interval_ms: int
    events: list[HeartbeatEvent]

    def implied_speed(self) -> float:
        """cp-units per real-second of ts.

        The audit demands this number be visible. It tells you what
        'disguise' the design actually buys: 1.0 means cp moves at the same
        rate as ts; values > 1.0 mean cp races ahead; values < 1.0 mean cp
        lags. ``sp`` is a separate field that the server *could* check but
        this model does not pretend to model how any real server enforces.
        """
        span_ms = self.events[-1].ts_ms - self.events[0].ts_ms
        if span_ms <= 0:
            return 0.0
        return (self.events[-1].cp - self.events[0].cp) / (span_ms / 1000.0)


@dataclass(frozen=True)
class MockResponse:
    """The response shape produced by the mock LMS.

    The four fields are deliberately independent. The audit's primary P1
    defect was conflating them.
    """

    http_ok: bool
    business_accepted: bool
    progress_updated: bool
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)