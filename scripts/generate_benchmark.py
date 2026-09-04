"""Generate the frozen synthetic robot-cell benchmark and demo evidence."""
# ruff: noqa: E501 -- exact generated Markdown copy includes long source lines

from __future__ import annotations

import hashlib
import shutil
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

from oscillink_safety_ops.benchmark import (
    BenchmarkCase,
    BenchmarkResult,
    canonical_json,
    execute_case,
    parse_case_line,
)

T0 = "2026-09-03T12:00:00Z"
T01 = "2026-09-03T12:00:00.100000Z"
T02 = "2026-09-03T12:00:00.200000Z"
T03 = "2026-09-03T12:00:00.300000Z"
T04 = "2026-09-03T12:00:00.400000Z"
T05 = "2026-09-03T12:00:00.500000Z"
T06 = "2026-09-03T12:00:00.600000Z"
REQUIRED_FAULT_FAMILIES = (
    "authority_boundary",
    "configuration_integrity",
    "motion_correlation",
    "motion_envelope",
    "nominal_monitoring",
    "occupancy_motion",
    "output_integrity",
    "recovery_lifecycle",
    "restart_persistence",
    "sensing_integrity",
    "simultaneous_faults",
    "time_order",
)
RUNTIME_BASELINE_COMMIT = "9485b192151d9440776938ae5dd28fa8a9befac1"
SOURCE_PATHS = (
    "scripts/generate_benchmark.py",
    "src/oscillink_safety_ops/benchmark.py",
)


def _run(case_id: str) -> str:
    return "run:benchmark:" + case_id.removeprefix("case:")


def _observations(
    case_id: str,
    *,
    sequence: int = 0,
    observed_at: str = T0,
    received_at: str | None = None,
    command_motion: bool = False,
    occupancy: str = "clear",
    motion_state: str = "stopped",
    speed_mps: float | None = 0.0,
    acceleration_mps2: float | None = 0.0,
    quality: str = "good",
    health_state: str = "healthy",
    clock_state: str = "healthy",
    health_last_sequence: int | None = None,
    tag: str | None = None,
    command_direction: str | None = "positive",
    physical_direction: str | None = "positive",
    command_frame_id: str | None = "frame:robot-base",
    physical_frame_id: str | None = "frame:robot-base",
    command_program_id: str | None = "program:synthetic-cell",
    physical_program_id: str | None = "program:synthetic-cell",
) -> list[dict[str, Any]]:
    run_id = _run(case_id)
    received = received_at or observed_at
    suffix = tag or str(sequence)
    last_sequence = sequence if health_last_sequence is None else health_last_sequence
    return [
        {
            "schema_version": 1,
            "observation_id": f"command:{suffix}",
            "run_id": run_id,
            "source_id": "production-ai:planner",
            "sequence_number": sequence,
            "observed_at": observed_at,
            "received_at": received,
            "source_domain": "production_ai",
            "command_id": f"command-id:{suffix}",
            "command_kind": "motion_requested" if command_motion else "idle",
            "motion_requested": command_motion,
            "motion_direction": command_direction,
            "frame_id": command_frame_id,
            "program_id": command_program_id,
        },
        {
            "schema_version": 1,
            "observation_id": f"physical:{suffix}",
            "run_id": run_id,
            "source_id": "independent-zone-sensor:a",
            "sequence_number": sequence,
            "observed_at": observed_at,
            "received_at": received,
            "source_domain": "independent_physical_observation",
            "zone_id": "zone:synthetic-protected",
            "occupancy": occupancy,
            "motion_state": motion_state,
            "speed_mps": speed_mps,
            "acceleration_mps2": acceleration_mps2,
            "quality": quality,
            "calibration_sha256": "sha256:" + "d" * 64,
            "motion_direction": physical_direction,
            "frame_id": physical_frame_id,
            "program_id": physical_program_id,
        },
        {
            "schema_version": 1,
            "observation_id": f"health:{suffix}",
            "run_id": run_id,
            "source_id": "independent-health-monitor:a",
            "sequence_number": sequence,
            "observed_at": observed_at,
            "received_at": received,
            "source_domain": "independent_source_health",
            "monitored_source_id": "independent-zone-sensor:a",
            "source_state": health_state,
            "clock_state": clock_state,
            "last_source_sequence": last_sequence,
        },
    ]


