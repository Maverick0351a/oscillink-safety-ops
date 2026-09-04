"""Pure deterministic supervisor orchestration tests."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

import pytest

from oscillink_safety_ops.runtime.configuration import BoundConfiguration
from oscillink_safety_ops.runtime.contracts import (
    CommandObservation,
    PhysicalObservation,
    SourceHealthObservation,
    SupervisorConfiguration,
)
from oscillink_safety_ops.runtime.freshness import EvaluationState, Observation
from oscillink_safety_ops.runtime.supervisor import (
    SupervisorRuntime,
    canonical_record_bytes,
    evaluate_supervisor,
    start_supervisor,
)

NOW = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)
SHA_A = "sha256:" + "a" * 64
SHA_B = "sha256:" + "b" * 64
SHA_C = "sha256:" + "c" * 64
SHA_D = "sha256:" + "d" * 64


def bound(raw: bytes = b"synthetic-config-v1") -> BoundConfiguration:
    configuration = SupervisorConfiguration(
        configuration_id="configuration:robot-cell:001",
        revision=1,
        scope_id="SCOPE-ROBOT-CELL-001",
        valid_from=datetime(2026, 9, 3, 11, 0, tzinfo=UTC),
        valid_until=datetime(2026, 9, 3, 13, 0, tzinfo=UTC),
        required_source_ids=(
            "independent-health-monitor:a",
            "independent-zone-sensor:a",
            "production-ai:planner",
        ),
        max_observation_age_seconds=0.5,
        max_receive_delay_seconds=0.2,
        max_future_skew_seconds=0.0,
        max_speed_mps=1.0,
        max_acceleration_mps2=2.0,
        signer_id="safety-config-signer:001",
        signature="ed25519:" + "00" * 64,
    )
    return BoundConfiguration(
        configuration=configuration,
        exact_bytes=raw,
        configuration_sha256="sha256:" + hashlib.sha256(raw).hexdigest(),
    )


def observations(
    *,
    sequence: int = 0,
    at: datetime = NOW,
    occupancy: str = "clear",
    motion: str = "stopped",
    commanded: bool = False,
    speed: float | None = 0.0,
    acceleration: float | None = 0.0,
    quality: str = "good",
    digests: tuple[str, str, str] = (SHA_A, SHA_B, SHA_C),
) -> tuple[CommandObservation, PhysicalObservation, SourceHealthObservation]:
    command = CommandObservation(
        observation_id=f"command:{sequence}",
        run_id="run:001",
        source_id="production-ai:planner",
        sequence_number=sequence,
        observed_at=at,
        received_at=at,
        input_sha256=digests[0],
        command_id=f"command-id:{sequence}",
        command_kind="motion_requested" if commanded else "idle",
        motion_requested=commanded,
    )
    physical = PhysicalObservation.model_validate(
        {
            "observation_id": f"physical:{sequence}",
            "run_id": "run:001",
            "source_id": "independent-zone-sensor:a",
            "sequence_number": sequence,
            "observed_at": at,
            "received_at": at,
            "input_sha256": digests[1],
            "zone_id": "zone:synthetic-protected",
            "occupancy": occupancy,
            "motion_state": motion,
            "speed_mps": speed,
            "acceleration_mps2": acceleration,
            "quality": quality,
            "calibration_sha256": SHA_D,
        }
    )
    health = SourceHealthObservation(
        observation_id=f"health:{sequence}",
        run_id="run:001",
        source_id="independent-health-monitor:a",
        sequence_number=sequence,
        observed_at=at,
        received_at=at,
        input_sha256=digests[2],
        monitored_source_id="independent-zone-sensor:a",
        source_state="healthy",
        clock_state="healthy",
        last_source_sequence=sequence,
    )
    return (command, physical, health)


def runtime() -> SupervisorRuntime:
    configuration = bound()
    return start_supervisor(
        run_id="run:001",
        configuration=configuration,
        evaluation_time=NOW,
        startup_input_sha256=(configuration.configuration_sha256,),
    )


def test_start_rejects_configuration_outside_its_validity_window() -> None:
    configuration = bound()
    with pytest.raises(ValueError, match="validity window"):
        start_supervisor(
            run_id="run:001",
            configuration=configuration,
            evaluation_time=NOW + timedelta(hours=2),
            startup_input_sha256=(configuration.configuration_sha256,),
        )


def test_evaluation_outside_configuration_validity_fails_closed() -> None:
    late = NOW + timedelta(hours=2)
    result = evaluate_supervisor(observations(at=late), evaluation_time=late, runtime=runtime())

    assert result.decision.action == "protective_stop_request"
    assert "configuration_invalid_at_evaluation" in result.decision.reason_codes
    assert result.state.state.latched is True


def test_runtime_rejects_mismatched_configuration_and_run_state() -> None:
    current = runtime()
    with pytest.raises(ValueError, match="configuration"):
        SupervisorRuntime(bound(b"other-config"), current.freshness, current.state)
    with pytest.raises(ValueError, match="run identity"):
        SupervisorRuntime(
            current.configuration,
            EvaluationState.empty("run:other"),
            current.state,
        )


def test_normal_evaluation_binds_configuration_and_all_sorted_exact_inputs() -> None:
    result = evaluate_supervisor(observations(), evaluation_time=NOW, runtime=runtime())

    assert result.decision.action == "none"
    assert result.decision.supervisor_state == "monitoring_normal"
    assert result.state.state.supervisor_state == "monitoring_normal"
    assert result.decision.configuration_sha256 == runtime().configuration.configuration_sha256
    assert result.decision.input_sha256 == (SHA_A, SHA_B, SHA_C)
    assert result.action_request is None


def test_occupied_measured_motion_creates_only_local_simulated_request_and_latches() -> None:
    result = evaluate_supervisor(
        observations(occupancy="present", motion="moving", commanded=True, speed=0.5),
        evaluation_time=NOW,
        runtime=runtime(),
    )

    assert result.decision.action == "protective_stop_request"
    assert result.decision.first_out_reason == "human_present_with_measured_motion"
    assert result.action_request is not None
    assert result.action_request.delivery_mode == "local_closed_file_simulation"
    assert result.action_request.operational_authority == "none"
    assert result.state.state.supervisor_state == "intervention_latched"
    assert result.state.state.latched is True


def test_motion_attribution_mismatch_creates_only_a_local_simulated_request() -> None:
    batch: list[Observation] = list(observations(motion="moving", commanded=True, speed=0.5))
    batch[0] = batch[0].model_copy(
        update={
            "motion_direction": "positive",
            "frame_id": "frame:robot-base",
            "program_id": "program:synthetic-cell",
        }
    )
    batch[1] = batch[1].model_copy(
        update={
            "motion_direction": "negative",
            "frame_id": "frame:workpiece",
            "program_id": "program:unexpected",
        }
    )

    result = evaluate_supervisor(tuple(batch), evaluation_time=NOW, runtime=runtime())

    assert result.decision.action == "protective_stop_request"
    assert {
        "motion_direction_mismatch",
        "motion_frame_mismatch",
        "motion_program_mismatch",
    }.issubset(result.decision.reason_codes)
    assert result.action_request is not None
    assert result.action_request.operational_authority == "none"
    assert result.state.state.latched is True


def test_missing_stale_frozen_and_contradictory_sources_fail_closed() -> None:
    missing = evaluate_supervisor(observations()[:-1], evaluation_time=NOW, runtime=runtime())
    stale = evaluate_supervisor(
        observations(at=NOW - timedelta(seconds=1)), evaluation_time=NOW, runtime=runtime()
    )
    contradictory_batch: list[Observation] = list(observations())
    contradictory_batch[1] = contradictory_batch[1].model_copy(
        update={"occupancy": "contradictory", "quality": "contradictory", "speed_mps": None}
    )
    contradictory = evaluate_supervisor(
        tuple(contradictory_batch), evaluation_time=NOW, runtime=runtime()
    )

    first = evaluate_supervisor(observations(), evaluation_time=NOW, runtime=runtime())
    later = NOW + timedelta(milliseconds=100)
    frozen = evaluate_supervisor(
        observations(
            sequence=1,
            at=NOW,
            digests=("sha256:" + "e" * 64, "sha256:" + "f" * 64, SHA_D),
        ),
        evaluation_time=later,
        runtime=first.state,
    )

    for result, reason in (
        (missing, "missing_source"),
        (stale, "stale_observation"),
        (frozen, "frozen_source"),
        (contradictory, "contradictory_state"),
    ):
        assert result.decision.action in {"inhibit_request", "protective_stop_request"}
        assert reason in result.decision.reason_codes
        assert result.state.state.latched is True


def test_simultaneous_faults_have_stable_first_out_and_sorted_reasons() -> None:
    batch = observations(
        at=NOW - timedelta(seconds=1),
        occupancy="present",
        motion="moving",
        commanded=False,
        speed=2.0,
        acceleration=3.0,
    )
    first = evaluate_supervisor(batch, evaluation_time=NOW, runtime=runtime())
    second = evaluate_supervisor(tuple(reversed(batch)), evaluation_time=NOW, runtime=runtime())

    assert canonical_record_bytes(first.decision) == canonical_record_bytes(second.decision)
    assert first.decision.first_out_reason == "stale_observation"
    assert first.decision.reason_codes == tuple(sorted(first.decision.reason_codes))
    assert {
        "stale_observation",
        "human_present_with_measured_motion",
        "unexpected_motion",
        "excessive_speed",
        "excessive_acceleration",
    }.issubset(first.decision.reason_codes)


def test_mid_run_configuration_change_and_output_uncertainty_fail_closed() -> None:
    changed = evaluate_supervisor(
        observations(),
        evaluation_time=NOW,
        runtime=runtime(),
        candidate_configuration=bound(b"substituted-config"),
    )
    uncertain = evaluate_supervisor(
        observations(), evaluation_time=NOW, runtime=runtime(), output_uncertain=True
    )

    assert changed.decision.action == "protective_stop_request"
    assert changed.decision.first_out_reason == "configuration_changed_mid_run"
    assert uncertain.decision.action == "protective_stop_request"
    assert uncertain.decision.first_out_reason == "output_uncertain"


def test_uncorrelatable_or_cross_run_inputs_fail_closed_without_crashing() -> None:
    health_only = evaluate_supervisor(observations()[2:], evaluation_time=NOW, runtime=runtime())
    cross_run_batch: list[Observation] = list(observations())
    cross_run_batch[1] = cross_run_batch[1].model_copy(update={"run_id": "run:other"})
    cross_run = evaluate_supervisor(tuple(cross_run_batch), evaluation_time=NOW, runtime=runtime())

    for result in (health_only, cross_run):
        assert result.decision.action == "protective_stop_request"
        assert "correlation_unverifiable" in result.decision.reason_codes
        assert result.state.state.latched is True


def test_same_configuration_state_time_and_inputs_produce_byte_identical_records() -> None:
    first = evaluate_supervisor(observations(), evaluation_time=NOW, runtime=runtime())
    second = evaluate_supervisor(observations(), evaluation_time=NOW, runtime=runtime())

    assert canonical_record_bytes(first.decision) == canonical_record_bytes(second.decision)
    assert canonical_record_bytes(first.state.state) == canonical_record_bytes(second.state.state)
    assert first == second
