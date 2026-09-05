"""Strict exact-byte contracts for the synthetic robot-cell benchmark."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath, PureWindowsPath
from types import MappingProxyType
from typing import Annotated, Any, Literal, TypeAlias

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictStr,
    ValidationError,
    field_validator,
)
from pydantic.types import JsonValue

from .runtime import replay as runtime_replay
from .runtime.configuration import BoundConfiguration, load_supervisor_configuration
from .runtime.contracts import (
    ActionAcknowledgment,
    CommandObservation,
    PhysicalObservation,
    RecoveryEvent,
    SourceHealthObservation,
    SupervisorStateRecord,
)
from .runtime.state_machine import (
    RecoveryConditions,
    apply_recovery_event,
    assess_reset_readiness,
    observe_action_acknowledgment,
)
from .runtime.supervisor import (
    SupervisorRuntime,
    canonical_record_bytes,
    evaluate_supervisor,
    start_supervisor,
)

Identifier = Annotated[
    StrictStr,
    Field(min_length=1, max_length=256, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}$"),
]
Sha256 = Annotated[StrictStr, Field(pattern=r"^sha256:[0-9a-f]{64}$")]


class BenchmarkContract(BaseModel):
    """Frozen strict base for benchmark records."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class EvaluationStep(BenchmarkContract):
    """One explicit-time deterministic supervisor evaluation."""

    kind: Literal["evaluate"]
    evaluation_time: AwareDatetime
    observations: Annotated[tuple[dict[str, JsonValue], ...], Field(min_length=1, max_length=64)]
    output_uncertain: StrictBool = False
    candidate_configuration_changed: StrictBool = False


class RestartStep(BenchmarkContract):
    """Synthetic process boundary that round-trips the exact state bytes."""

    kind: Literal["restart"]


class ProductionAuthorityAttemptStep(BenchmarkContract):
    """An untrusted producer probe that cannot alter supervisor state."""

    kind: Literal["production_authority_attempt"]
    attempted_operation: Literal[
        "reset", "administration", "configuration", "output_acknowledgment", "disable", "suppress"
    ]
    actor_domain: Literal["production_ai"]


class AcknowledgmentStep(BenchmarkContract):
    """A represented simulated-fixture acknowledgment observation."""

    kind: Literal["acknowledgment"]
    evaluation_time: AwareDatetime
    observed_at: AwareDatetime
    status: Literal["received_by_simulated_fixture", "rejected_by_simulated_fixture", "unknown"]
    identity_mode: Literal["matching", "mismatched"]


class RecoveryConditionsContract(BenchmarkContract):
    """Five explicit represented recovery prerequisites."""

    occupancy_clear: StrictBool
    motion_stopped: StrictBool
    sources_healthy: StrictBool
    configuration_unchanged: StrictBool
    output_resolved: StrictBool

    def runtime_value(self) -> RecoveryConditions:
        return RecoveryConditions(**self.model_dump())


class AssessResetStep(BenchmarkContract):
    """Assess readiness without granting or applying reset authority."""

    kind: Literal["assess_reset"]
    evaluation_time: AwareDatetime
    conditions: RecoveryConditionsContract


class RecoveryEventStep(BenchmarkContract):
    """A represented event from the separate independent safety authority."""

    kind: Literal["recovery_event"]
    event_kind: Literal["reset", "rearm", "recovery_confirmed", "fresh_start"]
    evaluation_time: AwareDatetime
    observed_at: AwareDatetime
    conditions: RecoveryConditionsContract = RecoveryConditionsContract(
        occupancy_clear=True,
        motion_stopped=True,
        sources_healthy=True,
        configuration_unchanged=True,
        output_resolved=True,
    )


BenchmarkStep: TypeAlias = Annotated[
    EvaluationStep
    | RestartStep
    | ProductionAuthorityAttemptStep
    | AcknowledgmentStep
    | AssessResetStep
    | RecoveryEventStep,
    Field(discriminator="kind"),
]