def _evaluate(observations: list[dict[str, Any]], at: str, **flags: bool) -> dict[str, Any]:
    return {"kind": "evaluate", "evaluation_time": at, "observations": observations, **flags}


def _case(
    case_id: str, title: str, families: tuple[str, ...], steps: list[dict[str, Any]]
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "case_id": case_id,
        "title": title,
        "fault_families": sorted(families),
        "run_id": _run(case_id),
        "start_at": T0,
        "steps": steps,
        "synthetic_evidence": True,
        "operational_authority": "none",
    }


def _ack(
    identity: str = "matching", status: str = "received_by_simulated_fixture"
) -> dict[str, Any]:
    return {
        "kind": "acknowledgment",
        "evaluation_time": T01,
        "observed_at": T01,
        "status": status,
        "identity_mode": identity,
    }


def _conditions(**changes: bool) -> dict[str, bool]:
    result = {
        "occupancy_clear": True,
        "motion_stopped": True,
        "sources_healthy": True,
        "configuration_unchanged": True,
        "output_resolved": True,
    }
    result.update(changes)
    return result


def _hazard(case_id: str) -> dict[str, Any]:
    return _evaluate(
        _observations(
            case_id,
            command_motion=True,
            occupancy="present",
            motion_state="moving",
            speed_mps=0.5,
            acceleration_mps2=0.5,
        ),
        T0,
    )


