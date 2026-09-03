"""Deterministic static-demo verification gate."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from scripts.verify_demo import DemoVerificationError, verify_demo

ROOT = Path(__file__).resolve().parents[2]


def test_demo_verifier_accepts_exact_generated_static_monitor() -> None:
    summary = verify_demo(
        ROOT / "demo",
        benchmark_root=ROOT / "benchmark" / "robot_cell_v1",
        repository_root=ROOT,
    )

    assert summary.total_cases == 36
    assert summary.exact_matches == 36
    assert summary.network_accessed is False
    assert summary.control_surfaces == 0


def test_demo_verifier_rejects_static_asset_drift(tmp_path: Path) -> None:
    demo = tmp_path / "demo"
    shutil.copytree(ROOT / "demo", demo)
    with (demo / "assets" / "app.js").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write("// drift\n")

    with pytest.raises(DemoVerificationError, match=r"app\.js") as captured:
        verify_demo(
            demo,
            benchmark_root=ROOT / "benchmark" / "robot_cell_v1",
            repository_root=ROOT,
        )

    assert captured.value.code == "asset_drift"


def test_repository_verification_gate_checks_demo(capsys: pytest.CaptureFixture[str]) -> None:
    import scripts.verify as repository_verifier

    repository_verifier.check_demo()

    assert (
        "demo: 36 scenarios; exact generated assets; no network/control surfaces"
        in capsys.readouterr().out
    )
