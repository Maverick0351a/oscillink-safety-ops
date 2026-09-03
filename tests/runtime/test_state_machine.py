"""Persistent latch and independently authorized recovery state-machine tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from oscillink_safety_ops.runtime.contracts import (
    ActionAcknowledgment,
    RecoveryEvent,
    SupervisorStateRecord,
)
from oscillink_safety_ops.runtime.policy import PolicyEvaluation
from oscillink_safety_ops.runtime.state_machine import (
    RecoveryConditions,
    apply_policy_evaluation,
    apply_recovery_event,
    assess_reset_readiness,
    initial_supervisor_state,
    observe_action_acknowledgment,
    record_action_request,
)

NOW = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)
CONFIG = "sha256:" + "a" * 64
INPUT = "sha256:" + "b" * 64
REQUEST = "sha256:" + "c" * 64
ACK_INPUT = "sha256:" + "d" * 64


def initial() -> SupervisorStateRecord:
    return initial_supervisor_state(
        run_id="run:001",
        evaluation_time=NOW,
        configuration_sha256=CONFIG,
        input_sha256=(INPUT,),
    )


def latched() -> SupervisorStateRecord:
    requested = apply_policy_evaluation(
        initial(),
        PolicyEvaluation(
            "protective_stop_request",
            "human_present_with_measured_motion",
            ("human_present_with_measured_motion",),
        ),
        evaluation_time=NOW,
        input_sha256=(INPUT,),
        configuration_sha256=CONFIG,
    )
    return record_action_request(
        requested.state,
        request_sha256=REQUEST,
        evaluation_time=NOW,
        input_sha256=(INPUT,),
    ).state


def acknowledgment(
    *, request_sha256: str = REQUEST, status: str = "received_by_simulated_fixture"
) -> ActionAcknowledgment:
    return ActionAcknowledgment.model_validate(
        {
            "acknowledgment_id": "ack:001",
            "run_id": "run:001",
            "observed_at": NOW,
            "request_sha256": request_sha256,
            "configuration_sha256": CONFIG,
            "input_sha256": (ACK_INPUT,),
            "status": status,
        }
    )


def recovery_event(kind: str, *, actor: str = "independent_safety_authority") -> RecoveryEvent:
    return RecoveryEvent.model_validate(
        {
            "event_id": f"recovery:{kind}",
            "run_id": "run:001",
            "observed_at": NOW,
            "event_kind": kind,
            "actor_domain": actor,
            "authorization_state": "externally_authorized",
            "configuration_sha256": CONFIG,
            "input_sha256": ACK_INPUT,
        }
    )


def conditions(**changes: bool) -> RecoveryConditions:
    values = {
        "occupancy_clear": True,
        "motion_stopped": True,
        "sources_healthy": True,
        "configuration_unchanged": True,
        "output_resolved": True,
    }
    values.update(changes)
    return RecoveryConditions(**values)


def stopped_unverified() -> SupervisorStateRecord:
    return observe_action_acknowledgment(latched(), acknowledgment(), evaluation_time=NOW).state


def test_required_state_vocabulary_and_normal_degraded_intervention_transitions() -> None:
    state = initial()
    assert state.supervisor_state == "initializing"
    normal = apply_policy_evaluation(
        state,
        PolicyEvaluation("none", "monitoring_normal", ("monitoring_normal",)),
        evaluation_time=NOW,
        input_sha256=(INPUT,),
        configuration_sha256=CONFIG,
    )
    degraded = apply_policy_evaluation(
        normal.state,
        PolicyEvaluation("advisory_warning", "source_degraded", ("source_degraded",)),
        evaluation_time=NOW,
        input_sha256=(INPUT,),
        configuration_sha256=CONFIG,
    )
    intervention = apply_policy_evaluation(
        degraded.state,
        PolicyEvaluation("inhibit_request", "missing_source", ("missing_source",)),
        evaluation_time=NOW,
        input_sha256=(INPUT,),
        configuration_sha256=CONFIG,
    )

    assert normal.state.supervisor_state == "monitoring_normal"
    assert degraded.state.supervisor_state == "monitoring_degraded"
    assert intervention.state.supervisor_state == "intervention_requested"
    assert intervention.state.latched is True


def test_acknowledgment_is_distinct_from_reset_and_never_clears_latch() -> None:
    state = latched()
    assert state.supervisor_state == "intervention_latched"

    observed = observe_action_acknowledgment(state, acknowledgment(), evaluation_time=NOW)

    assert observed.state.supervisor_state == "stopped_unverified"
    assert observed.state.latched is True
    assert observed.action == "none"
    assert observed.state.reset_sequence == 0


def test_acknowledgment_before_the_request_is_rejected_as_replayed() -> None:
    replayed = acknowledgment().model_copy(update={"observed_at": NOW - timedelta(seconds=1)})

    result = observe_action_acknowledgment(latched(), replayed, evaluation_time=NOW)

    assert result.state.supervisor_state == "intervention_latched"
    assert result.state.output_state == "unresolved"
    assert "output_false_acknowledgment" in result.state.reason_codes


def test_false_acknowledgment_keeps_output_unresolved_and_latched() -> None:
    for ack in (
        acknowledgment(request_sha256="sha256:" + "e" * 64),
        acknowledgment(status="rejected_by_simulated_fixture"),
    ):
        result = observe_action_acknowledgment(latched(), ack, evaluation_time=NOW)
        assert result.state.supervisor_state == "intervention_latched"
        assert result.state.output_state == "unresolved"
        assert result.state.latched is True
        assert "output_false_acknowledgment" in result.state.reason_codes


def test_reset_from_production_ai_has_no_authority() -> None:
    with pytest.raises(ValidationError):
        recovery_event("reset", actor="production_ai")


def test_reset_readiness_requires_a_latched_acknowledged_intervention() -> None:
    with pytest.raises(ValueError, match="latched intervention"):
        assess_reset_readiness(initial(), conditions=conditions(), evaluation_time=NOW)

    pending = assess_reset_readiness(latched(), conditions=conditions(), evaluation_time=NOW)
    assert pending.state.supervisor_state == "reset_not_permitted"
    assert pending.state.latched is True
    assert "reset_readiness_state_invalid" in pending.state.reason_codes


def test_reset_is_not_permitted_while_occupied_moving_degraded_changed_or_output_unresolved() -> (
    None
):
    unsafe_conditions = (
        conditions(occupancy_clear=False),
        conditions(motion_stopped=False),
        conditions(sources_healthy=False),
        conditions(configuration_unchanged=False),
        conditions(output_resolved=False),
    )
    for unsafe in unsafe_conditions:
        result = apply_recovery_event(
            stopped_unverified(),
            recovery_event("reset"),
            conditions=unsafe,
            evaluation_time=NOW,
        )
        assert result.state.supervisor_state == "reset_not_permitted"
        assert result.state.latched is True
        assert result.action == "none"


def test_replayed_or_future_recovery_event_cannot_advance_state() -> None:
    ready = assess_reset_readiness(
        stopped_unverified(), conditions=conditions(), evaluation_time=NOW
    ).state
    for observed_at, evaluation_time in (
        (NOW - timedelta(seconds=1), NOW),
        (NOW + timedelta(seconds=1), NOW),
    ):
        event = recovery_event("reset").model_copy(update={"observed_at": observed_at})
        result = apply_recovery_event(
            ready,
            event,
            conditions=conditions(),
            evaluation_time=evaluation_time,
        )
        assert result.state.supervisor_state == "reset_not_permitted"
        assert result.state.latched is True
        assert "recovery_event_time_invalid" in result.state.reason_codes


def test_reset_rearm_recovery_and_fresh_start_are_distinct_and_never_command_motion() -> None:
    ready = assess_reset_readiness(
        stopped_unverified(), conditions=conditions(), evaluation_time=NOW
    )
    reset = apply_recovery_event(
        ready.state,
        recovery_event("reset"),
        conditions=conditions(),
        evaluation_time=NOW,
    )
    rearm = apply_recovery_event(
        reset.state,
        recovery_event("rearm"),
        conditions=conditions(),
        evaluation_time=NOW,
    )
    recovered = apply_recovery_event(
        rearm.state,
        recovery_event("recovery_confirmed"),
        conditions=conditions(),
        evaluation_time=NOW,
    )
    fresh = apply_recovery_event(
        recovered.state,
        recovery_event("fresh_start"),
        conditions=conditions(),
        evaluation_time=NOW + timedelta(microseconds=1),
    )

    assert ready.state.supervisor_state == "reset_ready"
    assert reset.state.supervisor_state == "rearm_pending"
    assert rearm.state.supervisor_state == "recovery_pending"
    assert recovered.state.supervisor_state == "recovery_pending"
    assert recovered.state.fresh_start_required is True
    assert fresh.state.supervisor_state == "initializing"
    assert fresh.state.latched is False
    assert all(item.action == "none" for item in (ready, reset, rearm, recovered, fresh))


def test_reset_cannot_be_used_as_fresh_start() -> None:
    ready = assess_reset_readiness(
        stopped_unverified(), conditions=conditions(), evaluation_time=NOW
    )
    reset = apply_recovery_event(
        ready.state,
        recovery_event("reset"),
        conditions=conditions(),
        evaluation_time=NOW,
    )

    assert reset.state.supervisor_state == "rearm_pending"
    assert reset.state.latched is True
    assert reset.state.fresh_start_required is False


def test_state_records_are_byte_deterministic_for_same_explicit_inputs() -> None:
    first = apply_policy_evaluation(
        initial(),
        PolicyEvaluation("inhibit_request", "missing_source", ("missing_source",)),
        evaluation_time=NOW,
        input_sha256=(INPUT,),
        configuration_sha256=CONFIG,
    )
    second = apply_policy_evaluation(
        initial(),
        PolicyEvaluation("inhibit_request", "missing_source", ("missing_source",)),
        evaluation_time=NOW,
        input_sha256=(INPUT,),
        configuration_sha256=CONFIG,
    )

    assert first.state == second.state
    assert first.state.model_dump_json() == second.state.model_dump_json()
