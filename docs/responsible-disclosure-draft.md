# Responsible Disclosure Draft (Template Only)

This is a **template only**. This repository does not run a
disclosure program and does not encourage using this template to
disclose vulnerabilities to the platform audited here.

If you independently discover a real-world vulnerability in a real
platform's telemetry protocol, the usual responsible-disclosure
guidance applies: report it to the platform's security contact
through whatever channel they publish. **Do not** route the
disclosure through this repository.

## Template

```
To: <platform security contact, e.g. security@<vendor>>
Subject: Vulnerability report — heartbeat-shaped telemetry protocol

Hello,

I am writing to report a finding in the heartbeat-shaped telemetry
protocol that <platform> uses to record client playback progress.

Summary
-------
The protocol accepts progress events whose:
- `ts_ms` values are client-controlled and not validated against
  the server's wall clock.
- `cp` values are client-controlled and not validated against the
  real media timeline.
- sequence numbers are not bound to a server-issued nonce.

As a result, a client can submit a sequence of events that the
server records as 100% completion without the underlying media
ever being played.

Reproduction
------------
Performed in an authorized test environment with synthetic data.
No real user accounts, real course IDs, or real progress records
were involved. The reproduction used a local mock that implements
the documented protocol contract; a real-vendor reproduction was
NOT performed.

Impact
------
A client could falsely report playback completion. This affects
the integrity of any analytics, completion records, or grading
that depend on the protocol.

Suggested mitigation
--------------------
1. Bind `ts_ms` to a server-issued monotonic nonce.
2. Validate `cp` against a server-side media timeline.
3. Require a server-issued signed request for the `ended` event.

Disclosure preferences
----------------------
- I am happy to coordinate disclosure timing.
- I will not publicly disclose until you have a fix or 90 days,
  whichever comes first.
- I prefer to be credited by name / anonymously / not at all.

Thank you,
<name>
<contact>
```

## What is NOT in this template

* A claim that this repository has reproduced the issue against the
  real platform. It has not. The model in
  `docs/protocol-research-method.md` is documented but does not
  match any real vendor's wire format.
* Encouragement to test against the real platform. The audit
  (`docs/audit-2026-06.md`) is explicit that this is out of scope.
* A claim that anyone on this project will help you submit. The
  project does not facilitate disclosure.