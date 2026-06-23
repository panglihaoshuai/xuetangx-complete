"""Tests for the evidence tagging convention.

L0..L5 + CONFIRMED/PARTIALLY_CONFIRMED/UNPROVEN/FALSE.
"""
from __future__ import annotations

import pytest

from telemetry_research.evidence import (
    Evidence,
    EvidenceLevel,
    Verdict,
    tag,
)


def test_evidence_default_level_is_L0():
    e = Evidence(claim="heartbeat injects completion")
    assert e.level == EvidenceLevel.L0
    assert e.verdict == Verdict.UNPROVEN


def test_evidence_can_be_tagged_confirmed_l5():
    e = tag(
        claim="ts must be strictly monotonic",
        level=EvidenceLevel.L5,
        verdict=Verdict.CONFIRMED,
        reproducer="state_machine_test",
    )
    assert e.level == EvidenceLevel.L5
    assert e.verdict == Verdict.CONFIRMED


def test_evidence_level_ordering():
    """L0 < L1 < L2 < L3 < L4 < L5 in terms of strength."""
    levels = [
        EvidenceLevel.L0,
        EvidenceLevel.L1,
        EvidenceLevel.L2,
        EvidenceLevel.L3,
        EvidenceLevel.L4,
        EvidenceLevel.L5,
    ]
    for a, b in zip(levels, levels[1:]):
        assert a < b


def test_superlative_adjective_requires_l3_or_higher():
    """The audit establishes: words like 'stable', '100%', 'general' require
    at least L3 evidence. We encode that rule."""
    e = tag(
        claim="100% success",
        level=EvidenceLevel.L1,
        verdict=Verdict.PARTIALLY_CONFIRMED,
    )
    assert not e.supports_superlative()
    e_l3 = tag(
        claim="100% success in 50 trials across 3 tenants",
        level=EvidenceLevel.L3,
        verdict=Verdict.CONFIRMED,
    )
    assert e_l3.supports_superlative()


def test_verdict_must_be_known():
    with pytest.raises(ValueError):
        Evidence(
            claim="x",
            verdict="DEFINITELY",  # type: ignore[arg-type]
        )