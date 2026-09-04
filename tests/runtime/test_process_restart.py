"""Cross-process restart and latch-recovery replay verification tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_restart_recovery_sequence_crosses_a_fresh_process_at_every_transition() -> None:
    root = Path(__file__).resolve().parents[2]
    completed = subprocess.run(
        [sys.executable, "scripts/verify_process_restart.py"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["verification"] == "process_restart_latch_recovery_v1"
    assert report["process_count"] == 7
    assert [phase["state"] for phase in report["phases"]] == [
        "intervention_latched",
        "stopped_unverified",
        "reset_ready",
        "rearm_pending",
        "recovery_pending",
        "recovery_pending",
        "initializing",
    ]
    assert all(phase["latched"] for phase in report["phases"][:-1])
    assert report["phases"][-1]["latched"] is False
    assert report["phases"][-1]["fresh_start_required"] is False
    assert report["phases"][-1]["active_request_sha256"] is None
    assert report["physical_stop"] == "not_established"
    assert report["operational_authority"] == "none"


def test_restart_during_output_uncertainty_preserves_request_and_denies_recovery() -> None:
    root = Path(__file__).resolve().parents[2]
    completed = subprocess.run(
        [sys.executable, "scripts/verify_process_restart.py"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["output_uncertainty_process_count"] == 6
    assert {case["case"] for case in report["output_uncertainty_cases"]} == {
        "request-pending",
        "output-unresolved",
        "request-timeout",
    }
    for case in report["output_uncertainty_cases"]:
        assert case["restart_integrity_state"] == "verified"
        assert case["state"] == "intervention_latched"
        assert case["latched"] is True
        assert case["active_request_sha256"] is not None
        assert case["reset_probe_state"] == "reset_not_permitted"
        assert case["reset_probe_latched"] is True
        assert case["acknowledgment_inferred"] is False
        assert case["physical_stop"] == "not_established"
    assert {case["output_state"] for case in report["output_uncertainty_cases"]} == {
        "request_pending",
        "unresolved",
    }
    timed_out = next(
        case for case in report["output_uncertainty_cases"] if case["case"] == "request-timeout"
    )
    assert "output_timeout" in timed_out["reason_codes"]


def test_restart_from_invalid_or_interrupted_recovery_state_cannot_bypass_sequence() -> None:
    root = Path(__file__).resolve().parents[2]
    completed = subprocess.run(
        [sys.executable, "scripts/verify_process_restart.py"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["invalid_recovery_process_count"] == 8
    cases = {case["case"]: case for case in report["invalid_recovery_cases"]}
    assert set(cases) == {
        "reset-not-permitted",
        "rearm-pending",
        "recovery-pending",
        "recovery-confirmed",
    }
    assert cases["reset-not-permitted"]["pre_restart_state"] == "reset_not_permitted"
    assert cases["rearm-pending"]["pre_restart_state"] == "rearm_pending"
    assert cases["recovery-pending"]["pre_restart_state"] == "recovery_pending"
    assert cases["recovery-confirmed"]["fresh_start_required"] is True
    assert all(case["post_probe_state"] == "reset_not_permitted" for case in cases.values())
    assert all(case["latched"] is True for case in cases.values())
    assert all(case["active_request_preserved"] is True for case in cases.values())


def test_canonical_verifier_runs_the_process_restart_gate() -> None:
    root = Path(__file__).resolve().parents[2]
    verifier = (root / "scripts" / "verify.py").read_text(encoding="utf-8")

    assert '"scripts/verify_process_restart.py"' in verifier


def test_restart_preserves_consumed_command_attribution_history() -> None:
    root = Path(__file__).resolve().parents[2]
    completed = subprocess.run(
        [sys.executable, "scripts/verify_process_restart.py"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    history = report["attribution_history"]
    assert report["attribution_history_process_count"] == 2
    assert history["restart_integrity_state"] == "verified"
    assert history["latched"] is True
    assert history["history_count"] == 1
    assert history["history_command_id"] == "command-id:restart-history"
    assert history["consumed"] == ["command-id:restart-history:sequence:0"]
    assert history["physical_stop"] == "not_established"


def test_restart_adversarial_processes_fail_closed_without_clearing_the_latch() -> None:
    root = Path(__file__).resolve().parents[2]
    completed = subprocess.run(
        [sys.executable, "scripts/verify_process_restart.py"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["adversarial_process_count"] == 7
    assert {case["case"]: case["reason_code"] for case in report["adversarial_cases"]} == {
        "missing": "missing_state",
        "corrupt": "hash_mismatch",
        "nonlatched-bypass": "restart_state_not_latched",
        "identity-bypass": "restart_identity_mismatch",
        "partial-publication": "missing_state",
        "stale-checkpoint": "restart_state_id_mismatch",
        "conflicting-checkpoint": "restart_state_id_mismatch",
    }
    assert all(case["integrity_state"] == "failed_closed" for case in report["adversarial_cases"])
    assert all(case["latched"] is True for case in report["adversarial_cases"])
