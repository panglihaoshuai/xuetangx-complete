"""Pytest configuration: ensure src/ and the repo root are importable.

The repo uses a flat layout where ``src/telemetry_research`` and
``mock_lms`` are top-level packages, with tests under ``tests/``.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

# Prepend so tests can ``import telemetry_research`` and ``import mock_lms``.
for path in (str(SRC), str(ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)