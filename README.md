# Web Telemetry Trust-Boundary Research Harness

A local-only research harness for studying how a client-controlled
heartbeat-shaped telemetry protocol can drift away from a server's
intended acceptance rules. It does not interact with any real
platform.

## What this is

A Python package (`src/telemetry_research/`) that:

* Builds heartbeat sequences with explicit, parameterized math.
* Validates them against an in-process state machine (`mock_lms/`).
* Exposes the cp/ts slope of every sequence so the "disguise" the
  design actually buys is visible at a glance.
* Has a strict separation between *transport success* (`http_ok`)
  and *business acceptance* (`business_accepted`). The audit
  (`docs/audit-2026-06.md`) flags the conflation of these as the
  primary false-positive source.

A local mock LMS (`mock_lms/`) that:

* Listens on `127.0.0.1` only.
* Implements the contract documented in
  `docs/protocol-research-method.md`. It is not a clone of any
  vendor's server.
* Always returns HTTP 200 for well-formed requests but reports
  `business_accepted = false` with a stable `reason` code when the
  request violates the contract.

A test suite (`tests/`) that proves the invariants and that
parametrizes across the canonical durations the audit called out
(30 / 120 / 395 / 600 / 1800 seconds).

## What this is not

* Not a course-completion tool.
* Not a quiz solver.
* Not a discussion auto-poster.
* Not a clone or fork of any vendor's behavior.
* Not a tool that talks to any real platform. There is no
  entrypoint to do so, and the mock client refuses any URL that is
  not `127.0.0.1` or `localhost`.

## Provenance

This repository is the refactor of an earlier published project. The
audit (`docs/audit-2026-06.md`) explains what was found, what was
removed, and what was kept. The original scripts are quarantined in
`archived/legacy-research-notes/` with real identifiers replaced by
`[REDACTED-*]` tokens; they are not part of the public API.

## Quick start

```bash
# Clone
git clone <this repo>
cd <this repo>

# Install (Python 3.11+)
python3 -m pip install -e ".[test]"

# Run tests
python3 -m pytest -q
```

To run an interactive demo against the local mock LMS:

```python
from mock_lms import MockLMSServer
from telemetry_research import build_sequence
from telemetry_research.mock_client import post_sequence

server = MockLMSServer()
server.register(video_id=1, duration=120.0, expected_count=80)
server.start()

seq = build_sequence(
    duration=120.0,
    count=80,
    interval_ms=5000,
    video_id=1,
)
print("implied_speed:", seq.implied_speed())

responses = post_sequence(server.base_url, seq)
business_ok = all(r.business_accepted for r in responses)
print("business_ok:", business_ok)
```

## What was removed

The audit lists every removed capability. The short version:

* `brush_all.py` and the live-platform heartbeat injector.
* Auto-mark-image-text-finished by DOM mutation.
* Auto-submit discussion comments.
* Auto-answer homework questions.
* CDP auto-attach to a logged-in Chrome and drive it.
* Hard-coded live platform endpoints, cookie names, and CSRF usage.

The archived versions exist only for historical reference. They are
quarantined, desensitized, and not importable from `src/`.

## Repository layout

```
.
├── README.md                       # this file
├── SECURITY.md                     # security boundary
├── ETHICS.md                       # ethical boundary
├── pyproject.toml                  # package + tooling config
├── docs/
│   ├── audit-2026-06.md            # the audit that motivated this refactor
│   ├── protocol-research-method.md # the protocol model under test
│   ├── evidence-standard.md        # verdict / level vocabulary
│   └── responsible-disclosure-draft.md  # template only
├── src/
│   └── telemetry_research/
│       ├── __init__.py
│       ├── models.py               # dataclasses for events / responses
│       ├── sequence_builder.py     # builds heartbeat sequences
│       ├── validator.py            # invariant checks
│       ├── mock_client.py          # talks to 127.0.0.1 only
│       └── evidence.py             # redaction + evidence tagging
├── mock_lms/
│   ├── app.py                      # 127.0.0.1 HTTP server
│   ├── state_machine.py            # acceptance rules
│   └── README.md
├── tests/                          # 67 tests
│   ├── fixtures/                   # normal / invalid_timestamp /
│   │                               # invalid_progress / business_failure_200
│   ├── test_sequence_builder.py
│   ├── test_business_success.py
│   ├── test_false_positive_detection.py
│   ├── test_heartbeat_count_parametrized.py
│   ├── test_claim_consistency.py
│   ├── test_redaction.py
│   └── test_evidence.py
├── scripts/
│   └── redact_archived.py          # one-shot redaction helper
└── archived/
    └── legacy-research-notes/      # quarantined, desensitized
```

## Verifying the boundaries

```bash
# Tests must pass.
python3 -m pytest -q

# No real platform domain in executable source. The literal pattern is
# configured in tests/test_claim_consistency.py so this grep is illustrative.
grep -R "<real-domain-pattern>" src mock_lms tests scripts && echo "FAIL" || echo "ok"

# No real platform endpoint.
grep -R "<real-endpoint-pattern>" src mock_lms tests scripts && echo "FAIL" || echo "ok"

# README must not advertise discredited claims.
python3 -m pytest tests/test_claim_consistency.py -q
```

The third check is enforced as a test, not as a manual review, so it
catches regressions on every CI run.

## License

MIT. See the file `LICENSE` if present, or the SPDX header in
`pyproject.toml`.

## Acknowledgments

The audit was performed by the maintainer of this repository. The
original author of the upstream scripts is the same maintainer; the
audit is a self-audit. The `mock_lms` is original work for this
repository and does not derive from any vendor's code.