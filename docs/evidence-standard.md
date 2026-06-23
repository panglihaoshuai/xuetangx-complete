# Evidence Standard

This document is the evidence vocabulary the repository uses. It is
the answer to the audit's complaint that the original README
advertised strong-form claims ("100%", "通用", "稳定", "不触发检测")
without the evidence to back them.

## Verdict vocabulary

Every claim in this repository is tagged with one of:

| Verdict               | Meaning                                                     |
|-----------------------|-------------------------------------------------------------|
| CONFIRMED             | Reproduced in tests, deterministic, isolated.              |
| PARTIALLY_CONFIRMED   | Reproduced in some configurations but not all.              |
| UNPROVEN              | Hypothesized but not reproduced.                           |
| FALSE                 | Claimed but contradicted by data or reasoning.              |

## Evidence levels

| Level | Meaning                                                                |
|-------|------------------------------------------------------------------------|
| L0    | Guess.                                                                |
| L1    | Single observation.                                                   |
| L2    | Repeated observation, possibly in different orders.                   |
| L3    | Automated, reproducible, in this repo's test suite.                   |
| L4    | Cross-environment reproducible.                                       |
| L5    | Vendor-confirmed or source-of-truth verified.                         |

## What level you need for what kind of claim

| Claim type                  | Minimum level | Verdict required          |
|-----------------------------|---------------|---------------------------|
| "this property holds"       | L3            | CONFIRMED                 |
| "this property usually holds" | L2         | PARTIALLY_CONFIRMED       |
| "this property is universal" | L4          | CONFIRMED                 |
| "the real server does X"    | L5            | CONFIRMED (or UNPROVEN)   |
| "100% success" / "stable"   | L3 + L4       | CONFIRMED                 |
| "general / works everywhere" | L4 + L5     | CONFIRMED                 |

Anything weaker than the table requires the claim to be downgraded
or removed.

## What you must do when adding a claim

1. Write the claim as a single sentence.
2. Add it to `docs/claims.md` (or the relevant doc) with:
   * the verdict,
   * the level,
   * the reproducer (test name or external link),
   * the date.
3. If the claim is below L3, prefix the sentence with one of:
   `Observed:`, `Hypothesis:`, `Reported:`, `Anecdote:`.
4. If the claim is below the table threshold for the words used
   ("stable", "100%", etc.), rephrase.

## What you must NOT do

* Use the words "stable", "100%", "general", "works on any", "no
  detection risk", "fully bypasses" without L3 evidence.
* Conflate HTTP 200 with business success (see `protocol-research-method.md`).
* Cite a single observation as if it were a property.

## Reusing this standard elsewhere

If you find this standard useful for another audit, copy it. If you
find the standard missing a level or verdict you need, propose an
addition in a PR; do not silently relax the rules.