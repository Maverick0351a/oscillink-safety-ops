"""Frozen benchmark contracts and deterministic execution tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from oscillink_safety_ops.benchmark import BenchmarkCase, execute_case, parse_case_line


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def minimal_case() -> dict[str, object]:
    return {
        "schema_version": 1,
        "case_id": "case:nominal-idle",
        "title": "Nominal idle monitoring",
        "fault_families": ["nominal_monitoring"],
        "run_id": "run:benchmark:nominal-idle",
        "start_at": "2026-09-03T12:00:00Z",
        "steps": [
            {
                "kind": "evaluate",
                "evaluation_time": "2026-09-03T12:00:00Z",
                "observations": [
                    {
                        "schema_version": 1,
                        "observation_id": "command:0",
                        "run_id": "run:benchmark:nominal-idle",
                        "source_id": "production-ai:planner",
                        "sequence_number": 0,
                        "observed_at": "2026-09-03T12:00:00Z",
                        "received_at": "2026-09-03T12:00:00Z",
                        "source_domain": "production_ai",
                        "command_id": "command-id:0",
                        "command_kind": "idle",
                        "motion_requested": False,
                    },
                    {
                        "schema_version": 1,
                        "observation_id": "physical:0",
                        "run_id": "run:benchmark:nominal-idle",
                        "source_id": "independent-zone-sensor:a",
                        "sequence_number": 0,
                        "observed_at": "2026-09-03T12:00:00Z",
                        "received_at": "2026-09-03T12:00:00Z",
                        "source_domain": "independent_physical_observation",
                        "zone_id": "zone:synthetic-protected",
                        "occupancy": "clear",
                        "motion_state": "stopped",
                        "speed_mps": 0.0,
                        "acceleration_mps2": 0.0,
                        "quality": "good",
                        "calibration_sha256": "sha256:" + "d" * 64,
                    },
                    {
                        "schema_version": 1,
                        "observation_id": "health:0",
                        "run_id": "run:benchmark:nominal-idle",
                        "source_id": "independent-health-monitor:a",
                        "sequence_number": 0,
                        "observed_at": "2026-09-03T12:00:00Z",
                        "received_at": "2026-09-03T12:00:00Z",
                        "source_domain": "independent_source_health",
                        "monitored_source_id": "independent-zone-sensor:a",
                        "source_state": "healthy",
                        "clock_state": "healthy",
                        "last_source_sequence": 0,
                    },
                    {
                        "schema_version": 1,
                        "observation_id": "dependency:0",
                        "run_id": "run:benchmark:nominal-idle",
                        "source_id": "independent-dependency-monitor:a",
                        "sequence_number": 0,
                        "observed_at": "2026-09-03T12:00:00Z",
                        "received_at": "2026-09-03T12:00:00Z",
                        "source_domain": "independent_dependency_health",
                        "dependency_id": "dependency:shared-infrastructure",
                        "dependency_kind": "compute",
                        "dependency_state": "healthy",
                        "affected_source_ids": [
                            "independent-zone-sensor:a",
                            "production-ai:planner",
                        ],
                        "configuration_sha256": (
                            "sha256:38068747cb9a5927c334697e6a2649feed488465c9bba3612c85e47695640b86"
                        ),
                        "independence_state": "not_established",
                    },
                ],
            }
        ],
        "synthetic_evidence": True,
        "operational_authority": "none",
    }


def test_case_line_is_exact_canonical_strict_and_hash_bound() -> None:
    raw = _canonical(minimal_case())

    parsed = parse_case_line(raw)

    assert isinstance(parsed.case, BenchmarkCase)
    assert parsed.case.case_id == "case:nominal-idle"
    assert parsed.sha256.startswith("sha256:")
    assert parsed.byte_count == len(raw)

    changed = minimal_case()
    changed["unknown"] = True
    with pytest.raises(ValidationError):
        parse_case_line(_canonical(changed))
    with pytest.raises(ValueError, match="canonical"):
        parse_case_line(raw.replace(b"\n", b"\r\n"))


def test_execute_nominal_case_is_byte_deterministic_and_exposes_safety_boundaries(
    tmp_path: Path,
) -> None:
    repository = Path(__file__).resolve().parents[2]
    source = repository / "scenarios" / "robot_cell_v1"
    (tmp_path / "configuration.json").write_bytes((source / "configuration.json").read_bytes())
    (tmp_path / "authority.json").write_bytes((source / "authority.json").read_bytes())
    parsed = parse_case_line(_canonical(minimal_case()))

    first = execute_case(parsed, benchmark_root=tmp_path)
    second = execute_case(parsed, benchmark_root=tmp_path)

    assert first.canonical_bytes == second.canonical_bytes
    assert first.result["case_sha256"] == parsed.sha256
    assert first.result["outcome_action"] == "none"
    assert first.result["final"]["policy_state"] == "monitoring_normal"
    assert first.result["final"]["physical_stop"] == "not_established"
    assert first.result["final"]["common_cause_integrity"] == "represented_healthy_unvalidated"
    assert first.result["final"]["independence_established"] is False
    assert first.result["final"]["certification_state"] == "not_established"
    assert first.result["synthetic_evidence"] is True
    assert first.result["operational_authority"] == "none"


def test_lifecycle_case_preserves_latch_rejects_production_and_requires_staged_recovery(
    tmp_path: Path,
) -> None:
    repository = Path(__file__).resolve().parents[2]
    source = repository / "scenarios" / "robot_cell_v1"
    (tmp_path / "configuration.json").write_bytes((source / "configuration.json").read_bytes())
    (tmp_path / "authority.json").write_bytes((source / "authority.json").read_bytes())
    document = minimal_case()
    steps = document["steps"]
    assert isinstance(steps, list)
    evaluation = steps[0]
    assert isinstance(evaluation, dict)
    observations = evaluation["observations"]
    assert isinstance(observations, list)
    physical = observations[1]
    command = observations[0]
    assert isinstance(physical, dict) and isinstance(command, dict)
    command.update(command_kind="motion_requested", motion_requested=True)
    physical.update(occupancy="present", motion_state="moving", speed_mps=0.5)
    steps.extend(
        [
            {"kind": "restart"},
            {
                "kind": "production_authority_attempt",
                "attempted_operation": "reset",
                "actor_domain": "production_ai",
            },
            {
                "kind": "acknowledgment",
                "evaluation_time": "2026-09-03T12:00:00.100000Z",
                "observed_at": "2026-09-03T12:00:00.100000Z",
                "status": "received_by_simulated_fixture",
                "identity_mode": "matching",
            },
            {
                "kind": "assess_reset",
                "evaluation_time": "2026-09-03T12:00:00.200000Z",
                "conditions": {
                    "occupancy_clear": True,
                    "motion_stopped": True,
                    "sources_healthy": True,
                    "configuration_unchanged": True,
                    "output_resolved": True,
                },
            },
            {
                "kind": "recovery_event",
                "event_kind": "reset",
                "evaluation_time": "2026-09-03T12:00:00.300000Z",
                "observed_at": "2026-09-03T12:00:00.300000Z",
            },
            {
                "kind": "recovery_event",
                "event_kind": "rearm",
                "evaluation_time": "2026-09-03T12:00:00.400000Z",
                "observed_at": "2026-09-03T12:00:00.400000Z",
            },
            {
                "kind": "recovery_event",
                "event_kind": "recovery_confirmed",
                "evaluation_time": "2026-09-03T12:00:00.500000Z",
                "observed_at": "2026-09-03T12:00:00.500000Z",
            },
            {
                "kind": "recovery_event",
                "event_kind": "fresh_start",
                "evaluation_time": "2026-09-03T12:00:00.600000Z",
                "observed_at": "2026-09-03T12:00:00.600000Z",
            },
        ]
    )

    result = execute_case(parse_case_line(_canonical(document)), benchmark_root=tmp_path).result

    assert result["timeline"][1]["latched_preserved"] is True
    assert result["timeline"][2]["disposition"] == "rejected_no_authority"
    assert result["final"]["policy_state"] == "initializing"
    assert result["final"]["latched"] is False
    assert result["final"]["recovery_stage"] == "initializing"
    assert result["final"]["physical_stop"] == "not_established"