class BenchmarkCase(BenchmarkContract):
    """One synthetic closed-input benchmark case."""

    schema_version: Literal[1]
    case_id: Identifier
    title: Annotated[StrictStr, Field(min_length=1, max_length=200)]
    fault_families: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=32)]
    run_id: Identifier
    start_at: AwareDatetime
    steps: Annotated[tuple[BenchmarkStep, ...], Field(min_length=1, max_length=32)]
    synthetic_evidence: Literal[True]
    operational_authority: Literal["none"]

    @field_validator("fault_families")
    @classmethod
    def require_sorted_unique_families(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if value != tuple(sorted(set(value))):
            raise ValueError("fault_families must be sorted and unique")
        return value


class EvaluationTimeline(BenchmarkContract):
    step: int
    kind: Literal["evaluation"]
    evaluated_at: StrictStr
    action: Literal["none", "advisory_warning", "inhibit_request", "protective_stop_request"]
    decision_state: StrictStr
    latched_state: StrictStr
    first_out_reason: Identifier
    reason_codes: tuple[Identifier, ...]
    input_sha256: tuple[Sha256, ...]
    request_state: StrictStr
    acknowledgment_state: StrictStr
    physical_stop: Literal["not_established"]
    common_cause_integrity: Literal["represented_healthy_unvalidated", "unresolved"]
    independence_established: Literal[False]


class RestartTimeline(BenchmarkContract):
    step: int
    kind: Literal["restart"]
    state_sha256: Sha256
    latched_before: StrictBool
    latched_after: StrictBool
    latched_preserved: StrictBool
    physical_stop: Literal["not_established"]


class ProductionAttemptTimeline(BenchmarkContract):
    step: int
    kind: Literal["production_authority_attempt"]
    actor_domain: Literal["production_ai"]
    attempted_operation: StrictStr
    disposition: Literal["rejected_no_authority"]
    state_unchanged: Literal[True]
    physical_stop: Literal["not_established"]


class AcknowledgmentTimeline(BenchmarkContract):
    step: int
    kind: Literal["acknowledgment"]
    status: StrictStr
    identity_mode: Literal["matching", "mismatched"]
    acknowledgment_state: StrictStr
    latched_state: StrictStr
    reason_codes: tuple[Identifier, ...]
    request_state: StrictStr
    physical_stop: Literal["not_established"]


class AssessResetTimeline(BenchmarkContract):
    step: int
    kind: Literal["assess_reset"]
    recovery_stage: StrictStr
    latched: StrictBool
    reason_codes: tuple[Identifier, ...]
    physical_stop: Literal["not_established"]


class RecoveryTimeline(BenchmarkContract):
    step: int
    kind: Literal["recovery_event"]
    event_kind: StrictStr
    actor_domain: Literal["independent_safety_authority"]
    recovery_stage: StrictStr
    latched: StrictBool
    fresh_start_required: StrictBool
    reset_sequence: int
    reason_codes: tuple[Identifier, ...]
    physical_stop: Literal["not_established"]


ResultTimeline: TypeAlias = Annotated[
    EvaluationTimeline
    | RestartTimeline
    | ProductionAttemptTimeline
    | AcknowledgmentTimeline
    | AssessResetTimeline
    | RecoveryTimeline,
    Field(discriminator="kind"),
]


class ProductionIntentResult(BenchmarkContract):
    command_kind: StrictStr
    motion_requested: StrictBool


class MotionResult(BenchmarkContract):
    commanded: StrictBool
    measured: StrictBool
    speed_mps: float | None
    acceleration_mps2: float | None


class SourceHealthResult(BenchmarkContract):
    source_state: StrictStr
    clock_state: StrictStr


class FinalResult(BenchmarkContract):
    production_intent: ProductionIntentResult
    occupancy: tuple[StrictStr, ...]
    motion: MotionResult
    source_health: SourceHealthResult
    policy_state: StrictStr
    first_out_reason: Identifier
    reason_codes: tuple[Identifier, ...]
    request_state: StrictStr
    acknowledgment_state: StrictStr
    physical_stop: Literal["not_established"]
    common_cause_integrity: StrictStr
    independence_established: Literal[False]
    certification_state: Literal["not_established"]
    latched: StrictBool
    recovery_stage: StrictStr
    fresh_start_required: StrictBool
    reset_sequence: int
    input_sha256: tuple[Sha256, ...]


class BenchmarkResult(BenchmarkContract):
    """Strict exact expected-output contract for one benchmark case."""

    schema_version: Literal[1]
    result_format: Literal["oscillink-robot-cell-benchmark-result-v1"]
    case_id: Identifier
    title: StrictStr
    case_sha256: Sha256
    scenario_identity: Identifier
    runtime_format_sha256: Sha256
    configuration_sha256: Sha256
    configuration_authority_sha256: Sha256
    synthetic_evidence: Literal[True]
    operational_authority: Literal["none"]
    outcome_action: Literal[
        "none", "advisory_warning", "inhibit_request", "protective_stop_request"
    ]
    fault_families: tuple[Identifier, ...]
    production_authority_attempts: tuple[StrictStr, ...]
    timeline: tuple[ResultTimeline, ...]
    final: FinalResult


@dataclass(frozen=True, slots=True)
class ParsedCase:
    """A validated case bound to the exact canonical JSONL line."""

    case: BenchmarkCase
    sha256: str
    byte_count: int
    raw: bytes


@dataclass(frozen=True, slots=True)
class BenchmarkExecution:
    """Canonical exact result bytes and immutable parsed result."""

    canonical_bytes: bytes
    result: MappingProxyType[str, Any]


def canonical_json(value: object) -> bytes:
    """Return canonical UTF-8 compact JSON plus one LF."""

    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _duplicate_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_case_line(raw: bytes) -> ParsedCase:
    """Validate one canonical JSONL case and retain its exact-byte identity."""

    if type(raw) is not bytes or not raw:
        raise ValueError("case line must be nonempty exact bytes")
    try:
        text = raw.decode("utf-8", errors="strict")
        document: Any = json.loads(text, object_pairs_hook=_duplicate_object)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError("case line is malformed UTF-8 JSON") from error
    if canonical_json(document) != raw:
        raise ValueError("case line must be canonical UTF-8 JSON plus LF")
    case = BenchmarkCase.model_validate_json(raw)
    return ParsedCase(
        case=case,
        sha256="sha256:" + hashlib.sha256(raw).hexdigest(),
        byte_count=len(raw),
        raw=raw,
    )


_ACTION_RANK = {
    "none": 0,
    "advisory_warning": 1,
    "inhibit_request": 2,
    "protective_stop_request": 3,
}


def _bound_configuration(
    root: Path, *, evaluation_time: datetime
) -> tuple[BoundConfiguration, str]:
    resolved = root.resolve()
    authority_capture = runtime_replay._capture_regular_file(
        resolved,
        Path("authority.json"),
        maximum=runtime_replay.DEFAULT_MAX_AUTHORITY_BYTES,
    )
    authority = runtime_replay._load_authority(authority_capture, root=resolved)
    bound = load_supervisor_configuration(
        Path("configuration.json"), authority=authority, evaluation_time=evaluation_time
    )
    return bound, authority_capture.sha256


def _changed_candidate(configuration: BoundConfiguration) -> BoundConfiguration:
    raw = canonical_json({"synthetic_detected_candidate": "changed"})
    return BoundConfiguration(
        configuration=configuration.configuration,
        exact_bytes=raw,
        configuration_sha256="sha256:" + hashlib.sha256(raw).hexdigest(),
    )


def execute_case(parsed: ParsedCase, *, benchmark_root: Path) -> BenchmarkExecution:
    """Execute one validated synthetic case using explicit inputs only."""

    if not isinstance(parsed, ParsedCase) or not isinstance(benchmark_root, Path):
        raise TypeError("execute_case requires a ParsedCase and Path benchmark_root")
    case = parsed.case
    configuration, authority_sha256 = _bound_configuration(
        benchmark_root, evaluation_time=case.start_at
    )
    runtime = start_supervisor(
        run_id=case.run_id,
        configuration=configuration,
        evaluation_time=case.start_at,
        startup_input_sha256=(configuration.configuration_sha256,),
    )
    timeline: list[dict[str, Any]] = []
    strongest_action = "none"
    production_intent: dict[str, Any] = {"command_kind": "not_observed", "motion_requested": False}
    latest_occupancy: tuple[str, ...] = ()
    latest_motion: dict[str, Any] = {
        "commanded": False,
        "measured": False,
        "speed_mps": None,
        "acceleration_mps2": None,
    }
    latest_health: dict[str, Any] = {
        "source_state": "not_observed",
        "clock_state": "not_observed",
    }
    acknowledgment_state = "not_observed"
    request_state = "not_requested"
    common_cause_integrity = "common_cause_unassessed"
    independence_established = False
    production_attempts: list[str] = []
    for index, step in enumerate(case.steps):
        if isinstance(step, RestartStep):
            state_raw = canonical_record_bytes(runtime.state)
            loaded = SupervisorStateRecord.model_validate_json(state_raw)
            before = runtime.state.latched
            runtime = SupervisorRuntime(configuration, runtime.freshness, loaded)
            timeline.append(
                {
                    "step": index,
                    "kind": "restart",
                    "state_sha256": "sha256:" + hashlib.sha256(state_raw).hexdigest(),
                    "latched_before": before,
                    "latched_after": runtime.state.latched,
                    "latched_preserved": before == runtime.state.latched,
                    "physical_stop": "not_established",
                }
            )
            continue
        if isinstance(step, ProductionAuthorityAttemptStep):
            production_attempts.append(step.attempted_operation)
            timeline.append(
                {
                    "step": index,
                    "kind": "production_authority_attempt",
                    "actor_domain": step.actor_domain,
                    "attempted_operation": step.attempted_operation,
                    "disposition": "rejected_no_authority",
                    "state_unchanged": True,
                    "physical_stop": "not_established",
                }
            )
            continue
        if isinstance(step, AcknowledgmentStep):
            active_request = runtime.state.active_request_sha256
            if active_request is None:
                raise ValueError("acknowledgment step requires an active request")
            step_raw = canonical_json(step.model_dump(mode="json"))
            step_hash = "sha256:" + hashlib.sha256(step_raw).hexdigest()
            acknowledgment = ActionAcknowledgment(
                acknowledgment_id=f"ack:{index}",
                run_id=case.run_id,
                observed_at=step.observed_at,
                request_sha256=(
                    active_request if step.identity_mode == "matching" else "sha256:" + "e" * 64
                ),
                configuration_sha256=configuration.configuration_sha256,
                input_sha256=(step_hash,),
                source_domain="simulated_fixture",
                status=step.status,
            )
            transition = observe_action_acknowledgment(
                runtime.state, acknowledgment, evaluation_time=step.evaluation_time
            )
            runtime = SupervisorRuntime(configuration, runtime.freshness, transition.state)
            valid = transition.state.supervisor_state == "stopped_unverified"
            acknowledgment_state = (
                "receipt_observed_stopping_unverified" if valid else "false_or_unresolved"
            )
            request_state = transition.state.output_state
            timeline.append(
                {
                    "step": index,
                    "kind": "acknowledgment",
                    "status": step.status,
                    "identity_mode": step.identity_mode,
                    "acknowledgment_state": acknowledgment_state,
                    "latched_state": transition.state.supervisor_state,
                    "reason_codes": list(transition.state.reason_codes),
                    "request_state": request_state,
                    "physical_stop": "not_established",
                }
            )
            continue
        if isinstance(step, AssessResetStep):
            transition = assess_reset_readiness(
                runtime.state,
                conditions=step.conditions.runtime_value(),
                evaluation_time=step.evaluation_time,
            )
            runtime = SupervisorRuntime(configuration, runtime.freshness, transition.state)
            timeline.append(
                {
                    "step": index,
                    "kind": "assess_reset",
                    "recovery_stage": transition.state.supervisor_state,
                    "latched": transition.state.latched,
                    "reason_codes": list(transition.state.reason_codes),
                    "physical_stop": "not_established",
                }
            )
            continue
        if isinstance(step, RecoveryEventStep):
            step_raw = canonical_json(step.model_dump(mode="json"))
            event = RecoveryEvent(
                event_id=f"recovery:{index}:{step.event_kind}",
                run_id=case.run_id,
                observed_at=step.observed_at,
                event_kind=step.event_kind,
                actor_domain="independent_safety_authority",
                authorization_state="externally_authorized",
                configuration_sha256=configuration.configuration_sha256,
                input_sha256="sha256:" + hashlib.sha256(step_raw).hexdigest(),
            )
            transition = apply_recovery_event(
                runtime.state,
                event,
                conditions=step.conditions.runtime_value(),
                evaluation_time=step.evaluation_time,
            )
            runtime = SupervisorRuntime(configuration, runtime.freshness, transition.state)
            request_state = transition.state.output_state
            timeline.append(
                {
                    "step": index,
                    "kind": "recovery_event",
                    "event_kind": step.event_kind,
                    "actor_domain": "independent_safety_authority",
                    "recovery_stage": transition.state.supervisor_state,
                    "latched": transition.state.latched,
                    "fresh_start_required": transition.state.fresh_start_required,
                    "reset_sequence": transition.state.reset_sequence,
                    "reason_codes": list(transition.state.reason_codes),
                    "physical_stop": "not_established",
                }
            )
            continue
        if not isinstance(step, EvaluationStep):
            raise TypeError("unsupported benchmark step")
        observation_raw = b"".join(canonical_json(item) for item in step.observations)
        observations = runtime_replay.parse_observation_jsonl(observation_raw)
        commands = [item for item in observations if isinstance(item, CommandObservation)]
        physical = [item for item in observations if isinstance(item, PhysicalObservation)]
        health = [item for item in observations if isinstance(item, SourceHealthObservation)]
        if commands:
            production_intent = {
                "command_kind": commands[-1].command_kind,
                "motion_requested": commands[-1].motion_requested,
            }
        if health:
            latest_health = {
                "source_state": health[-1].source_state,
                "clock_state": health[-1].clock_state,
            }
        candidate = (
            _changed_candidate(configuration) if step.candidate_configuration_changed else None
        )
        evaluation = evaluate_supervisor(
            observations,
            evaluation_time=step.evaluation_time,
            runtime=runtime,
            candidate_configuration=candidate,
            output_uncertain=step.output_uncertain,
        )
        runtime = evaluation.state
        common_cause_integrity = evaluation.common_cause.integrity_state
        independence_established = evaluation.common_cause.independence_established
        latest_occupancy = evaluation.correlation.occupancy_states
        latest_motion = {
            "commanded": evaluation.correlation.commanded_motion,
            "measured": evaluation.correlation.measured_motion,
            "speed_mps": physical[-1].speed_mps if physical else None,
            "acceleration_mps2": physical[-1].acceleration_mps2 if physical else None,
        }
        action = evaluation.decision.action
        if _ACTION_RANK[action] > _ACTION_RANK[strongest_action]:
            strongest_action = action
        if evaluation.action_request is not None:
            request_state = "request_pending"
        timeline.append(
            {
                "step": index,
                "kind": "evaluation",
                "evaluated_at": step.evaluation_time.isoformat(),
                "action": action,
                "decision_state": evaluation.decision.supervisor_state,
                "latched_state": runtime.state.supervisor_state,
                "first_out_reason": evaluation.decision.first_out_reason,
                "reason_codes": list(evaluation.decision.reason_codes),
                "input_sha256": list(evaluation.decision.input_sha256),
                "request_state": request_state,
                "acknowledgment_state": acknowledgment_state,
                "physical_stop": "not_established",
                "common_cause_integrity": evaluation.common_cause.integrity_state,
                "independence_established": evaluation.common_cause.independence_established,
            }
        )
    final_state = runtime.state
    result: dict[str, Any] = {
        "schema_version": 1,
        "result_format": "oscillink-robot-cell-benchmark-result-v1",
        "case_id": case.case_id,
        "title": case.title,
        "case_sha256": parsed.sha256,
        "scenario_identity": "scenario:" + hashlib.sha256(parsed.raw).hexdigest(),
        "runtime_format_sha256": runtime_replay.runtime_format_identity().sha256,
        "configuration_sha256": configuration.configuration_sha256,
        "configuration_authority_sha256": authority_sha256,
        "synthetic_evidence": True,
        "operational_authority": "none",
        "outcome_action": strongest_action,
        "fault_families": list(case.fault_families),
        "production_authority_attempts": production_attempts,
        "timeline": timeline,
        "final": {
            "production_intent": production_intent,
            "occupancy": list(latest_occupancy),
            "motion": latest_motion,
            "source_health": latest_health,
            "policy_state": final_state.supervisor_state,
            "first_out_reason": final_state.first_out_reason,
            "reason_codes": list(final_state.reason_codes),
            "request_state": request_state,
            "acknowledgment_state": acknowledgment_state,
            "physical_stop": "not_established",
            "common_cause_integrity": common_cause_integrity,
            "independence_established": independence_established,
            "certification_state": "not_established",
            "latched": final_state.latched,
            "recovery_stage": final_state.supervisor_state,
            "fresh_start_required": final_state.fresh_start_required,
            "reset_sequence": final_state.reset_sequence,
            "input_sha256": list(final_state.input_sha256),
        },
    }
    raw = canonical_json(result)
    validated = BenchmarkResult.model_validate_json(raw)
    raw = canonical_json(validated.model_dump(mode="json"))
    return BenchmarkExecution(raw, MappingProxyType(json.loads(raw)))


REQUIRED_BENCHMARK_FILES = {
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
}
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
REQUIRED_CASE_IDS = (
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
)
MAX_BENCHMARK_FILE_BYTES = 4 * 1024 * 1024


class BenchmarkVerificationError(ValueError):
    """Stable fail-closed benchmark verification failure."""

    def __init__(self, code: str, message: str | None = None) -> None:
        self.code = code
        super().__init__(message or code)


@dataclass(frozen=True, slots=True)
class BenchmarkVerification:
    """Mechanically verified benchmark totals without timing claims."""

    total_cases: int
    exact_matches: int
    fault_families: int
    repeat_runs: int
    network_accessed: Literal[False] = False


def _read_regular(root: Path, relative: str) -> bytes:
    pure = PurePosixPath(relative)
    if (
        not relative
        or pure.is_absolute()
        or pure.anchor
        or PureWindowsPath(relative).drive
        or ".." in pure.parts
        or "\\" in relative
    ):
        raise BenchmarkVerificationError("path_escape", f"path escapes benchmark root: {relative}")
    cursor = root
    metadata: os.stat_result | None = None
    try:
        for part in pure.parts:
            cursor /= part
            metadata = cursor.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                raise BenchmarkVerificationError("symlink", f"symlink is forbidden: {relative}")
    except BenchmarkVerificationError:
        raise
    except FileNotFoundError as error:
        raise BenchmarkVerificationError("missing_file", f"missing file: {relative}") from error
    except OSError as error:
        raise BenchmarkVerificationError(
            "metadata_unavailable", f"metadata unavailable: {relative}"
        ) from error
    if metadata is None or not stat.S_ISREG(metadata.st_mode):
        raise BenchmarkVerificationError("special_file", f"not a regular file: {relative}")
    if metadata.st_size > MAX_BENCHMARK_FILE_BYTES:
        raise BenchmarkVerificationError(
            "file_too_large", f"file exceeds maximum byte count: {relative}"
        )
    try:
        with cursor.open("rb") as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode):
                raise BenchmarkVerificationError("special_file", f"not regular: {relative}")
            if (metadata.st_dev, metadata.st_ino) != (opened.st_dev, opened.st_ino):
                raise BenchmarkVerificationError(
                    "substitution", f"file changed opening: {relative}"
                )
            if opened.st_size != metadata.st_size:
                raise BenchmarkVerificationError(
                    "substitution", f"file size changed opening: {relative}"
                )
            return stream.read()
    except BenchmarkVerificationError:
        raise
    except OSError as error:
        raise BenchmarkVerificationError("read_failed", f"cannot read: {relative}") from error


