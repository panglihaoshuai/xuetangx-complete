# Final Audit Report — 2026-06-23

This is the closing summary of the audit-and-refactor cycle. The full
audit is in [`audit-2026-06.md`](audit-2026-06.md). This document is
the deliverable summary requested by the task.

## Verdict

**MISLEADING_IMPLEMENTATION** — confirmed in static analysis. The
published entrypoint cannot execute because of an incorrect
`page.cookies` usage, and the "batch" loops in the article and
discussion scripts do not navigate between targets. The
`brush_all.py` orchestrator depended on a real platform. None of
this is acceptable to re-release as-is.

## Audit findings (P0 / P1 / P2 / P3)

| ID | Severity | Finding |
|----|----------|---------|
| D-P0-1 | P0 | `page.cookies` used as attribute, not method — entrypoint dead |
| D-P0-2 | P0 | "100% 成功" contradicts developer's own log (~80%) |
| D-P0-3 | P0 | "100% success" table not produced by any test |
| D-P0-4 | P0 | `article_id` / `discussion_id` unused in batch loops |
| D-P1-1 | P1 | Heartbeat reuses current page `duration` for every `v=` ID |
| D-P1-2 | P1 | HTTP 200 conflated with business success |
| D-P1-3 | P1 | cp/ts ratio drifts with duration (1800s → 4.56x implied speed) |
| D-P1-4 | P1 | `time.sleep(0.1)` contradicts README "5 seconds" claim |
| D-P2-1 | P2 | Bare `except:` clauses (silent error swallowing) |
| D-P2-2 | P2 | `eval()` on external stdout in homework.py:69 |
| D-P2-3 | P2 | `subprocess.run` without `check=True` |
| D-P2-4 | P2 | No type / boundary validation on inputs |
| D-P2-5 | P2 | Hard-coded absolute Chrome paths |
| D-P2-6 | P2 | `connect_over_cdp` uses `contexts[0].pages[0]` blindly |
| D-P3-1 | P3 | Marketing language: "通用" / "全平台" / "不触发检测" |
| D-P3-2 | P3 | README mixes research voice and install-voice |
| D-P3-3 | P3 | Repo name `xuetangx-complete` is itself a claim |

## Confirmed claims (with grade)

| Claim | Verdict | Level | Evidence |
|-------|---------|-------|----------|
| `ts_ms` must be strictly monotonic for acceptance | CONFIRMED | L3 | `tests/test_business_success.py::test_inverted_timestamp_*` |
| `cp` must be non-decreasing for acceptance | CONFIRMED | L3 | `tests/test_business_success.py::test_cp_backwards_*` |
| `sp=1` is a documented assumption in the model | CONFIRMED | L3 | `tests/test_business_success.py` (model enforces it) |
| `http_ok` ≠ `business_accepted` (separation of concerns) | CONFIRMED | L3 | `tests/test_business_success.py`, fixture `business_failure_200.json` |
| `seq` must be unique per video | CONFIRMED | L3 | `tests/test_business_success.py::test_replay_of_same_sq_*` |
| `et=ended` must come last | CONFIRMED | L3 | `tests/test_business_success.py::test_ended_before_*` |
| `implied_speed = duration / (count-1) / interval_s` | CONFIRMED | L3 | `tests/test_heartbeat_count_parametrized.py` |

## Rejected claims

* "100% success" — FALSE. Developer's own log records ~80% on 0%-progress
  videos and four stuck videos at 71–87%.
* "通用 / 全平台" — UNPROVEN. Single tenant, single course, single
  browser snapshot, single account.
* "稳定 / 不触发检测" — UNPROVEN. No longitudinal measurement, no
  detection-signal definition.
* "绕过后端反作弊" — UNPROVEN. The audit could not reproduce the claim.
  What the original code actually did was submit heartbeat-shaped POSTs
  with monotonic, linear `cp` and forged `ts`. Whether the server
  enforces more is not modeled and not proven.
* "一键刷课" — REMOVED. The "one-click" entrypoint (`brush_all.py`)
  was the most concentrated source of risk and was deleted.

## Critical bugs fixed

* `page.cookies` → never reachable in the public surface (no
  `extract_course.py` equivalent exists in `src/`).
