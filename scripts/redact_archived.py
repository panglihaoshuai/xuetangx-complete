"""Quarantine helper for legacy research notes.

The original `archived/legacy-research-notes/` directory once held the
operational scripts as captured from upstream. After the public safety
review, those scripts were deleted because they were *operational
implementations*, not historical notes — preserving them under
`archived/` was not enough to make them safe to publish.

This script now only handles redaction of any `.md` documents that
*do* live in the archived directory (e.g. SUMMARY.md, README.md). It
applies the `[REDACTED-*]` tokens from
`src/telemetry_research/evidence.py` so that no real identifier
leaks into a published copy of this repository.

It is intentionally idempotent — running it twice has the same effect
as running it once.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from telemetry_research.evidence import redact_text  # noqa: E402

ARCHIVED = ROOT / "archived" / "legacy-research-notes"

# Files that legitimately live in the archived directory.
# After the public safety review, this is just SUMMARY.md and README.md.
QUARANTINED = [
    "SUMMARY.md",
    "README.md",
]

HEADER_PY = """\
# =============================================================================
# ARCHIVED LEGACY RESEARCH NOTES — NOT EXECUTABLE
# -----------------------------------------------------------------------------
# This file is preserved for historical reference only.
# =============================================================================

"""

HEADER_MD = """\
> **ARCHIVED — NOT EXECUTABLE.** This document is preserved for
> historical reference only. It is a high-level summary, not a
> guide. Real-platform identifiers have been replaced with
> `[REDACTED-*]` tokens.

"""

MARKER = "# ARCHIVED LEGACY RESEARCH NOTES — NOT EXECUTABLE"
MARKER_MD = "> **ARCHIVED — NOT EXECUTABLE.**"


def _has_header(text: str, marker: str) -> bool:
    return marker in text[:600]


def process_file(path: Path) -> None:
    original = path.read_text(encoding="utf-8")
    redacted = redact_text(original)

    if path.suffix == ".py":
        header = HEADER_PY
        marker = MARKER
    else:
        header = HEADER_MD
        marker = MARKER_MD

    if _has_header(redacted, marker):
        return

    new_text = header + redacted
    path.write_text(new_text, encoding="utf-8")
    print(f"  redacted + quarantined: {path.relative_to(ROOT)}")


def main() -> None:
    if not ARCHIVED.exists():
        print(f"!! {ARCHIVED} does not exist; nothing to do")
        return
    for name in QUARANTINED:
        path = ARCHIVED / name
        if not path.exists():
            print(f"  skipped (missing): {name}")
            continue
        process_file(path)


if __name__ == "__main__":
    main()