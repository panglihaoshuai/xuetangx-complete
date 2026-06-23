name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[test,dev]"
      - name: Run tests
        run: |
          python -m pytest -q
      - name: Lint (ruff)
        run: |
          ruff check src mock_lms tests scripts
      - name: Boundary grep
        run: |
          set -e
          ! grep -R "xuetangx.com" src mock_lms tests scripts
          ! grep -R "video-log" src mock_lms tests scripts
          echo "boundary checks ok"
      - name: Claim consistency
        run: |
          python -m pytest tests/test_claim_consistency.py -q
      - name: Audit doc mentions prior claims
        run: |
          grep -q "MISLEADING_IMPLEMENTATION" docs/audit-2026-06.md