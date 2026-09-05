"""Verify represented shared-dependency failures remain unresolved."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from oscillink_safety_ops.runtime.common_cause import evaluate_common_cause
from oscillink_safety_ops.runtime.contracts import (
    DependencyBinding,
    SharedDependencyObservation,
    SourceHealthObservation,
    SupervisorConfiguration,
)

NOW = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)
CONFIGURATION_SHA256 = "sha256:" + "a" * 64
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


def _configuration(kind: str) -> SupervisorConfiguration:
    binding = DependencyBinding(
        dependency_id=f"dependency:{kind}",
        dependency_kind=kind,
        monitor_source_id="independent-dependency-monitor:a",
        affected_source_ids=("independent-zone-sensor:a", "production-ai:planner"),
    )
    return SupervisorConfiguration(
        configuration_id="configuration:common-cause-campaign",
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
        dependency_bindings=(binding,),
        max_speed_mps=1.0,
        max_acceleration_mps2=2.0,
        signer_id="safety-config-signer:common-cause-campaign",
        signature="ed25519:" + "00" * 64,
    )


def verify_campaign() -> dict[str, object]:
    cases = []
    for index, kind in enumerate(KINDS):
        observation = SharedDependencyObservation(
            observation_id=f"dependency-observation:{kind}",
            run_id="run:common-cause-campaign",
            source_id="independent-dependency-monitor:a",
            sequence_number=0,
            observed_at=NOW,
            received_at=NOW,
            input_sha256="sha256:" + format(index + 1, "064x"),
            dependency_id=f"dependency:{kind}",
            dependency_kind=kind,
            dependency_state="failed",
            affected_source_ids=("independent-zone-sensor:a", "production-ai:planner"),
            configuration_sha256=CONFIGURATION_SHA256,
        )
        health = SourceHealthObservation(
            observation_id=f"health:{kind}",
            run_id="run:common-cause-campaign",
            source_id="independent-health-monitor:a",
            sequence_number=0,
            observed_at=NOW,
            received_at=NOW,
            input_sha256="sha256:" + format(index + 100, "064x"),
            monitored_source_id="independent-zone-sensor:a",
            source_state="healthy",
            clock_state="healthy",
            last_source_sequence=0,
        )
        result = evaluate_common_cause(
            (observation,),
            configuration=_configuration(kind),
            configuration_sha256=CONFIGURATION_SHA256,
            source_health=(health,),
        )
        expected = f"shared_dependency_failed:{kind}"
        if (
            result.integrity_state != "unresolved"
            or expected not in result.reason_codes
            or "shared_dependency_health_contradiction" not in result.reason_codes
            or result.independence_established is not False
        ):
            raise RuntimeError(f"common-cause case did not fail closed: {kind}")
        cases.append(
            {
                "dependency_kind": kind,
                "integrity_state": result.integrity_state,
                "independence_established": result.independence_established,
                "reason_codes": result.reason_codes,
            }
        )
    return {
        "schema_version": 1,
        "verification": "shared_dependency_common_cause_campaign_v1",
        "case_count": len(cases),
        "cases": cases,
        "certification_state": "not_established",
        "operational_authority": "none",
        "physical_stop": "not_established",
    }


def main() -> None:
    print(json.dumps(verify_campaign(), allow_nan=False, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
