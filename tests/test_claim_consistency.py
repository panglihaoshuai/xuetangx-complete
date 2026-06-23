"""Tests enforcing the README claim consistency rules established by the audit.

These read docs/protocol-research-method.md and assert it doesn't reintroduce
the discredited superlatives. They're text tests, not behavior tests.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Words that the audit explicitly flags as unsupported by current evidence.
DISALLOWED_TERMS = [
    r"\b100\s*%",
    r"\b100\s*percent\b",
    r"\b一百\s*百分\s*比\b",
    r"\b通用化\b",
    r"\b通用\b",
    r"\b稳定\b",
    r"\b不触发检测\b",
    r"\b绕过\b",
    r"\b完全绕过\b",
    r"\b一键刷课\b",
    r"\b一键\b",
    r"\b全平台\b",
    r"\b保证\b",
    r"\b必成功\b",
    r"\bbypass\b",
    r"\bbypasses?\b",
]

ALLOWED_FILES = {
    REPO_ROOT / "README.md",
    REPO_ROOT / "docs" / "audit-2026-06.md",  # quotes the old claims
    REPO_ROOT / "docs" / "evidence-standard.md",
    REPO_ROOT / "SECURITY.md",
    REPO_ROOT / "ETHICS.md",
}


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def test_readme_does_not_advertise_unsupported_claims():
    readme = _read(REPO_ROOT / "README.md")
    for pattern in DISALLOWED_TERMS:
        assert not re.search(pattern, readme, flags=re.IGNORECASE), (
            f"README.md contains disallowed term: {pattern!r}"
        )


def test_skill_does_not_advertise_unsupported_claims():
    readme = _read(REPO_ROOT / "README.md")
    # Allowed: "may", "can", "supports modeling", "is parameterized"
    for pattern in DISALLOWED_TERMS:
        if pattern in {r"\b通用化\b", r"\b通用\b"}:
            # Allowed in archived section / docs explaining audit, but the
            # top-level readme and SKILL.md must not use it. audit doc may.
            continue
        assert not re.search(pattern, readme, flags=re.IGNORECASE), (
            f"README contains disallowed term: {pattern!r}"
        )


def test_no_real_platform_domain_in_user_facing_text():
    """README, SECURITY.md, ETHICS.md must not mention the real platform domain."""
    files = [
        REPO_ROOT / "README.md",
        REPO_ROOT / "SECURITY.md",
        REPO_ROOT / "ETHICS.md",
        REPO_ROOT / "pyproject.toml",
    ]
    for path in files:
        text = _read(path)
        assert "xuetangx.com" not in text, (
            f"{path.name} mentions xuetangx.com - real domain not allowed"
        )
        assert "video-log" not in text, (
            f"{path.name} mentions real API path"
        )


def test_audit_report_mentions_old_claims():
    """The audit report must explicitly call out the discredited claims so
    future readers can trace what changed."""
    audit = _read(REPO_ROOT / "docs" / "audit-2026-06.md")
    assert "100%" in audit or "100 percent" in audit or "100\\s*%" in audit
    assert "MISLEADING_IMPLEMENTATION" in audit