def build_case_documents() -> list[dict[str, Any]]:
    """Return the complete deterministic, project-authored synthetic case set."""

    cases: list[dict[str, Any]] = []

    def add(
        case_id: str, title: str, families: tuple[str, ...], steps: list[dict[str, Any]]
    ) -> None:
        cases.append(_case(case_id, title, families, steps))

    add(
        "case:nominal-idle",
        "Nominal idle monitoring",
        ("nominal_monitoring",),
        [_evaluate(_observations("case:nominal-idle"), T0)],
    )
    add(
        "case:nominal-commanded-measured-motion",
        "Nominal aligned represented motion",
        ("nominal_monitoring",),
        [
            _evaluate(
                _observations(
                    "case:nominal-commanded-measured-motion",
                    command_motion=True,
                    motion_state="moving",
                    speed_mps=0.5,
                    acceleration_mps2=0.5,
                ),
                T0,
            )
        ],
    )
    for occupancy in ("present", "entering", "unknown"):
        quality = "degraded" if occupancy == "unknown" else "good"
        commanded_id = f"case:{occupancy}-commanded-motion"
        measured_id = f"case:{occupancy}-measured-motion"
        add(
            commanded_id,
            f"{occupancy.title()} occupancy with commanded motion",
            ("occupancy_motion",),
            [
                _evaluate(
                    _observations(
                        commanded_id, command_motion=True, occupancy=occupancy, quality=quality
                    ),
                    T0,
                )
            ],
        )
        add(
            measured_id,
            f"{occupancy.title()} occupancy with measured motion",
            ("motion_correlation", "occupancy_motion"),
            [
                _evaluate(
                    _observations(
                        measured_id,
                        occupancy=occupancy,
                        motion_state="moving",
                        speed_mps=0.5,
                        acceleration_mps2=0.5,
                        quality=quality,
                    ),
                    T0,
                )
            ],
        )
    add(
        "case:orphan-unexpected-motion",
        "Orphan and unexpected measured motion",
        ("motion_correlation",),
        [
            _evaluate(
                _observations(
                    "case:orphan-unexpected-motion",
                    motion_state="moving",
                    speed_mps=0.5,
                    acceleration_mps2=0.5,
                ),
                T0,
            )
        ],
    )
    add(
        "case:command-actual-mismatch",
        "Commanded motion with state and attribution mismatch",
        ("motion_correlation",),
        [
            _evaluate(_observations("case:command-actual-mismatch", command_motion=True), T0),
            _evaluate(
                _observations(
                    "case:command-actual-mismatch",
                    sequence=1,
                    observed_at=T01,
                    command_motion=True,
                    motion_state="moving",
                    speed_mps=0.5,
                    acceleration_mps2=0.5,
                    physical_direction="negative",
                    physical_frame_id="frame:workpiece",
                    physical_program_id="program:unexpected",
                ),
                T01,
            ),
        ],
    )
    for case_id, title, speed, acceleration in (
        ("case:speed-at-boundary", "Speed exactly at configured boundary", 1.0, 0.5),
        ("case:speed-above-boundary", "Speed above configured boundary", 1.000001, 0.5),
        ("case:acceleration-at-boundary", "Acceleration exactly at configured boundary", 0.5, 2.0),
        (
            "case:acceleration-above-boundary",
            "Acceleration above configured boundary",
            0.5,
            2.000001,
        ),
    ):
        add(
            case_id,
            title,
            ("motion_envelope",),
            [
                _evaluate(
                    _observations(
                        case_id,
                        command_motion=True,
                        motion_state="moving",
                        speed_mps=speed,
                        acceleration_mps2=acceleration,
                    ),
                    T0,
                )
            ],
        )
    add(
        "case:acceleration-unavailable",
        "Acceleration unavailable during represented motion",
        ("motion_envelope",),
        [
            _evaluate(
                _observations(
                    "case:acceleration-unavailable",
                    command_motion=True,
                    motion_state="moving",
                    speed_mps=0.5,
                    acceleration_mps2=None,
                ),
                T0,
            )
        ],
    )
    stale = _observations("case:stale-sensing", observed_at="2026-09-03T11:59:59Z", received_at=T0)
    add(
        "case:stale-sensing",
        "Stale independent sensing",
        ("sensing_integrity",),
        [_evaluate(stale, T0)],
    )
    frozen_id = "case:frozen-sensing"
    add(
        frozen_id,
        "Frozen source timestamps",
        ("sensing_integrity",),
        [
            _evaluate(_observations(frozen_id), T0),
            _evaluate(_observations(frozen_id, sequence=1, observed_at=T0, received_at=T01), T01),
        ],
    )
    missing = _observations("case:missing-sensing")
    del missing[1]
    add(
        "case:missing-sensing",
        "Missing required physical sensing",
        ("sensing_integrity",),
        [_evaluate(missing, T0)],
    )
    contradictory = _observations(
        "case:contradictory-sensing",
        occupancy="contradictory",
        motion_state="contradictory",
        speed_mps=None,
        acceleration_mps2=None,
        quality="contradictory",
    )
    add(
        "case:contradictory-sensing",
        "Contradictory physical sensing",
        ("sensing_integrity",),
        [_evaluate(contradictory, T0)],
    )
    for case_id, title, health in (
        ("case:degraded-source-health", "Degraded independent source health", "degraded"),
        ("case:failed-source-health", "Failed independent source health", "failed"),
    ):
        add(
            case_id,
            title,
            ("sensing_integrity",),
            [_evaluate(_observations(case_id, health_state=health), T0)],
        )
    gap_id = "case:sequence-gap"
    add(
        gap_id,
        "Source sequence gap",
        ("time_order",),
        [
            _evaluate(_observations(gap_id), T0),
            _evaluate(_observations(gap_id, sequence=2, observed_at=T02), T02),
        ],
    )
    rollback_id = "case:sequence-rollback"
    add(
        rollback_id,
        "Source sequence rollback",
        ("time_order",),
        [
            _evaluate(_observations(rollback_id), T0),
            _evaluate(_observations(rollback_id, sequence=1, observed_at=T01), T01),
            _evaluate(_observations(rollback_id, sequence=0, observed_at=T02, tag="rollback"), T02),
        ],
    )
    future_id = "case:future-time"
    add(
        future_id,
        "Observation timestamp in the future",
        ("time_order",),
        [_evaluate(_observations(future_id, observed_at=T01), T0)],
    )
    timestamp_id = "case:timestamp-rollback"
    add(
        timestamp_id,
        "Observation timestamp rollback",
        ("time_order",),
        [
            _evaluate(_observations(timestamp_id), T0),
            _evaluate(_observations(timestamp_id, sequence=1, observed_at=T02), T02),
            _evaluate(
                _observations(timestamp_id, sequence=2, observed_at=T01, received_at=T03), T03
            ),
        ],
    )
    substitution_id = "case:configuration-substitution"
    add(
        substitution_id,
        "Detected mid-run configuration substitution",
        ("configuration_integrity",),
        [_evaluate(_observations(substitution_id), T0, candidate_configuration_changed=True)],
    )
    expiry_id = "case:configuration-expiry"
    add(
        expiry_id,
        "Configuration expiry during run",
        ("configuration_integrity",),
        [
            _evaluate(_observations(expiry_id), T0),
            _evaluate(
                _observations(expiry_id, sequence=1, observed_at="2026-09-04T00:00:00Z"),
                "2026-09-04T00:00:00Z",
            ),
        ],
    )
    uncertainty_id = "case:output-uncertainty"
    add(
        uncertainty_id,
        "Output path uncertainty",
        ("output_integrity",),
        [_evaluate(_observations(uncertainty_id), T0, output_uncertain=True)],
    )
    false_ack_id = "case:false-acknowledgment"
    add(
        false_ack_id,
        "Mismatched false acknowledgment",
        ("output_integrity",),
        [_hazard(false_ack_id), _ack("mismatched")],
    )
    restart_id = "case:restart-latch-preservation"
    add(
        restart_id,
        "Process restart preserves intervention latch",
        ("restart_persistence",),
        [_hazard(restart_id), {"kind": "restart"}],
    )
    reset_attempt_id = "case:production-reset-attempt"
    add(
        reset_attempt_id,
        "Production AI reset attempt denied",
        ("authority_boundary",),
        [
            _hazard(reset_attempt_id),
            {
                "kind": "production_authority_attempt",
                "attempted_operation": "reset",
                "actor_domain": "production_ai",
            },
        ],
    )
    admin_id = "case:production-admin-attempt"
    add(
        admin_id,
        "Production AI administration attempt denied",
        ("authority_boundary",),
        [
            _hazard(admin_id),
            {
                "kind": "production_authority_attempt",
                "attempted_operation": "administration",
                "actor_domain": "production_ai",
            },
        ],
    )
    blocked_id = "case:reset-not-permitted"
    add(
        blocked_id,
        "Reset blocked while occupancy remains unresolved",
        ("recovery_lifecycle",),
        [
            _hazard(blocked_id),
            _ack(),
            {
                "kind": "assess_reset",
                "evaluation_time": T02,
                "conditions": _conditions(occupancy_clear=False),
            },
        ],
    )
    recovery_id = "case:valid-staged-recovery"
    add(
        recovery_id,
        "Valid staged reset rearm recovery and fresh start",
        ("recovery_lifecycle",),
        [
            _hazard(recovery_id),
            _ack(),
            {"kind": "assess_reset", "evaluation_time": T02, "conditions": _conditions()},
            {
                "kind": "recovery_event",
                "event_kind": "reset",
                "evaluation_time": T03,
                "observed_at": T03,
            },
            {
                "kind": "recovery_event",
                "event_kind": "rearm",
                "evaluation_time": T04,
                "observed_at": T04,
            },
            {
                "kind": "recovery_event",
                "event_kind": "recovery_confirmed",
                "evaluation_time": T05,
                "observed_at": T05,
            },
            {
                "kind": "recovery_event",
                "event_kind": "fresh_start",
                "evaluation_time": T06,
                "observed_at": T06,
            },
        ],
    )
    priority_id = "case:simultaneous-priority-faults"
    add(
        priority_id,
        "Simultaneous configuration output occupancy and motion faults",
        ("configuration_integrity", "output_integrity", "simultaneous_faults"),
        [
            _evaluate(
                _observations(
                    priority_id,
                    occupancy="present",
                    motion_state="moving",
                    speed_mps=1.5,
                    acceleration_mps2=2.5,
                ),
                T0,
                candidate_configuration_changed=True,
                output_uncertain=True,
            )
        ],
    )
    source_motion_id = "case:simultaneous-source-motion-faults"
    simultaneous = _observations(
        source_motion_id,
        observed_at="2026-09-03T11:59:59Z",
        received_at=T0,
        occupancy="entering",
        motion_state="moving",
        speed_mps=1.5,
        acceleration_mps2=2.5,
    )
    add(
        source_motion_id,
        "Simultaneous stale sensing and hazardous represented motion",
        ("sensing_integrity", "simultaneous_faults"),
        [_evaluate(simultaneous, T0)],
    )
    return deepcopy(cases)


