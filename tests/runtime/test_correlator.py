"""Pure deterministic command/physical-state correlation tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Literal

from oscillink_safety_ops.runtime.contracts import (
    CommandObservation,
    PhysicalObservation,
    SupervisorConfiguration,
)
from oscillink_safety_ops.runtime.correlator import correlate_command_and_state

NOW = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)
SHA_A = "sha256:" + "a" * 64
SHA_B = "sha256:" + "b" * 64
SHA_C = "sha256:" + "c" * 64


def configuration() -> SupervisorConfiguration:
    return SupervisorConfiguration(
        configuration_id="configuration:robot-cell:001",
        revision=1,
        scope_id="SCOPE-ROBOT-CELL-001",
        valid_from=datetime(2026, 9, 3, 11, 0, tzinfo=UTC),
        valid_until=datetime(2026, 9, 3, 13, 0, tzinfo=UTC),
        required_source_ids=("independent-zone-sensor:a", "production-ai:planner"),
        max_observation_age_seconds=0.5,
        max_receive_delay_seconds=0.2,
        max_future_skew_seconds=0.0,
        max_correlation_delay_seconds=0.25,
        max_speed_mps=1.0,
        max_acceleration_mps2=2.0,
        signer_id="safety-config-signer:001",
        signature="ed25519:" + "00" * 64,
    )


def command(
    *,
    motion: bool = True,
    direction: Literal["positive", "negative", "stationary", "unknown"] | None = "positive",
    frame_id: str | None = "frame:robot-base",
    program_id: str | None = "program:synthetic-cell",
) -> CommandObservation:
    return CommandObservation(
        observation_id="command:0",
        run_id="run:001",
        source_id="production-ai:planner",
        sequence_number=0,
        observed_at=NOW,
        received_at=NOW,
        input_sha256=SHA_A,
        command_id="command-id:0",
        command_kind="motion_requested" if motion else "idle",
        motion_requested=motion,
        motion_direction=direction,
        frame_id=frame_id,
        program_id=program_id,
    )


def physical(
    *,
    occupancy: str = "clear",
    motion: str = "stopped",
    speed: float | None = 0.0,
    acceleration: float | None = 0.0,
    direction: Literal["positive", "negative", "stationary", "unknown"] | None = "positive",
    frame_id: str | None = "frame:robot-base",
    program_id: str | None = "program:synthetic-cell",
    attributed_command_id: str | None = "command-id:0",
    attributed_command_sequence: int | None = 0,
) -> PhysicalObservation:
    return PhysicalObservation.model_validate(
        {
            "observation_id": "physical:0",
            "run_id": "run:001",
            "source_id": "independent-zone-sensor:a",
            "sequence_number": 0,
            "observed_at": NOW,
            "received_at": NOW,
            "input_sha256": SHA_B,
            "zone_id": "zone:synthetic-protected",
            "occupancy": occupancy,
            "motion_state": motion,
            "speed_mps": speed,
            "acceleration_mps2": acceleration,
            "quality": "degraded" if occupancy == "unknown" else "good",
            "calibration_sha256": SHA_C,
            "motion_direction": direction,
            "frame_id": frame_id,
            "program_id": program_id,
            "attributed_command_id": attributed_command_id,
            "attributed_command_sequence": attributed_command_sequence,
        }
    )


def test_human_present_entering_or_unknown_with_commanded_or_measured_motion_is_explicit() -> None:
    cases = (
        ("present", True, "stopped", "human_present_with_commanded_motion"),
        ("entering", True, "stopped", "human_entering_with_commanded_motion"),
        ("unknown", True, "stopped", "human_unknown_with_commanded_motion"),
        ("present", False, "moving", "human_present_with_measured_motion"),
        ("entering", False, "moving", "human_entering_with_measured_motion"),
        ("unknown", False, "moving", "human_unknown_with_measured_motion"),
    )
    for occupancy, commanded, measured, reason in cases:
        result = correlate_command_and_state(
            (
                physical(
                    occupancy=occupancy,
                    motion=measured,
                    speed=0.5 if measured == "moving" else 0.0,
                ),
                command(motion=commanded),
            ),
            configuration=configuration(),
        )
        assert reason in result.reason_codes


def test_orphan_unexpected_and_mismatched_motion_are_explicit() -> None:
    orphan = correlate_command_and_state(
        (command(motion=False), physical(motion="moving", speed=0.5)),
        configuration=configuration(),
    )
    mismatch = correlate_command_and_state(
        (command(motion=True), physical(motion="stopped", speed=0.0)),
        configuration=configuration(),
    )

    assert orphan.reason_codes == (
        "command_actual_mismatch",
        "command_attribution_nonmotion",
        "orphan_motion",
        "unexpected_motion",
    )
    assert mismatch.reason_codes == ("command_actual_mismatch",)


def test_conflicting_command_observations_fail_closed_explicitly() -> None:
    moving = command(motion=True)
    idle = command(motion=False).model_copy(
        update={
            "observation_id": "command:other",
            "source_id": "production-ai:other",
            "input_sha256": "sha256:" + "d" * 64,
        }
    )

    result = correlate_command_and_state(
        (moving, idle, physical(motion="moving", speed=0.5)),
        configuration=configuration(),
    )

    assert "command_observation_contradiction" in result.reason_codes


def test_excessive_speed_and_acceleration_are_detected_at_strict_boundaries() -> None:
    at_limit = correlate_command_and_state(
        (command(), physical(motion="moving", speed=1.0, acceleration=2.0)),
        configuration=configuration(),
    )
    excessive = correlate_command_and_state(
        (command(), physical(motion="moving", speed=1.000001, acceleration=2.000001)),
        configuration=configuration(),
    )

    assert "excessive_speed" not in at_limit.reason_codes
    assert "excessive_acceleration" not in at_limit.reason_codes
    assert {"excessive_speed", "excessive_acceleration"}.issubset(excessive.reason_codes)


def test_correlation_is_input_order_independent_and_binds_sorted_exact_hashes() -> None:
    inputs = (command(), physical(motion="moving", speed=0.5))
    forward = correlate_command_and_state(inputs, configuration=configuration())
    reverse = correlate_command_and_state(tuple(reversed(inputs)), configuration=configuration())

    assert forward == reverse
    assert forward.input_sha256 == (SHA_A, SHA_B)
    assert forward.reason_codes == tuple(sorted(forward.reason_codes))


def test_direction_frame_and_program_mismatches_are_independently_explicit() -> None:
    direction = correlate_command_and_state(
        (command(direction="positive"), physical(motion="moving", speed=0.5, direction="negative")),
        configuration=configuration(),
    )
    frame = correlate_command_and_state(
        (
            command(frame_id="frame:robot-base"),
            physical(motion="moving", speed=0.5, frame_id="frame:workpiece"),
        ),
        configuration=configuration(),
    )
    program = correlate_command_and_state(
        (
            command(program_id="program:synthetic-cell"),
            physical(motion="moving", speed=0.5, program_id="program:unexpected"),
        ),
        configuration=configuration(),
    )

    assert "motion_direction_mismatch" in direction.reason_codes
    assert "motion_frame_mismatch" in frame.reason_codes
    assert "motion_program_mismatch" in program.reason_codes


def test_missing_motion_attribution_is_explicit_when_motion_cannot_be_excluded() -> None:
    result = correlate_command_and_state(
        (
            command(direction=None, frame_id=None, program_id=None),
            physical(
                motion="moving",
                speed=0.5,
                direction=None,
                frame_id=None,
                program_id=None,
            ),
        ),
        configuration=configuration(),
    )

    assert {
        "motion_direction_attribution_missing",
        "motion_frame_attribution_missing",
        "motion_program_attribution_missing",
    }.issubset(result.reason_codes)


def test_ambiguous_direction_and_state_contradiction_cannot_normalize() -> None:
    ambiguous = correlate_command_and_state(
        (command(direction="unknown"), physical(motion="moving", speed=0.5)),
        configuration=configuration(),
    )
    contradictory = correlate_command_and_state(
        (command(), physical(motion="moving", speed=0.5, direction="stationary")),
        configuration=configuration(),
    )

    assert "motion_direction_attribution_ambiguous" in ambiguous.reason_codes
    assert "motion_direction_state_contradiction" in contradictory.reason_codes


def test_conflicting_physical_calibration_identity_is_explicit() -> None:
    first = physical(motion="moving", speed=0.5)
    second = first.model_copy(
        update={
            "observation_id": "physical:other",
            "source_id": "independent-zone-sensor:b",
            "input_sha256": "sha256:" + "d" * 64,
            "calibration_sha256": "sha256:" + "e" * 64,
        }
    )

    result = correlate_command_and_state(
        (command(), first, second),
        configuration=configuration(),
    )

    assert "calibration_identity_mismatch" in result.reason_codes


def test_command_identity_sequence_and_window_attribution_are_exact() -> None:
    wrong_identity = correlate_command_and_state(
        (
            command(),
            physical(
                motion="moving",
                speed=0.5,
                attributed_command_id="command-id:other",
            ),
        ),
        configuration=configuration(),
    )
    wrong_sequence = correlate_command_and_state(
        (
            command(),
            physical(motion="moving", speed=0.5, attributed_command_sequence=1),
        ),
        configuration=configuration(),
    )
    late_physical = physical(motion="moving", speed=0.5).model_copy(
        update={"observed_at": NOW + timedelta(seconds=0.250001)}
    )
    late = correlate_command_and_state(
        (command(), late_physical),
        configuration=configuration(),
    )
    early_command = command().model_copy(update={"observed_at": NOW + timedelta(microseconds=1)})
    early = correlate_command_and_state(
        (early_command, physical(motion="moving", speed=0.5)),
        configuration=configuration(),
    )

    assert "command_attribution_id_mismatch" in wrong_identity.reason_codes
    assert "command_attribution_sequence_mismatch" in wrong_sequence.reason_codes
    assert "command_response_late" in late.reason_codes
    assert "command_response_precedes_command" in early.reason_codes


def test_missing_command_identity_and_sequence_attribution_is_explicit() -> None:
    result = correlate_command_and_state(
        (
            command(),
            physical(
                motion="moving",
                speed=0.5,
                attributed_command_id=None,
                attributed_command_sequence=None,
            ),
        ),
        configuration=configuration(),
    )

    assert "command_attribution_missing" in result.reason_codes
