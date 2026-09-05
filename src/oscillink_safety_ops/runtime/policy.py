"""Pure fail-closed policy evaluation over correlated and health facts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .correlator import CorrelationResult

SupervisorAction = Literal["none", "advisory_warning", "inhibit_request", "protective_stop_request"]

_FIRST_OUT_PRIORITY = (
    "configuration_changed_mid_run",
    "output_uncertain",
    "missing_source",
    "missing_source_state",
    "frozen_source",
    "stale_observation",
    "contradictory_state",
    "cross_source_contradiction",
    "health_sequence_contradiction",
    "unhealthy_clock",
    "unhealthy_source",
    "human_present_with_measured_motion",
    "human_entering_with_measured_motion",
    "human_unknown_with_measured_motion",
    "excessive_speed",
    "excessive_acceleration",
    "unexpected_motion",
    "orphan_motion",
    "acceleration_unavailable",
    "human_present_with_commanded_motion",
    "human_entering_with_commanded_motion",
    "human_unknown_with_commanded_motion",
    "command_actual_mismatch",
    "source_degraded",
)
_PRIORITY = {reason: index for index, reason in enumerate(_FIRST_OUT_PRIORITY)}
_SOURCE_FAILURES = {
    "contradictory_state",
    "cross_source_contradiction",
    "frozen_source",
    "health_sequence_contradiction",
    "health_target_missing",
    "missing_sequence",
    "missing_source",
    "missing_source_state",
    "receive_delay",
    "sequence_rollback",
    "shared_dependency_binding_mismatch",
    "shared_dependency_configuration_mismatch",
    "shared_dependency_health_contradiction",
    "shared_dependency_observation_ambiguous",
    "shared_dependency_observation_missing",
    "shared_dependency_unconfigured",
    "stale_observation",
    "timestamp_rollback",
    "unhealthy_clock",
    "unhealthy_shared_dependency",
    "unhealthy_source",
    "unverifiable_state",
}
_MEASURED_HAZARDS = {
    "acceleration_unavailable",
    "calibration_identity_mismatch",
    "calibration_identity_unapproved",
    "command_attribution_ambiguous",
    "command_attribution_id_mismatch",
    "command_attribution_missing",
    "command_attribution_nonmotion",
    "command_attribution_sequence_mismatch",
    "command_attribution_reused",
    "command_history_capacity_exceeded",
    "command_identity_reused",
    "command_response_late",
    "command_response_precedes_command",
    "excessive_acceleration",
    "excessive_speed",
    "human_entering_with_measured_motion",
    "human_present_with_measured_motion",
    "human_unknown_with_measured_motion",
    "orphan_motion",
    "motion_direction_attribution_ambiguous",
    "motion_direction_attribution_missing",
    "motion_direction_mismatch",
    "motion_direction_state_contradiction",
    "motion_frame_attribution_missing",
    "motion_frame_mismatch",
    "motion_program_attribution_missing",
    "motion_program_mismatch",
    "unexpected_motion",
}
_COMMAND_HAZARDS = {
    "command_actual_mismatch",
    "human_entering_with_commanded_motion",
    "human_present_with_commanded_motion",
    "human_unknown_with_commanded_motion",
}


@dataclass(frozen=True, slots=True)
class PolicyEvaluation:
    """Deterministic action and stable causal explanation."""

    action: SupervisorAction
    first_out_reason: str
    reason_codes: tuple[str, ...]


def _first_out(reasons: tuple[str, ...]) -> str:
    return min(reasons, key=lambda reason: (_PRIORITY.get(reason, len(_PRIORITY)), reason))


def evaluate_policy(
    correlation: CorrelationResult,
    *,
    fault_reasons: tuple[str, ...] = (),
    configuration_changed: bool = False,
    output_uncertain: bool = False,
) -> PolicyEvaluation:
    """Choose the strongest conservative request from explicit facts only."""

    if type(fault_reasons) is not tuple or any(
        type(item) is not str or not item for item in fault_reasons
    ):
        raise TypeError("fault_reasons must be a tuple of nonempty plain strings")
    reasons = set(correlation.reason_codes)
    reasons.update(fault_reasons)
    if configuration_changed:
        reasons.add("configuration_changed_mid_run")
    if output_uncertain:
        reasons.add("output_uncertain")
    if not reasons:
        return PolicyEvaluation("none", "monitoring_normal", ("monitoring_normal",))

    ordered = tuple(sorted(reasons))
    moving = correlation.commanded_motion or correlation.measured_motion
    known_reasons = _MEASURED_HAZARDS | _SOURCE_FAILURES | _COMMAND_HAZARDS | {"source_degraded"}
    if reasons - known_reasons:
        action: SupervisorAction = "protective_stop_request"
    elif configuration_changed or output_uncertain:
        action = "protective_stop_request"
    elif reasons & _MEASURED_HAZARDS:
        action = "protective_stop_request"
    elif reasons & _SOURCE_FAILURES:
        action = "protective_stop_request" if moving else "inhibit_request"
    elif reasons <= {"source_degraded"}:
        action = "advisory_warning"
    elif reasons & _COMMAND_HAZARDS:
        action = "inhibit_request"
    else:
        # Unknown policy inputs cannot silently become normal or advisory.
        action = "protective_stop_request"
    return PolicyEvaluation(action, _first_out(ordered), ordered)
