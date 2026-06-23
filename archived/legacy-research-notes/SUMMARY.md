> **ARCHIVED — NOT EXECUTABLE.** This document is preserved for
> historical reference only. It is a high-level summary, not a
> guide. Real-platform identifiers have been replaced with
> `[REDACTED-*]` tokens.

# Archived Legacy Research Notes — Summary

This document is the **only** legacy material retained in the public
repository. The original operational scripts and step-by-step notes
were deleted during the public safety review because they constituted
operational implementations, not historical notes. Keeping them in
`archived/` was not sufficient to make them safe to publish.

What follows is a *defect catalog* and a *category summary* — both at
the level of "what the script was for" and "what was wrong with it",
without the code that would let someone re-run the original.

## Categories removed

The upstream repository, as captured at HEAD
`[REDACTED-COMMIT]`, contained seven executable scripts that, taken
together, formed a live course-completion tool. They have been
deleted.

| Script | Category | Defect summary |
|--------|----------|----------------|
| (script 1) | Heartbeat injection against a real platform | Used the current page's `<video>` duration for every video ID; treated HTTP 200 as business success; ran 80 forged-timestamp heartbeats in ~10 s of wall time while claiming a 7-minute real-time interval. |
| (script 2) | Image-text task-point bypass via DOM mutation | Forced the "我已看完" button to bypass its `disabled` state by mutating Vue component state; no server-side acknowledgment check. |
| (script 3) | Discussion auto-comment | Set `textarea.value`, dispatched a synthetic `input` event, and pressed Enter. Did not verify that the comment was actually persisted. |
| (script 4) | Homework auto-answer via `opencli` | Used `eval()` on `subprocess.run` stdout. Mapped arbitrary LLM outputs to radio clicks without question-by-question verification. |
| (script 5) | Course information extraction from a real platform's page | Used `page.cookies` (an attribute) where `page.context.cookies()` (a method) was required; produced `user_id=None, cc=None` on every call. |
| (script 6) | Chrome CDP attach with persistent login state | Spawned Chrome with `--user-data-dir` pointing at the user's real session. |
| (script 7) | Orchestrator that ran the above in sequence | Dead on arrival because of defect (5). |

## Defects found in the upstream material

The full list with code-line citations is in
`docs/audit-2026-06.md`. The short version:

* **P0-1**: Wrong API call — the orchestrator never executed because
  `page.cookies` is an attribute, not a method.
* **P0-2**: `article_id` and `discussion_id` were unused parameters in
  the batch loops; the "batch" was the same single-page operation
  counted N times.
* **P1-1**: Heartbeat loop reused one video's duration for every
  `v=` value, so `tp` was almost always wrong.
* **P1-2**: HTTP 200 was treated as business success with no
  independent `progress_updated` check.
* **P1-3**: The fixed `count=80` formula
  (`cp = duration * i / 79`, `ts += 5000`) produced a cp/ts slope
  that depends on `duration`. For long videos (1800 s) the implied
  rate became 4.56× — contradicting the "sp=1 disguise" claim.
* **P1-4**: Real wall-clock sleep was `0.05–0.15 s` while the README
  claimed "5 s interval". The forged `ts` field is the only thing
  the server saw; the wall-clock was a fiction.

## Claims that were unsupported

These were the strong-form claims made by the upstream README. They
are not made by the current repository.

| Claim | Status | Why it fails |
|-------|--------|--------------|
| "100% 成功" | FALSE | Developer's own log records ~80% on 0%-progress videos; 4 videos stuck at 71–87%. |
| "通用 / 全平台" | UNPROVEN | Single tenant, single course, single browser snapshot. |
| "稳定 / 不触发检测" | UNPROVEN | No longitudinal measurement, no detection-signal definition. |
| "绕过后端反作弊" | UNPROVEN | No measurement of what the server enforces; an interpretation of one observation. |
| "一键刷课" | REMOVED | The "one-click" entrypoint was the most concentrated source of risk. |

## Why the operational scripts are gone

Even with `[REDACTED-*]` tokens substituted for real identifiers,
the original `.py` files were *operational implementations*. A
reader could substitute their own account, course, and fingerprint
into the unmodified code and run it. That is what "operational
implementation" means. Archived-directory placement is a convention
for *historical* material; it is not a security boundary.

The current repository therefore does not include any code that
could be re-run against the real platform. The architectural
separation between the harness in `src/telemetry_research/` and any
historical reference is:

* The harness has no entrypoint that talks to any real platform.
* The historical reference is this single document.
* Real identifiers are redacted in *both* places.

## Verifying the boundary

A reader can verify the operational scripts are gone:

```bash
ls archived/legacy-research-notes/
# README.md
# SUMMARY.md   (this file, plus the README)
```

That is the entire contents of the archived directory.

## Restoration for forensic purposes

If a future auditor needs the original implementation text for a
legitimate forensic purpose (e.g. comparing what the server now
enforces against what the client assumed), the original `git`
history of the upstream repository is the correct source. This
repository does not contain it.

## Provenance

The audited upstream HEAD was `[REDACTED-COMMIT]`. The commit
history and full file contents of that HEAD remain at the upstream
repository; this refactor is published as a separate branch and
PR. The audit document (`docs/audit-2026-06.md`) cites the
specific lines of the upstream material that the defects were
found on, for reproducibility.