BENCHMARK_README = """# Robot cell v1 exact-byte benchmark

This frozen corpus contains project-authored synthetic closed-file cases for deterministic software
behavior. It contains no customer, facility, hardware, incident, or field data. A passing verifier
does not establish a physical stop, safe operation, PLr, SIL, stopping time, diagnostic coverage,
application validation, common-cause independence, certification, or compliance.

## Files and exactness

`cases.jsonl` and `expected-results.jsonl` use canonical UTF-8 JSON: sorted object keys, compact
separators, one object per line, and LF endings. The strict machine-readable schemas describe their
records. `metrics.json` is mechanically derived from cases and exact expected outputs. The canonical
manifest binds every other regular file in this directory by SHA-256 and positive byte count, plus
the frozen runtime baseline, exact benchmark/generator source bytes and their source-tree hash,
runtime format, configuration, public authority, and scenario identities. Repository HEAD may move;
the exact source hashes may not. The manifest cannot hash itself without a circular identity. No
private key is included.

## Verify locally

```bash
PYTHONPATH= uv run safety-ops benchmark verify --root benchmark/robot_cell_v1
PYTHONPATH= uv run python scripts/verify_benchmark.py benchmark/robot_cell_v1
```

Verification is local and performs no network access. Reported counts are correctness and coverage
counts only; no wall-clock latency is collected or presented as safety evidence.
"""

