"""Fail-closed deterministic policy tests."""

from __future__ import annotations

from oscillink_safety_ops.runtime.correlator import CorrelationResult
from oscillink_safety_ops.runtime.policy import evaluate_policy

SHA_A = "sha256:" + "a" * 64
SHA_B = "sha256:" + "b" * 64


def correlation(
    *reasons: str,
    commanded: bool = False,
    measured: bool = False,
) -> CorrelationResult:
    return CorrelationResult(
        run_id="run:001",
        commanded_motion=commanded,
        measured_motion=measured,
        occupancy_states=("clear",),
        reason_codes=tuple(sorted(reasons)),
        input_sha256=(SHA_A, SHA_B),
    )


def test_normal_and_degraded_policy_actions_are_explicit() -> None:
    normal = evaluate_policy(correlation())
    degraded = evaluate_policy(correlation(), fault_reasons=("source_degraded",))

    assert (normal.action, normal.first_out_reason, normal.reason_codes) == (
        "none",
        "monitoring_normal",
        ("monitoring_normal",),
    )
    assert (degraded.action, degraded.first_out_reason) == (
        "advisory_warning",
        "source_degraded",
    )


def test_commanded_human_exposure_inhibits_and_measured_exposure_requests_stop() -> None:
    commanded = evaluate_policy(correlation("human_present_with_commanded_motion", commanded=True))
    measured = evaluate_policy(correlation("human_entering_with_measured_motion", measured=True))

    assert commanded.action == "inhibit_request"
    assert measured.action == "protective_stop_request"


def test_unexpected_mismatch_excessive_and_unverifiable_motion_fail_closed() -> None:
    for reason in (
        "orphan_motion",
        "unexpected_motion",
        "excessive_speed",
        "excessive_acceleration",
        "acceleration_unavailable",
        "calibration_identity_mismatch",
        "motion_direction_attribution_ambiguous",
        "motion_direction_attribution_missing",
        "motion_direction_mismatch",
        "motion_direction_state_contradiction",
        "motion_frame_attribution_missing",
        "motion_frame_mismatch",
        "motion_program_attribution_missing",
        "motion_program_mismatch",
    ):
        result = evaluate_policy(correlation(reason, measured=True))
        assert result.action == "protective_stop_request"

    assert (
        evaluate_policy(correlation("command_actual_mismatch", commanded=True)).action
        == "inhibit_request"
    )


def test_source_faults_inhibit_at_rest_and_request_stop_during_motion() -> None:
    for reason in (
        "frozen_source",
        "missing_source",
        "stale_observation",
        "contradictory_state",
        "cross_source_contradiction",
    ):
        assert evaluate_policy(correlation(), fault_reasons=(reason,)).action == "inhibit_request"
        assert (
            evaluate_policy(correlation(commanded=True), fault_reasons=(reason,)).action
            == "protective_stop_request"
        )


def test_configuration_change_and_output_uncertainty_always_fail_closed() -> None:
    changed = evaluate_policy(correlation(), configuration_changed=True)
    unresolved = evaluate_policy(correlation(), output_uncertain=True)

    assert changed.action == "protective_stop_request"
    assert changed.first_out_reason == "configuration_changed_mid_run"
    assert unresolved.action == "protective_stop_request"
    assert unresolved.first_out_reason == "output_uncertain"


def test_simultaneous_faults_have_fixed_first_out_and_sorted_contributing_reasons() -> None:
    reasons = (
        "excessive_speed",
        "human_present_with_measured_motion",
        "unexpected_motion",
    )
    first = evaluate_policy(
        correlation(*reasons, measured=True),
        fault_reasons=("stale_observation", "missing_source"),
    )
    second = evaluate_policy(
        correlation(*reversed(reasons), measured=True),
        fault_reasons=("missing_source", "stale_observation"),
    )

    assert first == second
    assert first.first_out_reason == "missing_source"
    assert first.reason_codes == tuple(sorted(first.reason_codes))
    assert set(first.reason_codes) == {
        *reasons,
        "missing_source",
        "stale_observation",
    }
