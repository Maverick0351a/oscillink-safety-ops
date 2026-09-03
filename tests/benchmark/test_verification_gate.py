"""Canonical verification-gate coverage for the frozen benchmark."""

from __future__ import annotations

import pytest

import scripts.verify as repository_verifier


def test_repository_verification_gate_checks_frozen_benchmark(
    capsys: pytest.CaptureFixture[str],
) -> None:
    repository_verifier.check_benchmark()

    captured = capsys.readouterr()
    assert "benchmark: 36/36 exact; 12 fault families; 3 repeat runs" in captured.out
