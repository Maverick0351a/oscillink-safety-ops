"""Pure latched intervention and independently authorized recovery transitions."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime

from .contracts import (
    ActionAcknowledgment,
    RecoveryEvent,
    SupervisorStateName,
    SupervisorStateRecord,
)
from .policy import PolicyEvaluation, SupervisorAction


@dataclass(frozen=True, slots=True)
class RecoveryConditions:
    """Independent represented prerequisites; no field grants operational authority."""

    occupancy_clear: bool
    motion_stopped: bool
    sources_healthy: bool
    configuration_unchanged: bool
    output_resolved: bool

    def __post_init__(self) -> None:
        if any(
            type(value) is not bool
            for value in (
                self.occupancy_clear,
                self.motion_stopped,
                self.sources_healthy,
                self.configuration_unchanged,
                self.output_resolved,
            )
        ):
            raise TypeError("recovery conditions must be plain booleans")

    @property
    def all_satisfied(self) -> bool:
        return all(
            (
                self.occupancy_clear,
                self.motion_stopped,
                self.sources_healthy,
                self.configuration_unchanged,
                self.output_resolved,
            )
        )


@dataclass(frozen=True, slots=True)
class StateTransition:
    """One deterministic state transition and non-motion supervisor action."""

    state: SupervisorStateRecord
    action: SupervisorAction


def _state_id(payload: dict[str, object]) -> str:
    def encode(value: object) -> str:
        if type(value) is datetime:
            return value.isoformat()
        raise TypeError(f"unsupported state identity value: {type(value).__name__}")

    raw = json.dumps(
        payload,
        default=encode,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "state:" + hashlib.sha256(raw).hexdigest()


def _build_state(
    previous: SupervisorStateRecord | None,
    *,
    run_id: str,
    evaluation_time: datetime,
    supervisor_state: SupervisorStateName,
    latched: bool,
    first_out_reason: str,
    reason_codes: tuple[str, ...],
    configuration_sha256: str,
    input_sha256: tuple[str, ...],
    active_request_sha256: str | None = None,
    output_state: str = "not_requested",
    reset_sequence: int = 0,
    fresh_start_required: bool = False,
) -> SupervisorStateRecord:
    ordered_reasons = tuple(sorted(set(reason_codes)))
    ordered_hashes = tuple(sorted(input_sha256))
    payload: dict[str, object] = {
        "previous_state_id": previous.state_id if previous is not None else None,
        "run_id": run_id,
        "evaluated_at": evaluation_time,
        "supervisor_state": supervisor_state,
        "latched": latched,
        "first_out_reason": first_out_reason,
        "reason_codes": ordered_reasons,
        "configuration_sha256": configuration_sha256,
        "input_sha256": ordered_hashes,
        "active_request_sha256": active_request_sha256,
        "output_state": output_state,
        "reset_sequence": reset_sequence,
        "fresh_start_required": fresh_start_required,
    }
    return SupervisorStateRecord.model_validate(
        {"state_id": _state_id(payload), **payload_without_previous(payload)}
    )


def payload_without_previous(payload: dict[str, object]) -> dict[str, object]:
    """Copy the schema payload without the internal causal seed."""

    return {key: value for key, value in payload.items() if key != "previous_state_id"}


def initial_supervisor_state(
    *,
    run_id: str,
    evaluation_time: datetime,
    configuration_sha256: str,
    input_sha256: tuple[str, ...],
) -> SupervisorStateRecord:
    return _build_state(
        None,
        run_id=run_id,
        evaluation_time=evaluation_time,
        supervisor_state="initializing",
        latched=False,
        first_out_reason="initializing",
        reason_codes=("initializing",),
        configuration_sha256=configuration_sha256,
        input_sha256=input_sha256,
    )


def apply_policy_evaluation(
    state: SupervisorStateRecord,
    policy: PolicyEvaluation,
    *,
    evaluation_time: datetime,
    input_sha256: tuple[str, ...],
    configuration_sha256: str,
) -> StateTransition:
    if state.latched:
        return StateTransition(state, policy.action)
    if policy.action == "none":
        target: SupervisorStateName = "monitoring_normal"
        latched = False
    elif policy.action == "advisory_warning":
        target = "monitoring_degraded"
        latched = False
    else:
        target = "intervention_requested"
        latched = True
    return StateTransition(
        _build_state(
            state,
            run_id=state.run_id,
            evaluation_time=evaluation_time,
            supervisor_state=target,
            latched=latched,
            first_out_reason=policy.first_out_reason,
            reason_codes=policy.reason_codes,
            configuration_sha256=configuration_sha256,
            input_sha256=input_sha256,
            reset_sequence=state.reset_sequence,
        ),
        policy.action,
    )


def record_action_request(
    state: SupervisorStateRecord,
    *,
    request_sha256: str,
    evaluation_time: datetime,
    input_sha256: tuple[str, ...],
) -> StateTransition:
    if state.supervisor_state != "intervention_requested" or not state.latched:
        raise ValueError("action request can only be recorded for a latched intervention request")
    return StateTransition(
        _build_state(
            state,
            run_id=state.run_id,
            evaluation_time=evaluation_time,
            supervisor_state="intervention_latched",
            latched=True,
            first_out_reason=state.first_out_reason,
            reason_codes=state.reason_codes,
            configuration_sha256=state.configuration_sha256,
            input_sha256=input_sha256,
            active_request_sha256=request_sha256,
            output_state="request_pending",
            reset_sequence=state.reset_sequence,
        ),
        "none",
    )


def observe_action_acknowledgment(
    state: SupervisorStateRecord,
    acknowledgment: ActionAcknowledgment,
    *,
    evaluation_time: datetime,
) -> StateTransition:
    valid = (
        state.latched
        and state.active_request_sha256 is not None
        and acknowledgment.run_id == state.run_id
        and acknowledgment.configuration_sha256 == state.configuration_sha256
        and acknowledgment.request_sha256 == state.active_request_sha256
        and state.evaluated_at <= acknowledgment.observed_at <= evaluation_time
        and acknowledgment.status == "received_by_simulated_fixture"
    )
    reasons = state.reason_codes
    target: SupervisorStateName = "stopped_unverified"
    output_state = "acknowledged_unverified"
    if not valid:
        reasons = tuple(sorted({*reasons, "output_false_acknowledgment"}))
        target = "intervention_latched"
        output_state = "unresolved"
    return StateTransition(
        _build_state(
            state,
            run_id=state.run_id,
            evaluation_time=evaluation_time,
            supervisor_state=target,
            latched=True,
            first_out_reason=state.first_out_reason,
            reason_codes=reasons,
            configuration_sha256=state.configuration_sha256,
            input_sha256=acknowledgment.input_sha256,
            active_request_sha256=state.active_request_sha256,
            output_state=output_state,
            reset_sequence=state.reset_sequence,
        ),
        "none",
    )


def assess_reset_readiness(
    state: SupervisorStateRecord,
    *,
    conditions: RecoveryConditions,
    evaluation_time: datetime,
) -> StateTransition:
    if not state.latched or state.active_request_sha256 is None:
        raise ValueError("reset readiness requires a latched intervention with an action request")
    eligible_state = (
        state.supervisor_state in {"stopped_unverified", "reset_not_permitted"}
        and state.active_request_sha256 is not None
        and state.output_state == "acknowledged_unverified"
    )
    target: SupervisorStateName = (
        "reset_ready" if eligible_state and conditions.all_satisfied else "reset_not_permitted"
    )
    reasons = state.reason_codes
    if not eligible_state:
        reasons = tuple(sorted({*reasons, "reset_readiness_state_invalid"}))
    if not conditions.all_satisfied:
        reasons = tuple(sorted({*reasons, "reset_conditions_unresolved"}))
    return StateTransition(
        _build_state(
            state,
            run_id=state.run_id,
            evaluation_time=evaluation_time,
            supervisor_state=target,
            latched=True,
            first_out_reason=state.first_out_reason,
            reason_codes=reasons,
            configuration_sha256=state.configuration_sha256,
            input_sha256=state.input_sha256,
            active_request_sha256=state.active_request_sha256,
            output_state=state.output_state,
            reset_sequence=state.reset_sequence,
        ),
        "none",
    )


def _invalid_reset_reasons(conditions: RecoveryConditions) -> tuple[str, ...]:
    failures = []
    for name, satisfied in (
        ("reset_occupancy_not_clear", conditions.occupancy_clear),
        ("reset_motion_not_stopped", conditions.motion_stopped),
        ("reset_sources_not_healthy", conditions.sources_healthy),
        ("reset_configuration_changed", conditions.configuration_unchanged),
        ("reset_output_unresolved", conditions.output_resolved),
    ):
        if not satisfied:
            failures.append(name)
    return tuple(failures)


def apply_recovery_event(
    state: SupervisorStateRecord,
    event: RecoveryEvent,
    *,
    conditions: RecoveryConditions,
    evaluation_time: datetime,
) -> StateTransition:
    valid_time = state.evaluated_at <= event.observed_at <= evaluation_time
    valid_identity = (
        event.run_id == state.run_id
        and event.configuration_sha256 == state.configuration_sha256
        and valid_time
    )
    target: SupervisorStateName
    latched = True
    fresh_start_required = state.fresh_start_required
    reset_sequence = state.reset_sequence
    reasons = state.reason_codes
    if not valid_time:
        reasons = tuple(sorted({*reasons, "recovery_event_time_invalid"}))

    if event.event_kind == "reset":
        if (
            state.supervisor_state != "reset_ready"
            or not conditions.all_satisfied
            or not valid_identity
        ):
            target = "reset_not_permitted"
            reasons = tuple(
                sorted({*reasons, *_invalid_reset_reasons(conditions), "reset_not_permitted"})
            )
        else:
            target = "rearm_pending"
            reset_sequence += 1
    elif event.event_kind == "rearm":
        if (
            state.supervisor_state == "rearm_pending"
            and conditions.all_satisfied
            and valid_identity
        ):
            target = "recovery_pending"
        else:
            target = "reset_not_permitted"
            reasons = tuple(sorted({*reasons, "rearm_not_permitted"}))
    elif event.event_kind == "recovery_confirmed":
        if (
            state.supervisor_state == "recovery_pending"
            and conditions.all_satisfied
            and valid_identity
        ):
            target = "recovery_pending"
            fresh_start_required = True
        else:
            target = "reset_not_permitted"
            reasons = tuple(sorted({*reasons, "recovery_not_permitted"}))
    else:
        if (
            state.supervisor_state == "recovery_pending"
            and state.fresh_start_required
            and conditions.all_satisfied
            and valid_identity
        ):
            target = "initializing"
            latched = False
            fresh_start_required = False
            reasons = ("fresh_start_requires_new_monitoring_evidence",)
        else:
            target = "reset_not_permitted"
            reasons = tuple(sorted({*reasons, "fresh_start_not_permitted"}))

    return StateTransition(
        _build_state(
            state,
            run_id=state.run_id,
            evaluation_time=evaluation_time,
            supervisor_state=target,
            latched=latched,
            first_out_reason=(
                "fresh_start_requires_new_monitoring_evidence"
                if target == "initializing"
                else state.first_out_reason
            ),
            reason_codes=reasons,
            configuration_sha256=state.configuration_sha256,
            input_sha256=(event.input_sha256,),
            active_request_sha256=None if target == "initializing" else state.active_request_sha256,
            output_state="not_requested" if target == "initializing" else state.output_state,
            reset_sequence=reset_sequence,
            fresh_start_required=fresh_start_required,
        ),
        "none",
    )
