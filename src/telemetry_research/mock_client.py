"""Mock client used in tests and in manual REPL sessions.

This client talks to a *local* mock LMS. It is intentionally not a generic
HTTP client: it never accepts a URL pointing at any real platform, and it
refuses to construct a request unless the destination host is 127.0.0.1 or
localhost.
"""

from __future__ import annotations

from collections.abc import Iterable

from .models import HeartbeatEvent, HeartbeatSequence, MockResponse


class DestinationRejected(ValueError):
    """Raised when the destination URL points outside the local mock LMS."""


def _assert_local(url: str) -> None:
    lowered = url.lower()
    if "127.0.0.1" not in lowered and "localhost" not in lowered:
        raise DestinationRejected(
            f"refusing to send to non-local destination: {url}"
        )


def post_one(base_url: str, event: HeartbeatEvent) -> MockResponse:
    """POST a single event to the local mock LMS and parse the response."""
    _assert_local(base_url)
    import json
    import urllib.parse
    import urllib.request

    body = urllib.parse.urlencode(event.to_form()).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/heartbeat",
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        raw = resp.read().decode("utf-8")
    parsed = json.loads(raw)
    return MockResponse(
        http_ok=bool(parsed.get("http_ok")),
        business_accepted=bool(parsed.get("business_accepted")),
        progress_updated=bool(parsed.get("progress_updated")),
        reason=str(parsed.get("reason", "")),
    )


def post_sequence(base_url: str, sequence: HeartbeatSequence) -> list[MockResponse]:
    """POST an entire sequence, returning per-event responses.

    The audit's primary concern is the conflation of transport success
    with business success. This helper returns the full per-event response
    list so callers can compute their own success metric.
    """
    _assert_local(base_url)
    return [post_one(base_url, e) for e in sequence.events]


def is_business_success(responses: Iterable[MockResponse]) -> bool:
    """Whether *every* event in the sequence was accepted at the business
    layer. Transport success is necessary but not sufficient."""
    responses = list(responses)
    return bool(responses) and all(r.business_accepted for r in responses)