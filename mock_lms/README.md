# mock_lms

A local-only mock LMS server. Listens on `127.0.0.1` and implements
the contract documented in `../docs/protocol-research-method.md`.

## Components

* `state_machine.py` — `ServerState`, `process_event`. The decision
  core. Returns a tuple `(accepted, http_ok, reason)` so callers can
  distinguish transport success from business acceptance.
* `app.py` — `MockLMSServer`. Thin wrapper around `http.server` that
  binds the state machine to two routes: `POST /heartbeat` and
  `GET /state/{id}`.

## Endpoints

### POST /heartbeat

Body: `application/x-www-form-urlencoded` with these fields:

| Field    | Type | Example   |
|----------|------|-----------|
| video_id | int  | 1         |
| seq      | int  | 1         |
| et       | str  | play      |
| cp       | float| 0.0       |
| ts_ms    | int  | 1700000000000 |
| sp       | int  | 1         |

Response (always HTTP 200 when the form is parseable):

```json
{
  "http_ok": true,
  "business_accepted": true,
  "progress_updated": true,
  "reason": "",
  "video_id": 1,
  "seq": 1,
  "state": {
    "accepted": 1,
    "rejected": 0,
    "business_completed": false,
    "last_cp": 0.0
  }
}
```

### GET /state/{video_id}

Returns the current `ServerState` snapshot for the video. Useful in
tests that want to assert progress without parsing 80 individual
responses.

## What the mock does NOT do

* Bind any address other than `127.0.0.1`.
* Validate CSRF tokens, cookies, or browser fingerprints.
* Compare `ts_ms` against real wall-clock time.
* Persist state across restarts.
* Replay, deduplicate by IP, or rate-limit by client.

These are deliberately out of scope. The audit
(`../docs/audit-2026-06.md`) explains why modeling them would
require making claims we are not willing to make.

## Usage

```python
from mock_lms import MockLMSServer

server = MockLMSServer()
server.register(video_id=1, duration=120.0, expected_count=80)
server.start()
print(server.base_url)  # http://127.0.0.1:<random-port>

# In tests:
# - construct a sequence with telemetry_research.sequence_builder
# - post each event to server.base_url/heartbeat
# - assert on the per-event responses
```

The test suite in `../tests/` does exactly this.