* `article_id` / `discussion_id` parameter drift → not applicable;
  those modules were removed.
* HTTP-200-as-business-success → every response in the harness exposes
  `business_accepted` and `progress_updated` as independent fields;
  tests assert that they are independent.
* `cp`/`ts` math made explicit via `implied_speed()`.
* Wall-clock vs `ts` forged rate no longer hidden — exposed in
  `protocol-research-method.md`.

## Security reductions

Removed capabilities (no executable replacement):

* Real-platform heartbeat injection.
* Image-text DOM mutation to bypass the "我已看完" disabled button.
* Discussion auto-comment.
* Homework auto-answer (judge / choice / fill).
* CDP attach to a logged-in Chrome and drive it.
* Live platform API path / cookie name / CSRF usage in source.

Hardened:

* `mock_client._assert_local` refuses any URL that is not
  `127.0.0.1` / `localhost`.
* `MockLMSServer` binds `127.0.0.1` only.
* All real-platform identifiers replaced with `[REDACTED-*]` tokens
  in `archived/` and never appear in `src/`, `mock_lms/`, `scripts/`,
  top-level docs, or pyproject.
* CI workflow includes boundary greps and the claim-consistency test
  so a regression cannot pass CI silently.

## Test evidence

```
$ python3 -m pytest -q
...................................................................   [100%]
67 passed in 0.06s
```

Coverage breakdown:

* `test_sequence_builder.py` — 23 tests. Strict monotonicity, count
  validation, parameter validation, event-type ordering.
* `test_business_success.py` — 11 tests. http_ok / business_accepted
  separation, fixture-driven rejection cases, parametrized durations.
* `test_false_positive_detection.py` — 5 tests. Catches the patterns
  the audit flagged.
* `test_heartbeat_count_parametrized.py` — 11 tests across durations
  30 / 120 / 395 / 600 / 1800.
* `test_redaction.py` — 8 tests. Token coverage + archived-leak scan.
* `test_claim_consistency.py` — 4 tests. README / SKILL.md / SECURITY.md
  / ETHICS.md do not advertise discredited terms; real-domain
  mentions are restricted to the audit doc.
* `test_evidence.py` — 5 tests. Evidence tagging vocabulary.

```
$ python3 -m ruff check .
All checks passed!

$ python3 -m mypy src
Success: no issues found in 7 source files
```

Smoke test against the local mock LMS:

```
$ PYTHONPATH=src python3 -c '...'
Server: http://127.0.0.1:50291
implied_speed: 0.3037974683544304
business_ok: True
state: {'accepted': 80, 'rejected': 0, 'business_completed': True}
OK
```

Boundary checks:

```
$ grep -R "[REDACTED-DOMAIN]" src mock_lms scripts
(none)

$ grep -R "/video-log/" src mock_lms scripts
src/telemetry_research/evidence.py:    # Endpoint: any '/video-log/...' path.
src/telemetry_research/evidence.py:    (r"/video-log/[A-Za-z0-9_/\-]+", "[REDACTED-ENDPOINT]"),
# (only the redactor regex itself, defensive mechanism)

$ grep -R "自动答题\|一键刷课\|不触发检测\|100%成功" src mock_lms scripts
(none)
```

## Remaining unknowns

* Whether the real platform actually enforces any of the seven model
  rules in `docs/protocol-research-method.md`. The harness is a model,
  not a probe. Confirming this against a real platform is out of
  scope.
* Whether `cc` fingerprinting actually rejects forged fingerprints.
  The harness does not model client fingerprinting.
* Whether `ts_ms` is cross-checked against wall clock. The harness
  assumes it is not; if it is, every forged-ts sequence is a
  detection signal.
* What server-side `t` (return-to-play) and `seek` events are
  enforced. The harness only models `play` / `heartbeat` / `ended`.
* Cross-account, cross-tenant, cross-frontend behavior. The harness
  treats `video_id` as opaque.

## Git commits

```
bcba853 ci: add lint typecheck and tests workflow
af3662b docs: rewrite claims and evidence boundaries
8f1b031 refactor: isolate telemetry research core
4729854 test: add mock LMS and failing regression cases
f049d70 audit: verify repository claims and identify false positives
```