DATASET_CARD = """---
pretty_name: Oscillink Synthetic Robot Cell Exact-Byte Benchmark v1
license: apache-2.0
language:
  - en
tags:
  - robotics
  - safety
  - synthetic
  - deterministic
size_categories:
  - n<1K
---

# Oscillink Synthetic Robot Cell Exact-Byte Benchmark v1

## Dataset summary

Project-authored synthetic cases and exact deterministic expected outputs for a closed-file
robot-cell safety-supervisor demonstrator. Inputs model production intent, independent observations,
source health, output uncertainty, authority probes, persistence, and staged recovery.

## Intended use

Offline software regression, exact-byte reproducibility, policy inspection, and safety-manager demo
fixtures. Verify the canonical manifest before use. No network, device, controller, or machine
interface is represented.

`SAFETY_MANAGER_DEMO.md` is the generated field guide. The dependency-free read-only monitor in
`demo/` is generated from all expected-result records and these metrics; it adds no hand-entered
score and exposes no command, reset, rearm, acknowledgment, or stop affordance.

## Limitations

This is synthetic maintainer evidence, not field or application validation. It does not select or
validate real limits, sensors, diagnostics, communications, controllers, final elements, stopping
performance, independence, cybersecurity, or residual risk. Request creation and simulated receipt
do not establish physical stopping. PLr, SIL, total stopping time, diagnostic coverage, application
validation, and unresolved common-cause assumptions remain TBD pending a qualified target-system
assessment.

## License and rights

Apache-2.0 for project-authored records and documentation. No private keys, customer data,
copyrighted standards text, or third-party equipment data are included. The canonical public Dataset
is `Maverick03511/safetyops-bench-v1`; its companion static monitor is
`Maverick03511/oscillink-safety-ops-demo`.
"""


