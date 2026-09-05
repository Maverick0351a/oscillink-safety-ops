"""Deterministic shared-dependency and common-cause tests."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from oscillink_safety_ops.runtime.common_cause import evaluate_common_cause
from oscillink_safety_ops.runtime.contracts import (
    DependencyBinding,
    SharedDependencyObservation,
    SourceHealthObservation,
    SupervisorConfiguration,
)

NOW = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)
CONFIG = "sha256:" + "a" * 64
SHA_B = "sha256:" + "b" * 64
SHA_C = "sha256:" + "c" * 64
KINDS = (
    "power",
    "network",
    "sensor",
    "clock",
    "compute",
    "software_update",
    "credentials",
    "enclosure_environment",
    "communications",
    "final_element",
)


def binding(kind: str = "power") -> DependencyBinding:
    return DependencyBinding.model_validate(
        {
            "dependency_id": f"dependency:{kind}",
            "dependency_kind": kind,
            "monitor_source_id": "independent-dependency-monitor:a",
            "affected_source_ids": (
                "independent-zone-sensor:a",
                "production-ai:planner",
            ),
        }
    )


def configuration(kind: str = "power") -> SupervisorConfiguration:
    return SupervisorConfiguration(
        configuration_id="configuration:common-cause",
        revision=1,
        scope_id="SCOPE-ROBOT-CELL-001",
        valid_from=datetime(2026, 9, 3, 11, 0, tzinfo=UTC),
        valid_until=datetime(2026, 9, 3, 13, 0, tzinfo=UTC),
        required_source_ids=(
            "independent-dependency-monitor:a",
            "independent-zone-sensor:a",
            "production-ai:planner",
        ),
        max_observation_age_seconds=0.5,
        max_receive_delay_seconds=0.2,
        max_future_skew_seconds=0.0,
        max_correlation_delay_seconds=0.25,
        approved_calibration_sha256=("sha256:" + "d" * 64,),
        dependency_bindings=(binding(kind),),
        max_speed_mps=1.0,
        max_acceleration_mps2=2.0,
        signer_id="safety-config-signer:common-cause",
        signature="ed25519:" + "00" * 64,
    )


def dependency(kind: str = "power", state: str = "healthy") -> SharedDependencyObservation:
    return SharedDependencyObservation.model_validate(
        {
            "observation_id": f"dependency-observation:{kind}",
            "run_id": "run:common-cause",
            "source_id": "independent-dependency-monitor:a",
            "sequence_number": 0,
            "observed_at": NOW,
            "received_at": NOW,
            "input_sha256": SHA_B,
            "dependency_id": f"dependency:{kind}",
            "dependency_kind": kind,
            "dependency_state": state,
            "affected_source_ids": (
                "independent-zone-sensor:a",
                "production-ai:planner",
            ),
            "configuration_sha256": CONFIG,
            "independence_state": "not_established",
        }
    )


def source_health() -> SourceHealthObservation:
    return SourceHealthObservation(
        observation_id="health:common-cause",
        run_id="run:common-cause",
        source_id="independent-health-monitor:a",
        sequence_number=0,
        observed_at=NOW,
        received_at=NOW,
        input_sha256=SHA_C,
        monitored_source_id="independent-zone-sensor:a",
        source_state="healthy",
        clock_state="healthy",
        last_source_sequence=0,
    )


@pytest.mark.parametrize("kind", KINDS)
def test_each_declared_shared_dependency_failure_is_explicit(kind: str) -> None:
    result = evaluate_common_cause(
        (dependency(kind, "failed"),),
        configuration=configuration(kind),
        configuration_sha256=CONFIG,
        source_health=(source_health(),),
    )

    assert result.integrity_state == "unresolved"
    assert f"shared_dependency_failed:{kind}" in result.reason_codes
    assert "shared_dependency_health_contradiction" in result.reason_codes
    assert result.independence_established is False
    assert result.operational_authority == "none"


def test_missing_or_wrong_configuration_dependency_evidence_fails_closed() -> None:
    missing = evaluate_common_cause(
        (),
        configuration=configuration(),
        configuration_sha256=CONFIG,
        source_health=(source_health(),),
    )
    wrong_configuration = evaluate_common_cause(
        (dependency().model_copy(update={"configuration_sha256": "sha256:" + "e" * 64}),),
        configuration=configuration(),
        configuration_sha256=CONFIG,
        source_health=(source_health(),),
    )

    assert "shared_dependency_observation_missing" in missing.reason_codes
    assert "shared_dependency_configuration_mismatch" in wrong_configuration.reason_codes
    assert missing.independence_established is False
    assert wrong_configuration.independence_established is False


def test_healthy_represented_dependency_does_not_claim_independence() -> None:
    result = evaluate_common_cause(
        (dependency(),),
        configuration=configuration(),
        configuration_sha256=CONFIG,
        source_health=(source_health(),),
    )

    assert result.integrity_state == "represented_healthy_unvalidated"
    assert result.reason_codes == ("common_cause_unassessed",)
    assert result.independence_established is False
    assert result.certification_state == "not_established"


def test_canonical_common_cause_campaign_covers_every_declared_dependency_kind() -> None:
    root = Path(__file__).resolve().parents[2]
    completed = subprocess.run(
        [sys.executable, "scripts/verify_common_cause_campaign.py"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["verification"] == "shared_dependency_common_cause_campaign_v1"
    assert report["case_count"] == len(KINDS)
    assert all(case["integrity_state"] == "unresolved" for case in report["cases"])
    assert all(case["independence_established"] is False for case in report["cases"])
    assert report["certification_state"] == "not_established"
    assert report["operational_authority"] == "none"
    assert report["physical_stop"] == "not_established"
