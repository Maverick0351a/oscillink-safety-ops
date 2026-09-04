"""Pure orchestration for correlation, freshness, policy, and latched state."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from .configuration import BoundConfiguration
from .contracts import (
    ActionRequest,
    CommandObservation,
    PhysicalObservation,
    SupervisorDecision,
    SupervisorStateRecord,
)
from .correlator import CorrelationResult, correlate_command_and_state
from .freshness import EvaluationState, FreshnessError, Observation, evaluate_freshness_and_order
from .policy import PolicyEvaluation, evaluate_policy
from .state_machine import (
    apply_policy_evaluation,
    initial_supervisor_state,
    record_action_request,
    record_command_attribution_history,
)


@dataclass(frozen=True, slots=True)
class SupervisorRuntime:
    """All explicit immutable state required by one deterministic evaluation."""

    configuration: BoundConfiguration
    freshness: EvaluationState
    state: SupervisorStateRecord

    def __post_init__(self) -> None:
        if self.state.configuration_sha256 != self.configuration.configuration_sha256:
            raise ValueError("runtime configuration identity contradicts persisted state")
        if self.freshness.run_id != self.state.run_id:
            raise ValueError("runtime run identity contradicts freshness state")


@dataclass(frozen=True, slots=True)
class SupervisorEvaluation:
    """One authority-free evaluation result and its next explicit state."""

    correlation: CorrelationResult
    policy: PolicyEvaluation
    decision: SupervisorDecision
    action_request: ActionRequest | None
    state: SupervisorRuntime


def canonical_record_bytes(record: BaseModel) -> bytes:
    """Return stable canonical UTF-8 JSON bytes for a validated record."""

    payload = record.model_dump(mode="json")
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _identity(prefix: str, payload: Mapping[str, object]) -> str:
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return prefix + ":" + hashlib.sha256(raw).hexdigest()


def start_supervisor(
    *,
    run_id: str,
    configuration: BoundConfiguration,
    evaluation_time: datetime,
    startup_input_sha256: tuple[str, ...],
) -> SupervisorRuntime:
    """Create explicit initializing state; startup uncertainty is never normal."""

    if evaluation_time.tzinfo is None or evaluation_time.utcoffset() is None:
        raise ValueError("evaluation_time must be timezone-aware")
    if not (
        configuration.configuration.valid_from
        <= evaluation_time
        < configuration.configuration.valid_until
    ):
        raise ValueError("configuration is outside its validity window at supervisor start")

    return SupervisorRuntime(
        configuration=configuration,
        freshness=EvaluationState.empty(run_id),
        state=initial_supervisor_state(
            run_id=run_id,
            evaluation_time=evaluation_time,
            configuration_sha256=configuration.configuration_sha256,
            input_sha256=startup_input_sha256,
        ),
    )


def evaluate_supervisor(
    observations: tuple[Observation, ...],
    *,
    evaluation_time: datetime,
    runtime: SupervisorRuntime,
    candidate_configuration: BoundConfiguration | None = None,
    output_uncertain: bool = False,
) -> SupervisorEvaluation:
    """Evaluate one explicit batch without wall clock, environment, network, or I/O."""

    if type(observations) is not tuple or not observations:
        raise ValueError("supervisor requires a nonempty observation tuple")
    input_hashes = tuple(sorted(item.input_sha256 for item in observations))
    if len(input_hashes) != len(set(input_hashes)):
        raise ValueError("supervisor input hashes must be unique")
    correlatable = tuple(
        item for item in observations if isinstance(item, (CommandObservation, PhysicalObservation))
    )
    try:
        correlation = correlate_command_and_state(
            correlatable,
            configuration=runtime.configuration.configuration,
            command_history=runtime.state.command_history,
            consumed_command_attributions=runtime.state.consumed_command_attributions,
        )
        faults: tuple[str, ...] = ()
    except ValueError:
        correlation = CorrelationResult(
            run_id=runtime.state.run_id,
            commanded_motion=False,
            measured_motion=False,
            occupancy_states=(),
            reason_codes=(),
            input_sha256=input_hashes,
            command_history=runtime.state.command_history,
            consumed_command_attributions=runtime.state.consumed_command_attributions,
        )
        faults = ("correlation_unverifiable",)

    candidate = candidate_configuration or runtime.configuration
    configuration_changed = (
        candidate.configuration_sha256 != runtime.configuration.configuration_sha256
    )
    active_configuration = runtime.configuration.configuration
    if not (active_configuration.valid_from <= evaluation_time < active_configuration.valid_until):
        faults = tuple(sorted({*faults, "configuration_invalid_at_evaluation"}))
    next_freshness = runtime.freshness
    try:
        fresh = evaluate_freshness_and_order(
            observations,
            configuration=runtime.configuration.configuration,
            evaluation_time=evaluation_time,
            state=runtime.freshness,
        )
        next_freshness = fresh.state
    except FreshnessError as error:
        faults = tuple(sorted({*faults, error.code}))

    policy = evaluate_policy(
        correlation,
        fault_reasons=faults,
        configuration_changed=configuration_changed,
        output_uncertain=output_uncertain,
    )
    attribution_state = record_command_attribution_history(
        runtime.state,
        command_history=correlation.command_history,
        consumed_command_attributions=correlation.consumed_command_attributions,
        evaluation_time=evaluation_time,
        input_sha256=input_hashes,
    ).state
    transition = apply_policy_evaluation(
        attribution_state,
        policy,
        evaluation_time=evaluation_time,
        input_sha256=input_hashes,
        configuration_sha256=runtime.configuration.configuration_sha256,
    )
    decision_payload = {
        "prior_state_id": runtime.state.state_id,
        "run_id": runtime.state.run_id,
        "evaluated_at": evaluation_time.isoformat(),
        "supervisor_state": transition.state.supervisor_state,
        "action": policy.action,
        "first_out_reason": policy.first_out_reason,
        "reason_codes": policy.reason_codes,
        "configuration_sha256": runtime.configuration.configuration_sha256,
        "input_sha256": input_hashes,
    }
    decision = SupervisorDecision(
        decision_id=_identity("decision", decision_payload),
        run_id=runtime.state.run_id,
        evaluated_at=evaluation_time,
        supervisor_state=transition.state.supervisor_state,
        action=policy.action,
        first_out_reason=policy.first_out_reason,
        reason_codes=policy.reason_codes,
        configuration_sha256=runtime.configuration.configuration_sha256,
        input_sha256=input_hashes,
    )

    request: ActionRequest | None = None
    request_action: Literal["inhibit_request", "protective_stop_request"] | None = None
    if policy.action == "inhibit_request":
        request_action = "inhibit_request"
    elif policy.action == "protective_stop_request":
        request_action = "protective_stop_request"
    final_state = transition.state
    if request_action is not None and (
        transition.state.supervisor_state == "intervention_requested"
    ):
        decision_sha = "sha256:" + hashlib.sha256(canonical_record_bytes(decision)).hexdigest()
        request = ActionRequest(
            request_id=_identity(
                "request",
                {
                    "decision_sha256": decision_sha,
                    "configuration_sha256": runtime.configuration.configuration_sha256,
                    "input_sha256": input_hashes,
                },
            ),
            run_id=runtime.state.run_id,
            created_at=evaluation_time,
            action=request_action,
            decision_sha256=decision_sha,
            configuration_sha256=runtime.configuration.configuration_sha256,
            input_sha256=input_hashes,
        )
        request_sha = "sha256:" + hashlib.sha256(canonical_record_bytes(request)).hexdigest()
        final_state = record_action_request(
            transition.state,
            request_sha256=request_sha,
            evaluation_time=evaluation_time,
            input_sha256=input_hashes,
        ).state

    next_runtime = SupervisorRuntime(runtime.configuration, next_freshness, final_state)
    return SupervisorEvaluation(correlation, policy, decision, request, next_runtime)