def _field_guide(metrics: dict[str, Any], results: list[dict[str, Any]]) -> str:
    by_id = {str(item["case_id"]): item for item in results}
    recovery = by_id["case:valid-staged-recovery"]["final"]
    priority = by_id["case:simultaneous-priority-faults"]["final"]
    return f"""# Safety manager benchmark field guide

**SYNTHETIC EVIDENCE — SOFTWARE BEHAVIOR ONLY**

This closed-file robot-cell corpus helps a safety manager inspect deterministic supervisor evidence,
not operate equipment. It has no network, controller, machine, reset, rearm, acknowledgment, stop,
or command interface. Every request and receipt is represented synthetic data; physical stop remains `not_established`.

## Verified corpus at a glance

- {metrics["exact_matches"]}/{metrics["total_cases"]} exact byte matches across {metrics["deterministic_repeatability"]["runs_per_case"]} runs per case
- {metrics["fault_family_coverage"]["covered_families"]}/{metrics["fault_family_coverage"]["total_required"]} required fault families represented
- {metrics["deterministic_repeatability"]["total_executions"]} deterministic executions; no wall-clock latency claim
- actions: {", ".join(f"`{key}` {value}" for key, value in metrics["action_outcomes"].items())}

## Inspection sequence

1. Confirm exact `case_id`, title, scenario identity, case hash, configuration hash, authority hash,
   runtime-format hash, and input hashes.
2. Compare production intent with independent occupancy, measured motion, and source health.
3. Read the deterministic policy state and action, then preserve first-out separately from the sorted
   set of all contributing reasons.
4. Keep request state, fixture acknowledgment, and physical stopping distinct. An acknowledgment is
   receipt evidence only. No physical stop is established.
5. Inspect latch, recovery stage, fresh-start requirement, and reset sequence. Displayed recovery
   events are records from a represented independent safety authority, never UI commands.

## High-value cases

- `case:simultaneous-priority-faults`: first-out `{priority["first_out_reason"]}` with sorted reasons
  `{", ".join(priority["reason_codes"])}`.
- `case:false-acknowledgment`: a mismatched receipt does not resolve the output path or prove stop.
- `case:restart-latch-preservation`: process restart preserves the intervention latch.
- `case:production-reset-attempt`: production-AI reset authority is rejected.
- `case:valid-staged-recovery`: ends at `{recovery["recovery_stage"]}`, latched
  `{str(recovery["latched"]).lower()}`, fresh-start required
  `{str(recovery["fresh_start_required"]).lower()}`, reset sequence `{recovery["reset_sequence"]}`.

## What this evidence cannot establish

This synthetic benchmark does not establish a physical stop, safe operation, field effectiveness,
certification, compliance, or target-system integrity. PLr, SIL, total stopping time, diagnostic
coverage, application validation, and common-cause target values remain TBD pending qualified
assessment of an exact machine and installation.
"""


