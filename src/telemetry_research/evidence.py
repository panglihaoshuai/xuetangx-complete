"""Evidence tagging convention used throughout the harness.

The audit establishes a strict vocabulary:

* Verdict: CONFIRMED / PARTIALLY_CONFIRMED / UNPROVEN / FALSE.
* Level:   L0 guess .. L5 source-of-truth confirmation.
* Superlatives ("stable", "100%", "general") require L3 or higher.

This module is the single source of truth for that vocabulary.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


class EvidenceLevel(enum.IntEnum):
    """Strength of evidence. Higher is stronger."""

    L0 = 0  # guess
    L1 = 1  # single observation
    L2 = 2  # repeated observation
    L3 = 3  # automated reproducible
    L4 = 4  # cross-environment reproducible
    L5 = 5  # source-of-truth or vendor-confirmed


class Verdict(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    PARTIALLY_CONFIRMED = "PARTIALLY_CONFIRMED"
    UNPROVEN = "UNPROVEN"
    FALSE = "FALSE"


SUPERLATIVE_LEVEL_THRESHOLD = EvidenceLevel.L3


@dataclass(frozen=True)
class Evidence:
    claim: str
    level: EvidenceLevel = EvidenceLevel.L0
    verdict: Verdict = Verdict.UNPROVEN
    reproducer: str | None = None
    notes: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.verdict, Verdict):
            raise ValueError(
                f"verdict must be a Verdict enum, got {self.verdict!r}"
            )

    def supports_superlative(self) -> bool:
        """Whether this evidence is strong enough to back a superlative.

        Per the audit: words like "100%", "stable", "general" require
        L3 or higher evidence.
        """
        return (
            self.verdict in (Verdict.CONFIRMED, Verdict.PARTIALLY_CONFIRMED)
            and self.level >= SUPERLATIVE_LEVEL_THRESHOLD
        )


def tag(
    claim: str,
    level: EvidenceLevel = EvidenceLevel.L0,
    verdict: Verdict = Verdict.UNPROVEN,
    reproducer: str | None = None,
    notes: str = "",
) -> Evidence:
    return Evidence(
        claim=claim,
        level=level,
        verdict=verdict,
        reproducer=reproducer,
        notes=notes,
    )


# Redaction patterns for stripping real-platform identifiers from text.
# Each entry: (compiled regex, replacement token).
REDACT_PATTERNS: list[tuple] = [
    # cc fingerprint: 32-hex characters observed in the audit.
    (r"\b0[0-9A-F]{31}\b", "[REDACTED-CC]"),
    # user id 'k': JSON / Python / JS dict syntax with 7+ digit integer.
    (r"""(['"]k['"]\s*:\s*['"]?)\d{7,}""", r"\1[REDACTED-USERID]"),
    # user id bare: 'k=NNN' style.
    (r"\bk=(\d{7,})\b", "k=[REDACTED-USERID]"),
    # course_id dict syntax.
    (r"""(['"](?:c|course_id)['"]\s*:\s*['"]?)\d{7,}""", r"\1[REDACTED-COURSEID]"),
    # course_id bare.
    (r"\bcourse_id=(\d{7,})\b", "course_id=[REDACTED-COURSEID]"),
    # classroomid dict syntax.
    (r"""(['"]classroomid['"]\s*:\s*['"]?)\d{5,}""", r"\1[REDACTED-CLASSROOMID]"),
    (r"\bclassroomid=(\d{5,})\b", "classroomid=[REDACTED-CLASSROOMID]"),
    # sign dict syntax.
    (r"""(['"]sign['"]\s*:\s*['"]?)[a-z]{2,}[0-9]{6,}""", r"\1[REDACTED-SIGN]"),
    # sign bare.
    (r"\bsign=([a-z]{2,}[0-9]{6,})\b", "sign=[REDACTED-SIGN]"),
    # The specific tenant sign from the audit.
    (r"\bhebnu[0-9]{6,}\b", "[REDACTED-SIGN]"),
    # Endpoint: any '/video-log/...' path.
    (r"/video-log/[A-Za-z0-9_/\-]+", "[REDACTED-ENDPOINT]"),
    # Domain.
    (r"https?://[A-Za-z0-9.\-]*xuetangx\.com", "[REDACTED-DOMAIN]"),
    (r"\bxuetangx\.com\b", "[REDACTED-DOMAIN]"),
    # Comments referencing bare user_id example values like `// 79159369` or
    # `// 值：79159369` are still leaks. Catch 7+ digit integers when they
    # appear on a line by themselves (very common in code-comments) or after
    # `// 示例` style markers.
    (r"//[^\n]{0,30}\b\d{7,}\b", "// [REDACTED-USERID]"),
]


def redact_text(text: str) -> str:
    """Apply every redaction pattern in order. Returns redacted text."""
    import re

    out = text
    for pattern, replacement in REDACT_PATTERNS:
        out = re.sub(pattern, replacement, out)
    return out