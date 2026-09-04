"""Generated benchmark case-set coverage tests."""

from __future__ import annotations

from pathlib import Path

from oscillink_safety_ops.benchmark import canonical_json, execute_case, parse_case_line
from scripts.generate_benchmark import (
    REQUIRED_FAULT_FAMILIES,
    build_case_documents,
    generate_benchmark,
)

REQUIRED_CASE_IDS = {
    "case:nominal-idle",
    "case:nominal-commanded-measured-motion",
    "case:present-commanded-motion",
    "case:present-measured-motion",
    "case:entering-commanded-motion",
    "case:entering-measured-motion",
    "case:unknown-commanded-motion",
    "case:unknown-measured-motion",
    "case:orphan-unexpected-motion",
    "case:command-actual-mismatch",
    "case:speed-at-boundary",
    "case:speed-above-boundary",
    "case:acceleration-at-boundary",
    "case:acceleration-above-boundary",
    "case:acceleration-unavailable",
    "case:stale-sensing",
    "case:frozen-sensing",
    "case:missing-sensing",
    "case:contradictory-sensing",
    "case:degraded-source-health",
    "case:failed-source-health",
    "case:sequence-gap",
    "case:sequence-rollback",
    "case:future-time",
    "case:timestamp-rollback",
    "case:configuration-substitution",
    "case:configuration-expiry",
    "case:output-uncertainty",
    "case:false-acknowledgment",
    "case:restart-latch-preservation",
    "case:production-reset-attempt",
    "case:production-admin-attempt",
    "case:reset-not-permitted",
    "case:valid-staged-recovery",
    "case:simultaneous-priority-faults",
    "case:simultaneous-source-motion-faults",
}


def test_generated_case_set_is_strict_deterministic_and_covers_required_scenarios() -> None:
    first = build_case_documents()
    second = build_case_documents()

    assert first == second
    assert len(first) >= 20
    assert {case["case_id"] for case in first} == REQUIRED_CASE_IDS
    assert {family for case in first for family in case["fault_families"]} == set(
        REQUIRED_FAULT_FAMILIES
    )
    assert len({canonical_json(case) for case in first}) == len(first)
    for document in first:
        parsed = parse_case_line(canonical_json(document))
        assert parsed.case.synthetic_evidence is True
        assert parsed.case.operational_authority == "none"


def test_every_generated_case_executes_exactly_and_key_boundary_oracles_hold(
    tmp_path: Path,
) -> None:
    repository = Path(__file__).resolve().parents[2]
    source = repository / "scenarios" / "robot_cell_v1"
    (tmp_path / "configuration.json").write_bytes((source / "configuration.json").read_bytes())
    (tmp_path / "authority.json").write_bytes((source / "authority.json").read_bytes())

    results = {
        document["case_id"]: execute_case(
            parse_case_line(canonical_json(document)), benchmark_root=tmp_path
        )
        for document in build_case_documents()
    }

    assert len(results) == 36
    assert results["case:speed-at-boundary"].result["outcome_action"] == "none"
    assert (
        results["case:speed-above-boundary"].result["final"]["first_out_reason"]
        == "excessive_speed"
    )
    assert results["case:acceleration-at-boundary"].result["outcome_action"] == "none"
    assert (
        results["case:acceleration-above-boundary"].result["final"]["first_out_reason"]
        == "excessive_acceleration"
    )
    assert (
        results["case:simultaneous-priority-faults"].result["final"]["first_out_reason"]
        == "configuration_changed_mid_run"
    )
    assert (
        results["case:simultaneous-source-motion-faults"].result["final"]["first_out_reason"]
        == "stale_observation"
    )
    attribution = results["case:command-actual-mismatch"].result["timeline"][1]
    assert attribution["action"] == "protective_stop_request"
    assert attribution["reason_codes"] == [
        "motion_direction_mismatch",
        "motion_frame_mismatch",
        "motion_program_mismatch",
    ]
    assert attribution["physical_stop"] == "not_established"
    late_attribution = results["case:command-actual-mismatch"].result["timeline"][2]
    assert late_attribution["action"] == "protective_stop_request"
    assert "command_response_late" in late_attribution["reason_codes"]
    assert late_attribution["physical_stop"] == "not_established"
    for execution in results.values():
        reasons = execution.result["final"]["reason_codes"]
        assert reasons == sorted(set(reasons))
        assert execution.result["final"]["physical_stop"] == "not_established"


def test_generator_writes_repeatable_exact_outputs_metrics_schemas_and_manifest(
    tmp_path: Path,
) -> None:
    repository = Path(__file__).resolve().parents[2]
    destination = tmp_path / "robot_cell_v1"

    first = generate_benchmark(
        destination,
        source_repository=repository,
        runtime_baseline_commit="dc27cf6ce25be97b0cb70b698679445103409e7b",
    )
    first_bytes = {
        path.relative_to(destination).as_posix(): path.read_bytes()
        for path in destination.rglob("*")
        if path.is_file()
    }
    second = generate_benchmark(
        destination,
        source_repository=repository,
        runtime_baseline_commit="dc27cf6ce25be97b0cb70b698679445103409e7b",
    )
    second_bytes = {
        path.relative_to(destination).as_posix(): path.read_bytes()
        for path in destination.rglob("*")
        if path.is_file()
    }

    assert first == second
    assert first_bytes == second_bytes
    assert first["total_cases"] == 36
    assert first["exact_matches"] == 36
    assert first["deterministic_repeatability"]["matching_cases"] == 36
    assert "latency" not in str(first).lower()
    assert set(first_bytes) == {
        "DATASET_CARD.md",
        "README.md",
        "SAFETY_MANAGER_DEMO.md",
        "authority.json",
        "benchmark-case.schema.json",
        "benchmark-manifest.json",
        "benchmark-result.schema.json",
        "cases.jsonl",
        "configuration.json",
        "expected-results.jsonl",
        "metrics.json",
    }
    demo = first_bytes["SAFETY_MANAGER_DEMO.md"].decode("utf-8")
    assert "36/36 exact byte matches across 3 runs per case" in demo
    assert "case:valid-staged-recovery" in demo
    assert "physical stop remains `not_established`" in demo