def _sha256(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _source_identities(source_repository: Path) -> dict[str, str]:
    identities = {
        relative: _sha256((source_repository / relative).read_bytes()) for relative in SOURCE_PATHS
    }
    identities["tree"] = _sha256(canonical_json(identities))
    return identities


def _write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def _role(path: str) -> str:
    return {
        "DATASET_CARD.md": "dataset_card",
        "README.md": "documentation",
        "SAFETY_MANAGER_DEMO.md": "safety_manager_field_guide",
        "authority.json": "public_authority",
        "benchmark-case.schema.json": "case_schema",
        "benchmark-result.schema.json": "result_schema",
        "cases.jsonl": "case_input",
        "configuration.json": "configuration",
        "expected-results.jsonl": "expected_output",
        "metrics.json": "derived_metrics",
    }[path]


def generate_benchmark(
    destination: Path, *, source_repository: Path, runtime_baseline_commit: str
) -> dict[str, Any]:
    """Generate all frozen benchmark artifacts from cases and runtime outputs."""

    destination.mkdir(parents=True, exist_ok=True)
    scenario_source = source_repository / "scenarios" / "robot_cell_v1"
    shutil.copyfile(scenario_source / "configuration.json", destination / "configuration.json")
    shutil.copyfile(scenario_source / "authority.json", destination / "authority.json")

    source_identities = _source_identities(source_repository)
    documents = build_case_documents()
    case_lines = [canonical_json(document) for document in documents]
    parsed_cases = [parse_case_line(line) for line in case_lines]
    case_ids = [item.case.case_id for item in parsed_cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("generated benchmark case IDs must be unique")
    _write(destination / "cases.jsonl", b"".join(case_lines))

    executions = [execute_case(item, benchmark_root=destination) for item in parsed_cases]
    repeat_executions = [
        [execute_case(item, benchmark_root=destination).canonical_bytes for item in parsed_cases]
        for _ in range(2)
    ]
    expected_lines = [item.canonical_bytes for item in executions]
    matching_cases = sum(
        all(repeat[index] == expected_lines[index] for repeat in repeat_executions)
        for index in range(len(expected_lines))
    )
    _write(destination / "expected-results.jsonl", b"".join(expected_lines))

    results = [dict(item.result) for item in executions]
    action_outcomes = Counter(str(item["outcome_action"]) for item in results)
    state_outcomes = Counter(str(item["final"]["policy_state"]) for item in results)
    first_out_outcomes = Counter(str(item["final"]["first_out_reason"]) for item in results)
    family_counts = Counter(
        str(family) for document in documents for family in document["fault_families"]
    )
    metrics: dict[str, Any] = {
        "schema_version": 1,
        "metrics_format": "oscillink-robot-cell-benchmark-metrics-v1",
        "benchmark_id": "benchmark:robot-cell-v1",
        "runtime_baseline_commit": runtime_baseline_commit,
        "total_cases": len(documents),
        "expected_results": len(expected_lines),
        "exact_matches": matching_cases,
        "action_outcomes": dict(sorted(action_outcomes.items())),
        "state_outcomes": dict(sorted(state_outcomes.items())),
        "first_out_outcomes": dict(sorted(first_out_outcomes.items())),
        "fault_family_coverage": {
            "required": list(REQUIRED_FAULT_FAMILIES),
            "counts": dict(sorted(family_counts.items())),
            "covered_families": len(family_counts),
            "total_required": len(REQUIRED_FAULT_FAMILIES),
            "complete": set(family_counts) == set(REQUIRED_FAULT_FAMILIES),
        },
        "deterministic_repeatability": {
            "runs_per_case": 3,
            "total_executions": len(documents) * 3,
            "matching_cases": matching_cases,
            "byte_stable": matching_cases == len(documents),
        },
    }
    metrics_raw = canonical_json(metrics)
    _write(destination / "metrics.json", metrics_raw)

    case_schema_raw = canonical_json(BenchmarkCase.model_json_schema(mode="validation"))
    result_schema_raw = canonical_json(BenchmarkResult.model_json_schema(mode="validation"))
    _write(destination / "benchmark-case.schema.json", case_schema_raw)
    _write(destination / "benchmark-result.schema.json", result_schema_raw)
    _write(destination / "README.md", BENCHMARK_README.encode("utf-8"))
    _write(destination / "DATASET_CARD.md", DATASET_CARD.encode("utf-8"))
    _write(destination / "SAFETY_MANAGER_DEMO.md", _field_guide(metrics, results).encode("utf-8"))

    runtime_hashes = {str(item["runtime_format_sha256"]) for item in results}
    configuration_hashes = {str(item["configuration_sha256"]) for item in results}
    authority_hashes = {str(item["configuration_authority_sha256"]) for item in results}
    if len(runtime_hashes) != 1 or len(configuration_hashes) != 1 or len(authority_hashes) != 1:
        raise ValueError("generated benchmark identities are inconsistent")
    paths = sorted(
        path.relative_to(destination).as_posix()
        for path in destination.rglob("*")
        if path.is_file() and path.name != "benchmark-manifest.json"
    )
    files = []
    for relative in paths:
        raw = (destination / relative).read_bytes()
        files.append(
            {
                "path": relative,
                "role": _role(relative),
                "sha256": _sha256(raw),
                "byte_count": len(raw),
            }
        )
    manifest = {
        "schema_version": 1,
        "manifest_format": "oscillink-robot-cell-benchmark-manifest-v1",
        "benchmark_id": "benchmark:robot-cell-v1",
        "scope_id": "SCOPE-ROBOT-CELL-001",
        "runtime_baseline_commit": runtime_baseline_commit,
        "benchmark_source_sha256": source_identities["src/oscillink_safety_ops/benchmark.py"],
        "generator_source_sha256": source_identities["scripts/generate_benchmark.py"],
        "source_tree_sha256": source_identities["tree"],
        "runtime_format_sha256": next(iter(runtime_hashes)),
        "configuration_sha256": next(iter(configuration_hashes)),
        "configuration_authority_sha256": next(iter(authority_hashes)),
        "case_format": "canonical-jsonl-utf8-lf-v1",
        "result_format": "oscillink-robot-cell-benchmark-result-v1",
        "case_schema_sha256": _sha256(case_schema_raw),
        "result_schema_sha256": _sha256(result_schema_raw),
        "scenario_identities": sorted(str(item["scenario_identity"]) for item in results),
        "required_fault_families": list(REQUIRED_FAULT_FAMILIES),
        "declared_totals": {
            "cases": len(documents),
            "expected_results": len(expected_lines),
            "fault_families": len(REQUIRED_FAULT_FAMILIES),
        },
        "files": files,
        "private_keys_included": False,
    }
    _write(destination / "benchmark-manifest.json", canonical_json(manifest))
    return metrics


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    generate_benchmark(
        root / "benchmark" / "robot_cell_v1",
        source_repository=root,
        runtime_baseline_commit=RUNTIME_BASELINE_COMMIT,
    )


if __name__ == "__main__":
    main()
