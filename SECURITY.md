# SECURITY

This document is the security boundary for this repository. It is
deliberately short.

## What this repository is

A *Web Telemetry Trust-Boundary Research Harness*. It models a
documented heartbeat-shaped protocol locally and tests client behavior
against that local model.

## What this repository is not

A tool that interacts with any real platform. There is no entrypoint
that talks to any vendor's server. The original `brush_all.py` and
companion scripts that did so have been moved to
`archived/legacy-research-notes/` and quarantined.

## Hard rules

1. **No network egress.** The mock LMS binds `127.0.0.1` only. The
   `mock_client` module refuses any URL that is not `127.0.0.1` or
   `localhost`. Any code change that relaxes this is a security
   regression and must be reverted.
2. **No real identifiers in the public surface.** Every committed
   `.py`, `.md`, `.json`, `.toml`, `.yaml` under `src/`, `mock_lms/`,
   `tests/`, `docs/`, and the top level is scanned for the real
   platform's domain, its API path patterns, the `cc` fingerprint,
   user-id patterns, course-id patterns, classroom-id patterns, and
   tenant-sign patterns. See `tests/test_redaction.py` and
   `tests/test_claim_consistency.py` for the exact set of tokens.
3. **No new "research" capabilities that target a real platform.**
   If you discover a behavior on a real platform, document it in
   `docs/audit-*.md` and stop. The harness is a model, not a probe.
4. **No `eval()` on user-derived data.** The audit flagged
   `homework.py:69` for this. If you need to parse JSON, use `json.loads`.
5. **No bare `except:` clauses.** They swallow errors silently and
   mask the exact failure modes the audit identified.

## Reporting a security issue

See `SECURITY.md` at the top of this repository. For the prototype
stage, there is no formal disclosure program; please open a GitHub
issue or contact the maintainers directly.

## Threat model (out of scope)

This repository does not defend against:

* Compromised dependencies in the test environment.
* Local privilege escalation on the developer's machine.
* A motivated user repointing `mock_client` at a real URL by editing
  the source. The constant `_assert_local` is a guardrail, not a
  security boundary.

The repository is not a security product. It is a research tool.