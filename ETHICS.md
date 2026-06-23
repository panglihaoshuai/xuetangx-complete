# ETHICS

This document is the ethical boundary for this repository.

## Position

The original published version of this project was a course-completion
tool that targeted a real platform using the user's logged-in browser
session. The audit (`docs/audit-2026-06.md`) rated that version
`MISLEADING_IMPLEMENTATION` and identified several critical defects in
both the technical claims and the operation.

The audit also established that, even if every claim in the original
README had been true, the tool would still be a violation of the
target platform's terms of service. Automating completion of paid or
graded coursework in someone else's name, regardless of how cleverly,
is misrepresentation.

This repository therefore does not, and will not, contain executable
code that targets a real platform. This is not a research disclaimer
that excuses specific exceptions; it is a hard rule.

## What "research" means here

This repository is allowed to exist because:

1. It builds a *model* of the heartbeat protocol from the published
   audit data, not from any new probe of the live platform.
2. It runs that model against a local mock LMS that is implemented in
   this same repository.
3. It documents its assumptions and limits. The audit document is the
   primary artifact; the code is the secondary one.

## What "research" does not mean here

It does not mean:

* "We will release a paper that includes a working bypass." — We will
  not. The harness is a model under test, not a probe.
* "We will issue a CVE on the real platform." — Out of scope. The
  audit was internal to this repository.
* "It is okay to keep the live-platform scripts in `archived/` if
  someone really wants them." — They are quarantined for historical
  reference only and they are desensitized. They will not be made
  runnable.

## Who this is for

* Researchers studying client-trust telemetry protocols.
* Engineers building trust-boundary instrumentation.
* Educators demonstrating how a poorly-specified protocol allows
  fabricated progress events.

## Who this is not for

* Students seeking to skip coursework.
* Operators seeking to bypass course completion rules.
* Anyone who wants a working tool against a real platform. There is
  none in this repository.

## If you find a real vulnerability

You have two reasonable choices:

1. Do nothing. The audit did not promise disclosure, and the
   target platform is out of scope for this project.
2. Report it directly to the platform's security contact using
   `docs/responsible-disclosure-draft.md` as a template, **without
   referencing this repository**.

The repository does not endorse option 2 and does not facilitate it.