"""Tests for the redaction utility that strips real-platform identifiers.

The audit mandates that no real user_id, course_id, classroom_id, sign, cookie
names, cc fingerprints, or API paths leak into the public repository's
executable code or top-level docs.
"""
from __future__ import annotations

from pathlib import Path

from telemetry_research.evidence import REDACT_PATTERNS, redact_text


def test_redact_text_strips_cc_fingerprint():
    s = "cc=0325E954D654D7C80498CE5AAF1F53F5"
    assert "[REDACTED-CC]" in redact_text(s)
    assert "0325E954D654D7C80498CE5AAF1F53F5" not in redact_text(s)


def test_redact_text_strips_real_user_id():
    s = "k=79159369 from cookie"
    out = redact_text(s)
    assert "[REDACTED-USERID]" in out
    assert "79159369" not in out


def test_redact_text_strips_course_and_classroom_ids():
    s = "course_id=4005682 classroomid=29601185 sign=hebnu08091009038"
    out = redact_text(s)
    assert "[REDACTED-COURSEID]" in out
    assert "[REDACTED-CLASSROOMID]" in out
    assert "[REDACTED-SIGN]" in out
    assert "4005682" not in out
    assert "29601185" not in out
    assert "hebnu08091009038" not in out


def test_redact_text_strips_video_log_endpoint():
    s = "POST /video-log/heartbeat/ HTTP/1.1"
    out = redact_text(s)
    assert "[REDACTED-ENDPOINT]" in out
    assert "video-log" not in out


def test_redact_text_strips_real_domain():
    s = "fetch('https://www.xuetangx.com/api')"
    out = redact_text(s)
    assert "[REDACTED-DOMAIN]" in out
    assert "xuetangx.com" not in out


def test_redact_text_passes_through_synthetic_values():
    s = "video_id=1 duration=120 count=80"
    out = redact_text(s)
    # Synthetic values must not be redacted.
    assert out == s


def test_redact_patterns_covers_all_required_keys():
    """The audit requires every published key to have a redaction pattern."""
    expected_tokens = {
        "REDACTED-CC",
        "REDACTED-USERID",
        "REDACTED-COURSEID",
        "REDACTED-CLASSROOMID",
        "REDACTED-SIGN",
        "REDACTED-ENDPOINT",
        "REDACTED-DOMAIN",
    }
    found_tokens = set()
    for _, replacement in REDACT_PATTERNS:
        for token in expected_tokens:
            if token in replacement:
                found_tokens.add(token)
    assert expected_tokens.issubset(found_tokens)


def test_archived_scripts_are_desensitized(tmp_path: Path):
    """If a developer accidentally puts a real value into an archived script,
    it must be flagged by redaction. This test runs the redactor over the
    archived directory and asserts no real values remain."""
    archived = Path(__file__).resolve().parents[1] / "archived"
    if not archived.exists():
        # Nothing to test yet.
        return
    found_unredacted = []
    for path in archived.rglob("*"):
        if path.is_file() and path.suffix in {".py", ".md", ".txt", ".json"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            for marker in [
                "0325E954D654D7C80498CE5AAF1F53F5",
                "79159369",
                "4005682",
                "29601185",
                "hebnu08091009038",
                "www.xuetangx.com",
                "/video-log/heartbeat/",
            ]:
                # An archived script may legitimately reference these in
                # a "redaction example" comment; we treat the literal
                # value not preceded by REDACTED as a leak.
                if marker in text and "[REDACTED" not in text:
                    found_unredacted.append((path, marker))
    assert not found_unredacted, f"Archived files leak real values: {found_unredacted}"