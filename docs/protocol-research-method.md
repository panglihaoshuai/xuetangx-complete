# Protocol Research Method

This document specifies the *model* the harness implements. It does not
describe any real vendor's server.

## 1. Model

A heartbeat-shaped client emits a sequence of events for one
synthetic video. Each event carries:

| Field   | Type   | Meaning                                   |
|---------|--------|-------------------------------------------|
| seq     | int    | Per-video sequence number, starts at 1.  |
| video_id| int    | Opaque target identifier.                 |
| et      | string | One of: `play`, `heartbeat`, `ended`.     |
| cp      | float  | Cumulative progress in seconds.           |
| ts_ms   | int    | Synthetic wall-clock ms, monotonic.       |
| sp      | int    | Speed claim. Defaults to 1.               |

The full sequence for one video is exactly:

```
event 1:    et=play,        cp=0
event 2..N-1: et=heartbeat, cp=cp(i)
event N:    et=ended,       cp=duration
```

where `cp(i) = duration * i / (count - 1)` and `ts_ms(i) = ts_start + i * interval_ms`.

## 2. Acceptance rules

The mock LMS accepts an event when *all* of:

1. `seq > 0` and `seq` has not been seen before for this video.
2. `ts_ms` is strictly greater than the previously accepted `ts_ms`.
3. `cp` is non-decreasing relative to the previously accepted `cp`.
4. `cp <= duration + epsilon`.
5. `sp == 1`.
6. `et` is one of the three allowed types.
7. If `et == ended`, then `seq == count` and `cp ≈ duration`.

Any violation is reported as `business_accepted = false` with a
stable `reason` code. The transport layer (`http_ok`) returns `true`
regardless — that is the entire point of separating the two.

## 3. What is NOT modeled

This model deliberately does not model:

* Any vendor's actual server-side validation logic.
* Network latency, retries, idempotency keys, or signed requests.
* CAPTCHA, browser fingerprinting, or behavior analysis.
* Cross-video consistency checks.
* Server-side `ts_ms` versus wall-clock comparisons.

If you want to claim the mock matches a real server, you are out of
scope. The mock is a *reference implementation of the contract the
client is willing to assume*. The audit's P1 finding is that the
client and the real server do not actually agree on every detail.

## 4. Why `implied_speed` is exposed

The harness exposes `HeartbeatSequence.implied_speed()` returning the
cp/ts slope of the sequence. This is the *only* number that tells
you what "disguise" the sequence actually buys. With the canonical
audit construction (`count=80`, `interval_ms=5000`):

| duration | implied_speed |
|----------|---------------|
| 30       | 0.076x        |
| 120      | 0.304x        |
| 395      | 1.000x        |
| 600      | 1.519x        |
| 1800     | 4.557x        |

A 1.0x "disguise" only happens at exactly `duration == 395 s`. Other
durations either understate or overstate the implied rate.

## 5. Reproducing an experiment

```python
from telemetry_research import build_sequence
from mock_lms import MockLMSServer

server = MockLMSServer()
server.register(video_id=1, duration=120.0, expected_count=80)
server.start()

seq = build_sequence(
    duration=120.0,
    count=80,
    interval_ms=5000,
    video_id=1,
)

from telemetry_research.mock_client import post_sequence
responses = post_sequence(server.base_url, seq)

business_ok = all(r.business_accepted for r in responses)
print(business_ok, seq.implied_speed())
```

This produces a deterministic result against the local mock LMS. It
does not contact any external server.

## 6. Boundaries of the method

* The harness is a model. It cannot prove anything about the real
  platform.
* The harness cannot reproduce server-side detection rules because
  those are not published.
* The harness cannot reproduce cross-account behaviors.
* The harness is appropriate for *unit-level* client reasoning, not
  for predicting platform behavior.

## 7. Future work (out of scope here)

These are explicitly *not* in this repository's roadmap:

* Recording real traffic.
* Fuzzing real endpoints.
* Issuing cross-account probes.
* Bypassing any client fingerprinting.