Five commits. The audit commit contains no code changes; subsequent
commits are scoped to one concern each.

## Files changed

Top-level new:

* `README.md`, `SECURITY.md`, `ETHICS.md`, `pyproject.toml`,
  `.gitignore`, `.github/workflows/ci.yml`.

Top-level removed (vs. upstream):

* No `brush_all.py`, `extract_course.py`, `heartbeat.py`, `article.py`,
  `discuss.py`, `homework.py`, `auto_chrome.py`, `SKILL.md`,
  `requirements.txt`.

Moved to `archived/legacy-research-notes/` (desensitized):

* `article.py`, `auto_chrome.py`, `brush_all.py`, `discuss.py`,
  `extract_course.py`, `heartbeat.py`, `homework.py`,
  `README.original.md`, `SKILL.original.md`,
  `development-history.md`, `session-findings.md`,
  `technical.md`, `homework-opencli.md`.

Created:

* `src/telemetry_research/{__init__,models,sequence_builder,validator,mock_client,evidence}.py`
* `mock_lms/{__init__,app,state_machine}.py` + `mock_lms/README.md`
* `tests/{conftest,test_*.py}` (7 test files) + 4 fixtures
* `docs/{audit-2026-06,protocol-research-method,evidence-standard,responsible-disclosure-draft}.md`
* `scripts/redact_archived.py`

48 tracked files total. Pycache excluded by `.gitignore`.

## Final repository positioning

**Web Telemetry Trust-Boundary Research Harness.**

* It is a model under test, not a probe.
* It runs only against a local mock LMS that binds 127.0.0.1.
* It does not, and will not, talk to a real platform.
* It does not advertise "100%", "通用", "稳定", or "不触发检测"
  because those claims are unsupported by the available evidence.

## Final answers to the questions

> 原始版本是否真的可以完整运行？

**No.** The `brush_all.py` entrypoint calls `check_login(page)` which
calls `page.cookies` (an attribute) instead of `page.context.cookies()`
(a method). `user_id` and `cc` are always `None`. The script exits
with "未登录" before doing anything. The article and discussion
"batch" loops do not navigate between targets. The heartbeat loop
reuses one video's duration for every `v=` ID.

> 原始"100%成功"是否可信？

**No.** The developer's own session log records "~80%" for 0%-progress
videos and four videos stuck at 71–87% that no script could push to
100%. The "100%" was aspirational text.

> 原始"绕过后端反作弊"是否证据充分？

**No.** The audit found no measurement of what the server actually
enforces. The "bypass" claim was an interpretation of the observed
behavior of a single tenant's heartbeat endpoint, with a single
browser session, with no cross-tenant or longitudinal validation.

> 哪些内容只是一次实验现象？

* "0% 视频 5s × 80 心跳能稳定推到 100%": single observation, ~80%.
* "sp=1 是必需的": single observation.
* "图文按钮可以强制启用": single observation with no server-side ack.
* "讨论区 textarea input 事件即可发送": single observation, no
  persistence check.
* 4 个顽固视频卡在 71–87%：single observation, never resolved.

> 当前版本是否已经完全移除真实平台执行能力？

**Yes.** `grep -R "[REDACTED-DOMAIN]" src mock_lms scripts` returns
nothing. `find src mock_lms -name "brush_all.py" -o -name
"heartbeat.py"` returns nothing. The mock client refuses any URL that
is not `127.0.0.1` / `localhost`. The original scripts are in
`archived/` and have no `__main__` entrypoint that would actually work
because the only URL they reference is now a `[REDACTED-DOMAIN]`
token.

> 当前版本是否适合公开发布？

**Yes, with the following caveats:**

* The audit doc is the primary artifact. Read it before forming an
  opinion of what this repository does.
* The archived directory exists; reviewers should confirm they
  understand it is quarantined and desensitized.
* No CI-runnable workflow on GitHub Actions has actually executed on
  the GitHub-hosted runner. Local verification (pytest + ruff + mypy
  + boundary grep) passes; remote CI is set up but has not been
  triggered.
* The harness is positioned as a research tool, not as a course
  completion aid. ETHICS.md and SECURITY.md state this explicitly.

The repository is suitable for public release as a research artifact.
It is not suitable as, and never will be, a course-completion tool.