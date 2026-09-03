"""Offline benchmark CLI tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from oscillink_safety_ops.cli import run
from scripts.generate_benchmark import generate_benchmark

SOURCE_COMMIT = "6f633895bd8d6f636f7353be34d2a307fbc2aee3"


def test_benchmark_verify_cli_emits_machine_readable_verified_totals(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repository = Path(__file__).resolve().parents[2]
    benchmark = tmp_path / "robot_cell_v1"
    generate_benchmark(
        benchmark, source_repository=repository, runtime_baseline_commit=SOURCE_COMMIT
    )
    monkeypatch.chdir(repository)

    exit_code = run(["benchmark", "verify", "--root", str(benchmark)])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == {
        "exact_matches": 36,
        "fault_families": 12,
        "network_accessed": False,
        "repeat_runs": 3,
        "total_cases": 36,
    }
