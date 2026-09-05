"""Deterministic generative invariants for the simulated supervisor state machine."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from hypothesis import HealthCheck, given, seed, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from oscillink_safety_ops.runtime.contracts import (
    ActionAcknowledgment,
    CommandObservation,
    RecoveryEvent,
    SupervisorStateRecord,
)
from oscillink_safety_ops.runtime.correlator import CorrelationResult
from oscillink_safety_ops.runtime.policy import PolicyEvaluation, SupervisorAction, evaluate_policy
from oscillink_safety_ops.runtime.state_machine import (
    RecoveryConditions,
    apply_policy_evaluation,
    apply_recovery_event,
    assess_reset_readiness,
    initial_supervisor_state,
    observe_action_acknowledgment,
    record_action_request,
)
from oscillink_safety_ops.runtime.supervisor import canonical_record_bytes

NOW = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)
CONFIG = "sha256:" + "a" * 64
INPUT = "sha256:" + "b" * 64
REQUEST = "sha256:" + "c" * 64

settings.register_profile(
    "batch5",
    max_examples=100,
    derandomize=True,
    database=None,
    deadline=None,
    suppress_health_check=(HealthCheck.too_slow,),
)
settings.load_profile("batch5")


def _latched_state() -> SupervisorStateRecord:
    initial = initial_supervisor_state(
        run_id="run:property",
        evaluation_time=NOW,
        configuration_sha256=CONFIG,
        input_sha256=(INPUT,),
    )
    requested = apply_policy_evaluation(
        initial,
        PolicyEvaluation(
            "protective_stop_request",
            "human_present_with_measured_motion",
            ("human_present_with_measured_motion",),
        ),
        evaluation_time=NOW,
        input_sha256=(INPUT,),
        configuration_sha256=CONFIG,
    ).state
    return record_action_request(
        requested,
        request_sha256=REQUEST,
        evaluation_time=NOW,
        input_sha256=(INPUT,),
    ).state


@seed(0x5AFE)
@given(
    st.lists(
        st.sampled_from(("none", "advisory_warning", "inhibit_request", "protective_stop_request")),
        max_size=40,
    )
)
def test_latch_is_monotonic_under_all_policy_evaluations(
    actions: list[SupervisorAction],
) -> None:
    state = _latched_state()
    for index, action in enumerate(actions):
        result = apply_policy_evaluation(
            state,
            PolicyEvaluation(action, f"property:{index}", (f"property:{index}",)),
            evaluation_time=NOW + timedelta(microseconds=index),
            input_sha256=(INPUT,),
            configuration_sha256=CONFIG,
        )
        assert result.state.latched is True
        state = result.state


@seed(0xA017)
@given(
    st.sampled_from(("reset", "rearm", "recovery_confirmed", "fresh_start")),
    st.booleans(),
)
def test_recovery_never_commands_motion_and_invalid_sequence_cannot_clear_latch(
    kind: str, all_safe: bool
) -> None:
    conditions = RecoveryConditions(
        occupancy_clear=all_safe,
        motion_stopped=all_safe,
        sources_healthy=all_safe,
        configuration_unchanged=all_safe,
        output_resolved=all_safe,
    )
    event = RecoveryEvent.model_validate(
        {
            "event_id": f"event:{kind}",
            "run_id": "run:property",
            "observed_at": NOW,
            "event_kind": kind,
            "actor_domain": "independent_safety_authority",
            "authorization_state": "externally_authorized",
            "configuration_sha256": CONFIG,
            "input_sha256": INPUT,
        }
    )

    result = apply_recovery_event(
        _latched_state(), event, conditions=conditions, evaluation_time=NOW
    )

    assert result.action == "none"
    assert result.state.latched is True


@seed(0xC0DE)
@given(st.text(min_size=1, max_size=32).filter(lambda value: value != "none"))
def test_production_observations_cannot_gain_administrative_authority(value: str) -> None:
    payload = {
        "observation_id": "command:property",
        "run_id": "run:property",
        "source_id": "production-ai:planner",
        "sequence_number": 0,
        "observed_at": NOW,
        "received_at": NOW,
        "input_sha256": INPUT,
        "command_id": "command:property",
        "command_kind": "idle",
        "motion_requested": False,
        "reset_authority": value,
    }
    try:
        command = CommandObservation.model_validate(payload)
    except ValidationError:
        return
    assert command.reset_authority == "none"
    assert command.configuration_authority == "none"
    assert command.output_authority == "none"
    assert command.operational_authority == "none"


@seed(0xD371)
@given(st.sampled_from(("none", "advisory_warning", "inhibit_request", "protective_stop_request")))
def test_canonical_state_bytes_are_deterministic(action: SupervisorAction) -> None:
    policy = PolicyEvaluation(action, "property:reason", ("property:reason",))
    first = apply_policy_evaluation(
        initial_supervisor_state(
            run_id="run:property",
            evaluation_time=NOW,
            configuration_sha256=CONFIG,
            input_sha256=(INPUT,),
        ),
        policy,
        evaluation_time=NOW,
        input_sha256=(INPUT,),
        configuration_sha256=CONFIG,
    ).state
    second = apply_policy_evaluation(
        initial_supervisor_state(
            run_id="run:property",
            evaluation_time=NOW,
            configuration_sha256=CONFIG,
            input_sha256=(INPUT,),
        ),
        policy,
        evaluation_time=NOW,
        input_sha256=(INPUT,),
        configuration_sha256=CONFIG,
    ).state
    assert canonical_record_bytes(first) == canonical_record_bytes(second)


def _safe_conditions() -> RecoveryConditions:
    return RecoveryConditions(True, True, True, True, True)


def _ready_state() -> SupervisorStateRecord:
    acknowledgment = ActionAcknowledgment(
        acknowledgment_id="ack:property",
        run_id="run:property",
        observed_at=NOW,
        request_sha256=REQUEST,
        configuration_sha256=CONFIG,
        input_sha256=(INPUT,),
        source_domain="simulated_fixture",
        status="received_by_simulated_fixture",
    )
    stopped = observe_action_acknowledgment(
        _latched_state(), acknowledgment, evaluation_time=NOW
    ).state
    return assess_reset_readiness(stopped, conditions=_safe_conditions(), evaluation_time=NOW).state


def _event(kind: str, index: int) -> RecoveryEvent:
    return RecoveryEvent.model_validate(
        {
            "event_id": f"event:{kind}:{index}",
            "run_id": "run:property",
            "observed_at": NOW + timedelta(microseconds=index),
            "event_kind": kind,
            "actor_domain": "independent_safety_authority",
            "authorization_state": "externally_authorized",
            "configuration_sha256": CONFIG,
            "input_sha256": "sha256:" + format(index + 1, "064x"),
        }
    )


@seed(0xF123)
@given(
    st.lists(
        st.sampled_from(("reset", "rearm", "recovery_confirmed", "fresh_start")),
        min_size=1,
        max_size=12,
    )
)
def test_only_full_independent_recovery_then_fresh_start_can_clear_latch(
    kinds: list[str],
) -> None:
    state = _ready_state()
    applied: list[str] = []
    for index, kind in enumerate(kinds, start=1):
        transition = apply_recovery_event(
            state,
            _event(kind, index),
            conditions=_safe_conditions(),
            evaluation_time=NOW + timedelta(microseconds=index),
        )
        applied.append(kind)
        state = transition.state
        if not state.latched:
            assert applied[-4:] == ["reset", "rearm", "recovery_confirmed", "fresh_start"]
            assert state.supervisor_state == "initializing"
            break


@seed(0xFA11)
@given(
    st.sampled_from(
        (
            "stale_observation",
            "future_timestamp",
            "frozen_source",
            "configuration_changed_mid_run",
            "missing_source",
        )
    )
)
def test_configuration_and_freshness_uncertainty_always_fail_closed(reason: str) -> None:
    correlation = CorrelationResult(
        run_id="run:property",
        commanded_motion=False,
        measured_motion=False,
        occupancy_states=(),
        reason_codes=(),
        input_sha256=(INPUT,),
    )
    policy = evaluate_policy(
        correlation,
        fault_reasons=() if reason == "configuration_changed_mid_run" else (reason,),
        configuration_changed=reason == "configuration_changed_mid_run",
    )
    result = apply_policy_evaluation(
        initial_supervisor_state(
            run_id="run:property",
            evaluation_time=NOW,
            configuration_sha256=CONFIG,
            input_sha256=(INPUT,),
        ),
        policy,
        evaluation_time=NOW,
        input_sha256=(INPUT,),
        configuration_sha256=CONFIG,
    )
    assert policy.action in {"inhibit_request", "protective_stop_request"}
    assert result.state.latched is True