def _strict_document(raw: bytes, *, kind: str) -> dict[str, Any]:
    try:
        text = raw.decode("utf-8", errors="strict")
        value = json.loads(text, object_pairs_hook=_duplicate_object)
    except UnicodeDecodeError as error:
        raise BenchmarkVerificationError("invalid_utf8", f"{kind} is not UTF-8") from error
    except (json.JSONDecodeError, RecursionError, ValueError) as error:
        raise BenchmarkVerificationError("malformed_json", f"{kind} is malformed JSON") from error
    if type(value) is not dict:
        raise BenchmarkVerificationError("invalid_shape", f"{kind} must be an object")
    if canonical_json(value) != raw:
        raise BenchmarkVerificationError("noncanonical_json", f"{kind} is not canonical JSON")
    return value


def _jsonl_lines(raw: bytes, *, kind: str) -> list[bytes]:
    if not raw or not raw.endswith(b"\n") or b"\r" in raw:
        raise BenchmarkVerificationError("malformed_jsonl", f"{kind} must use LF-terminated JSONL")
    lines = raw.splitlines(keepends=True)
    if any(line == b"\n" for line in lines):
        raise BenchmarkVerificationError("malformed_jsonl", f"{kind} contains a blank line")
    return lines


def _actual_paths(root: Path) -> set[str]:
    paths: set[str] = set()
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        try:
            metadata = path.lstat()
        except OSError as error:
            raise BenchmarkVerificationError(
                "metadata_unavailable", f"metadata unavailable: {relative}"
            ) from error
        if stat.S_ISDIR(metadata.st_mode):
            if stat.S_ISLNK(metadata.st_mode):
                raise BenchmarkVerificationError("symlink", f"symlink is forbidden: {relative}")
            continue
        if stat.S_ISLNK(metadata.st_mode):
            raise BenchmarkVerificationError("symlink", f"symlink is forbidden: {relative}")
        if not stat.S_ISREG(metadata.st_mode):
            raise BenchmarkVerificationError("special_file", f"not a regular file: {relative}")
        paths.add(relative)
    return paths


