> **ARCHIVED — NOT EXECUTABLE.** This document is preserved for
> historical reference only. It is a high-level summary, not a
> guide. Real-platform identifiers have been replaced with
> `[REDACTED-*]` tokens.

# Archived Legacy Research Notes

This directory is preserved for **historical reference only**.

## Contents

After the public safety review, this directory contains exactly two
files:

* `README.md` — this file.
* `SUMMARY.md` — a high-level defect catalog with no runnable code.

That's it.

## What used to be here

The original `archived/` directory held seven executable Python
scripts plus four Markdown documents copied from the upstream
repository. The scripts were:

* Heartbeat injection against a real platform.
* Image-text task-point bypass via DOM mutation.
* Discussion auto-comment.
* Homework auto-answer via a third-party browser tool.
* Course information extraction from a real platform's page.
* Chrome CDP attach with persistent login state.
* Orchestrator that ran the above in sequence.

The Markdown documents were:

* The original README with installation and quick-start.
* The original `SKILL.md`.
* Two detailed session-finding documents with experimental
  procedures and concrete example payloads.
* A technical reference with API endpoint and field details.
* A homework / `opencli` command reference.

## Why they were removed

Even with `[REDACTED-*]` tokens substituted for real identifiers,
those files were **operational implementations**. A reader could
substitute their own account, course, and fingerprint into the
unmodified code and run it. That is the operational definition of
"operational implementation". Archived-directory placement is a
convention for *historical* material; it is not a security
boundary.

This was the central finding of the public safety review. The
audit document (`docs/audit-2026-06.md`) and the final report
(`docs/final-report-2026-06.md`) both predate this finding and may
quote specific lines from the originals for reproducibility. The
operational *code* is no longer in this repository.

## What is here instead

`SUMMARY.md` is a defect catalog. It describes what each deleted
script was for, what was wrong with it, and why the strong-form
claims in the original README ("100% 成功", "通用", "稳定",
"不触发检测", "一键刷课", "绕过后端反作弊") are not supported by
the available evidence. It does not include the operational code.

## Verifying the boundary

```bash
$ ls archived/legacy-research-notes/
README.md
SUMMARY.md
```

Two files. No `.py`. No `.json`. No concrete example payloads. No
endpoint paths. No real-platform identifiers.

## What you should do if you came here looking for a tool

You are in the wrong place. The current repository is a research
harness for the protocol model only. It does not interact with any
real platform. The audit document explains why every original
capability was removed.

If you are looking for a way to automate course completion on a
real platform, no file in this repository will help you — and that
is by design.

## Restoration for forensic purposes

If a future auditor needs the original implementation text for a
legitimate forensic purpose, the original git history of the
upstream repository is the correct source. This repository does
not contain it.