def _derived_metrics(
    cases: list[ParsedCase],
    expected: list[BenchmarkResult],
    *,
    runtime_baseline_commit: str,
    exact_matches: int,
    matching_cases: int,
) -> dict[str, Any]:
    action_outcomes = Counter(item.outcome_action for item in expected)
    state_outcomes = Counter(item.final.policy_state for item in expected)
    first_out_outcomes = Counter(item.final.first_out_reason for item in expected)
    family_counts = Counter(family for item in cases for family in item.case.fault_families)
    return {
        "schema_version": 1,
        "metrics_format": "oscillink-robot-cell-benchmark-metrics-v1",
        "benchmark_id": "benchmark:robot-cell-v1",
        "runtime_baseline_commit": runtime_baseline_commit,
        "total_cases": len(cases),
        "expected_results": len(expected),
        "exact_matches": exact_matches,
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
            "total_executions": len(cases) * 3,
            "matching_cases": matching_cases,
            "byte_stable": matching_cases == len(cases),
        },
    }


def verify_benchmark(
    benchmark_root: Path, *, repository_root: Path | None = None
) -> BenchmarkVerification:
    """Verify the frozen benchmark completely using local files and explicit state only."""

    if not isinstance(benchmark_root, Path):
        raise BenchmarkVerificationError("invalid_root", "benchmark root must be a Path")
    try:
        root_metadata = benchmark_root.lstat()
    except OSError as error:
        raise BenchmarkVerificationError("invalid_root", "benchmark root is unavailable") from error
    if stat.S_ISLNK(root_metadata.st_mode) or not stat.S_ISDIR(root_metadata.st_mode):
        raise BenchmarkVerificationError("invalid_root", "benchmark root must be a real directory")
    root = benchmark_root.resolve()
    repository = (repository_root or Path.cwd()).resolve()

    manifest_raw = _read_regular(root, "benchmark-manifest.json")
    manifest = _strict_document(manifest_raw, kind="manifest")
    expected_manifest_fields = {
        "schema_version",
        "manifest_format",
        "benchmark_id",
        "scope_id",
        "runtime_baseline_commit",
        "benchmark_source_sha256",
        "generator_source_sha256",
        "source_tree_sha256",
        "runtime_format_sha256",
        "configuration_sha256",
        "configuration_authority_sha256",
        "case_format",
        "result_format",
        "case_schema_sha256",
        "result_schema_sha256",
        "scenario_identities",
        "required_fault_families",
        "declared_totals",
        "files",
        "private_keys_included",
    }
    if set(manifest) != expected_manifest_fields:
        raise BenchmarkVerificationError("manifest_contract", "manifest fields are invalid")
    if (
        type(manifest["schema_version"]) is not int
        or manifest["schema_version"] != 1
        or manifest["manifest_format"] != "oscillink-robot-cell-benchmark-manifest-v1"
        or manifest["benchmark_id"] != "benchmark:robot-cell-v1"
        or manifest["scope_id"] != "SCOPE-ROBOT-CELL-001"
        or manifest["case_format"] != "canonical-jsonl-utf8-lf-v1"
        or manifest["result_format"] != "oscillink-robot-cell-benchmark-result-v1"
        or manifest["private_keys_included"] is not False
    ):
        raise BenchmarkVerificationError("manifest_identity", "manifest identity is invalid")
    if manifest["required_fault_families"] != list(REQUIRED_FAULT_FAMILIES):
        raise BenchmarkVerificationError("fault_family_coverage", "required fault families drifted")

    entries = manifest["files"]
    if type(entries) is not list:
        raise BenchmarkVerificationError("manifest_contract", "manifest files must be an array")
    listed: dict[str, dict[str, Any]] = {}
    ordered_paths: list[str] = []
    captured: dict[str, bytes] = {}
    for entry in entries:
        if type(entry) is not dict or set(entry) != {"path", "role", "sha256", "byte_count"}:
            raise BenchmarkVerificationError("manifest_contract", "manifest entry is invalid")
        relative = entry["path"]
        if type(relative) is not str:
            raise BenchmarkVerificationError("manifest_contract", "manifest path is invalid")
        if relative in listed:
            raise BenchmarkVerificationError("duplicate", f"duplicate manifest path: {relative}")
        ordered_paths.append(relative)
        listed[relative] = entry
        if (
            relative not in REQUIRED_BENCHMARK_FILES
            or entry["role"] != REQUIRED_BENCHMARK_FILES[relative]
        ):
            raise BenchmarkVerificationError(
                "manifest_contract", f"unexpected manifest path: {relative}"
            )
        byte_count = entry["byte_count"]
        digest = entry["sha256"]
        if type(byte_count) is not int or byte_count < 1:
            raise BenchmarkVerificationError("byte_count", f"invalid byte count: {relative}")
        if (
            type(digest) is not str
            or len(digest) != 71
            or not digest.startswith("sha256:")
            or any(character not in "0123456789abcdef" for character in digest[7:])
        ):
            raise BenchmarkVerificationError("hash", f"invalid SHA-256: {relative}")
        raw = _read_regular(root, relative)
        captured[relative] = raw
        if len(raw) != byte_count:
            raise BenchmarkVerificationError("byte_count", f"byte count mismatch: {relative}")
        if "sha256:" + hashlib.sha256(raw).hexdigest() != digest:
            raise BenchmarkVerificationError("hash", f"SHA-256 mismatch: {relative}")
    if ordered_paths != sorted(ordered_paths):
        raise BenchmarkVerificationError("manifest_contract", "manifest paths are not sorted")
    if set(listed) != set(REQUIRED_BENCHMARK_FILES):
        raise BenchmarkVerificationError("manifest_contract", "manifest file set is incomplete")
    actual = _actual_paths(root)
    required_actual = {*REQUIRED_BENCHMARK_FILES, "benchmark-manifest.json"}
    if actual != required_actual:
        raise BenchmarkVerificationError(
            "unmanifested_file", f"benchmark file set differs: {sorted(actual ^ required_actual)}"
        )
    secret_markers = (b"BEGIN PRIVATE KEY", b"ed25519-private:", b'"private_key"')
    if any(marker in raw for raw in captured.values() for marker in secret_markers):
        raise BenchmarkVerificationError("private_key", "private-key material is forbidden")

    runtime_baseline_commit = manifest["runtime_baseline_commit"]
    if (
        type(runtime_baseline_commit) is not str
        or runtime_baseline_commit != "d0ce7509c907edd8d6f1ce385bcd0d2ccd87f35c"
    ):
        raise BenchmarkVerificationError("source_drift", "runtime baseline commit identity drifted")
    benchmark_source = _read_regular(repository, "src/oscillink_safety_ops/benchmark.py")
    generator_source = _read_regular(repository, "scripts/generate_benchmark.py")
    benchmark_source_sha256 = "sha256:" + hashlib.sha256(benchmark_source).hexdigest()
    generator_source_sha256 = "sha256:" + hashlib.sha256(generator_source).hexdigest()
    if manifest["benchmark_source_sha256"] != benchmark_source_sha256:
        raise BenchmarkVerificationError("source_drift", "benchmark source identity drifted")
    if manifest["generator_source_sha256"] != generator_source_sha256:
        raise BenchmarkVerificationError("source_drift", "generator source identity drifted")
    source_tree = canonical_json(
        {
            "scripts/generate_benchmark.py": generator_source_sha256,
            "src/oscillink_safety_ops/benchmark.py": benchmark_source_sha256,
        }
    )
    if manifest["source_tree_sha256"] != "sha256:" + hashlib.sha256(source_tree).hexdigest():
        raise BenchmarkVerificationError("source_drift", "source tree identity drifted")
    runtime_identity = runtime_replay.runtime_format_identity()
    if manifest["runtime_format_sha256"] != runtime_identity.sha256:
        raise BenchmarkVerificationError("source_drift", "runtime format identity drifted")
    if (
        manifest["configuration_sha256"]
        != "sha256:" + hashlib.sha256(captured["configuration.json"]).hexdigest()
    ):
        raise BenchmarkVerificationError("identity_mismatch", "configuration identity mismatch")
    if (
        manifest["configuration_authority_sha256"]
        != "sha256:" + hashlib.sha256(captured["authority.json"]).hexdigest()
    ):
        raise BenchmarkVerificationError("identity_mismatch", "authority identity mismatch")

    current_case_schema = canonical_json(BenchmarkCase.model_json_schema(mode="validation"))
    current_result_schema = canonical_json(BenchmarkResult.model_json_schema(mode="validation"))
    if captured["benchmark-case.schema.json"] != current_case_schema:
        raise BenchmarkVerificationError("schema_drift", "case schema drifted")
    if captured["benchmark-result.schema.json"] != current_result_schema:
        raise BenchmarkVerificationError("schema_drift", "result schema drifted")
    if (
        manifest["case_schema_sha256"]
        != "sha256:" + hashlib.sha256(current_case_schema).hexdigest()
    ):
        raise BenchmarkVerificationError("identity_mismatch", "case schema identity mismatch")
    if (
        manifest["result_schema_sha256"]
        != "sha256:" + hashlib.sha256(current_result_schema).hexdigest()
    ):
        raise BenchmarkVerificationError("identity_mismatch", "result schema identity mismatch")

    case_lines = _jsonl_lines(captured["cases.jsonl"], kind="cases")
    try:
        cases = [parse_case_line(line) for line in case_lines]
    except (TypeError, ValueError, ValidationError) as error:
        raise BenchmarkVerificationError("invalid_case", "case record is invalid") from error
    case_ids = [item.case.case_id for item in cases]
    if len(cases) != len(REQUIRED_CASE_IDS):
        raise BenchmarkVerificationError("case_count", "benchmark requires exactly 36 cases")
    if len(case_ids) != len(set(case_ids)):
        raise BenchmarkVerificationError("duplicate", "benchmark contains duplicate case IDs")
    if tuple(case_ids) != REQUIRED_CASE_IDS:
        raise BenchmarkVerificationError("case_identity", "benchmark case identities drifted")

    result_lines = _jsonl_lines(captured["expected-results.jsonl"], kind="expected results")
    expected: list[BenchmarkResult] = []
    try:
        for line in result_lines:
            document = _strict_document(line, kind="expected result")
            result = BenchmarkResult.model_validate_json(line)
            if canonical_json(document) != line:
                raise ValueError("noncanonical result")
            if list(result.reason_codes if hasattr(result, "reason_codes") else []) != []:
                raise ValueError("unexpected result shape")
            expected.append(result)
    except (TypeError, ValueError, ValidationError) as error:
        raise BenchmarkVerificationError("invalid_result", "expected result is invalid") from error
    result_ids = [item.case_id for item in expected]
    if len(result_ids) != len(set(result_ids)):
        raise BenchmarkVerificationError("duplicate", "expected results contain duplicate case IDs")
    if result_ids != case_ids:
        raise BenchmarkVerificationError(
            "case_result_alignment", "case/result identities do not align"
        )
    for item in expected:
        if item.final.reason_codes != tuple(sorted(set(item.final.reason_codes))):
            raise BenchmarkVerificationError(
                "invalid_result", "result reasons are not sorted unique"
            )
        if item.final.first_out_reason not in item.final.reason_codes:
            raise BenchmarkVerificationError("invalid_result", "first-out is not contributing")

    executions = [execute_case(item, benchmark_root=root) for item in cases]
    actual_lines = [item.canonical_bytes for item in executions]
    exact_matches = sum(
        actual_line == expected_line
        for actual_line, expected_line in zip(actual_lines, result_lines, strict=True)
    )
    if exact_matches != len(cases):
        raise BenchmarkVerificationError(
            "exact_output_mismatch", "actual output differs byte-for-byte"
        )
    repeats = [
        [execute_case(item, benchmark_root=root).canonical_bytes for item in cases]
        for _ in range(2)
    ]
    matching_cases = sum(
        all(repeat[index] == actual_lines[index] for repeat in repeats)
        for index in range(len(cases))
    )
    if matching_cases != len(cases):
        raise BenchmarkVerificationError("repeatability", "case output is not byte-repeatable")

    families = {family for item in cases for family in item.case.fault_families}
    if families != set(REQUIRED_FAULT_FAMILIES):
        raise BenchmarkVerificationError(
            "fault_family_coverage", "fault-family coverage is incomplete"
        )
    scenarios = sorted(item.scenario_identity for item in expected)
    if manifest["scenario_identities"] != scenarios:
        raise BenchmarkVerificationError("identity_mismatch", "scenario identities do not match")
    declared = manifest["declared_totals"]
    expected_totals = {
        "cases": len(cases),
        "expected_results": len(expected),
        "fault_families": len(families),
    }
    if declared != expected_totals:
        raise BenchmarkVerificationError("wrong_totals", "manifest totals do not match records")

    metrics = _derived_metrics(
        cases,
        expected,
        runtime_baseline_commit=runtime_baseline_commit,
        exact_matches=exact_matches,
        matching_cases=matching_cases,
    )
    if captured["metrics.json"] != canonical_json(metrics):
        raise BenchmarkVerificationError("wrong_totals", "declared metrics do not match records")
    return BenchmarkVerification(
        total_cases=len(cases),
        exact_matches=exact_matches,
        fault_families=len(families),
        repeat_runs=3,
    )
