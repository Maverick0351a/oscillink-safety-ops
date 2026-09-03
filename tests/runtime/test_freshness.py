"""Pure deterministic freshness, source-state, and ordering tests."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from typing import Literal

import pytest

from oscillink_safety_ops.runtime.contracts import (
    CommandObservation,
    PhysicalObservation,
    SourceHealthObservation,
    SupervisorConfiguration,
)
from oscillink_safety_ops.runtime.freshness import (
    EvaluationState,
    FreshnessError,
    evaluate_freshness_and_order,
)

NOW = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)
SHA_A = "sha256:" + "a" * 64
SHA_B = "sha256:" + "b" * 64
SHA_C = "sha256:" + "c" * 64
SHA_D = "sha256:" + "d" * 64


def configuration(
    *,
    required_source_ids: tuple[str, ...] = (
        "independent-health-monitor:a",
        "independent-zone-sensor:a",
        "production-ai:planner",
    ),
    max_age: float = 0.5,
    max_delay: float = 0.2,
    future_skew: float = 0.0,
) -> SupervisorConfiguration:
    return SupervisorConfiguration(
        configuration_id="configuration:robot-cell:001",
        revision=1,
        scope_id="SCOPE-ROBOT-CELL-001",
        valid_from=datetime(2026, 9, 3, 11, 0, tzinfo=UTC),
        valid_until=datetime(2026, 9, 3, 13, 0, tzinfo=UTC),
        required_source_ids=required_source_ids,
        max_observation_age_seconds=max_age,
        max_receive_delay_seconds=max_delay,
        max_future_skew_seconds=future_skew,
        max_speed_mps=1.0,
        max_acceleration_mps2=2.0,
        signer_id="safety-config-signer:001",
        signature="ed25519:" + "00" * 64,
    )


def command(
    *,
    sequence: int = 0,
    observed_at: datetime = NOW,
    received_at: datetime = NOW,
    digest: str = SHA_A,
) -> CommandObservation:
    return CommandObservation(
        observation_id=f"command:{sequence}",
        run_id="run:001",
        source_id="production-ai:planner",
        sequence_number=sequence,
        observed_at=observed_at,
        received_at=received_at,
        input_sha256=digest,
        command_id=f"command-id:{sequence}",
        command_kind="motion_requested",
        motion_requested=True,
    )


def physical(
    *,
    source_id: str = "independent-zone-sensor:a",
    sequence: int = 0,
    observed_at: datetime = NOW,
    received_at: datetime = NOW,
    digest: str = SHA_B,
    occupancy: Literal["clear", "present", "unknown", "contradictory"] = "clear",
    motion_state: Literal["stopped", "moving", "unknown", "contradictory"] = "stopped",
    quality: Literal["good", "degraded", "invalid", "missing", "contradictory"] = "good",
) -> PhysicalObservation:
    return PhysicalObservation(
        observation_id=f"physical:{source_id}:{sequence}",
        run_id="run:001",
        source_id=source_id,
        sequence_number=sequence,
        observed_at=observed_at,
        received_at=received_at,
        input_sha256=digest,
        zone_id="zone:synthetic-protected",
        occupancy=occupancy,
        motion_state=motion_state,
        speed_mps=0.0 if quality not in {"missing", "contradictory"} else None,
        quality=quality,
        calibration_sha256=SHA_D,
    )


def health(
    *,
    sequence: int = 0,
    observed_at: datetime = NOW,
    received_at: datetime = NOW,
    digest: str = SHA_C,
    source_state: Literal["healthy", "degraded", "failed", "missing", "contradictory"] = (
        "healthy"
    ),
    clock_state: Literal["healthy", "degraded", "failed", "unknown", "contradictory"] = ("healthy"),
    last_source_sequence: int | None = 0,
) -> SourceHealthObservation:
    return SourceHealthObservation(
        observation_id=f"health:{sequence}",
        run_id="run:001",
        source_id="independent-health-monitor:a",
        sequence_number=sequence,
        observed_at=observed_at,
        received_at=received_at,
        input_sha256=digest,
        monitored_source_id="independent-zone-sensor:a",
        source_state=source_state,
        clock_state=clock_state,
        last_source_sequence=last_source_sequence,
    )


def nominal_batch(
    *,
    sequence: int = 0,
    observed_at: datetime = NOW,
    digests: tuple[str, str, str] = (SHA_A, SHA_B, SHA_C),
) -> tuple[CommandObservation | PhysicalObservation | SourceHealthObservation, ...]:
    return (
        command(
            sequence=sequence,
            observed_at=observed_at,
            received_at=observed_at,
            digest=digests[0],
        ),
        physical(
            sequence=sequence,
            observed_at=observed_at,
            received_at=observed_at,
            digest=digests[1],
        ),
        health(
            sequence=sequence,
            observed_at=observed_at,
            received_at=observed_at,
            digest=digests[2],
            last_source_sequence=sequence,
        ),
    )


def test_evaluation_is_pure_deterministic_and_returns_immutable_state() -> None:
    initial = EvaluationState.empty("run:001")
    first = evaluate_freshness_and_order(
        tuple(reversed(nominal_batch())),
        configuration=configuration(),
        evaluation_time=NOW,
        state=initial,
    )
    repeated = evaluate_freshness_and_order(
        nominal_batch(),
        configuration=configuration(),
        evaluation_time=NOW,
        state=initial,
    )

    assert first == repeated
    assert first.input_sha256 == (SHA_A, SHA_B, SHA_C)
    assert tuple(first.state.cursors) == tuple(sorted(first.state.cursors))
    assert initial.cursors == {}
    with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
        first.state.run_id = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        first.state.cursors["new"] = first.state.cursors["production-ai:planner"]  # type: ignore[index]


def test_missing_required_source_is_rejected() -> None:
    with pytest.raises(FreshnessError) as captured:
        evaluate_freshness_and_order(
            nominal_batch()[:-1],
            configuration=configuration(),
            evaluation_time=NOW,
            state=EvaluationState.empty("run:001"),
        )

    assert captured.value.code == "missing_source"
    assert captured.value.source_ids == ("independent-health-monitor:a",)


def test_duplicate_source_observation_and_duplicate_input_are_rejected() -> None:
    duplicate_source = (
        *nominal_batch(),
        physical(source_id="independent-zone-sensor:a", sequence=1, digest=SHA_D),
    )
    with pytest.raises(FreshnessError) as captured:
        evaluate_freshness_and_order(
            duplicate_source,
            configuration=configuration(),
            evaluation_time=NOW,
            state=EvaluationState.empty("run:001"),
        )
    assert captured.value.code == "duplicate_source"

    duplicate_hash = nominal_batch(digests=(SHA_A, SHA_A, SHA_C))
    with pytest.raises(FreshnessError) as captured:
        evaluate_freshness_and_order(
            duplicate_hash,
            configuration=configuration(),
            evaluation_time=NOW,
            state=EvaluationState.empty("run:001"),
        )
    assert captured.value.code == "duplicate_input"


@pytest.mark.parametrize(
    ("first_sequence", "second_sequence", "expected_code"),
    ((0, 0, "duplicate_sequence"), (0, 2, "missing_sequence"), (2, 1, "sequence_rollback")),
)
def test_duplicate_missing_and_rollback_sequences_are_rejected(
    first_sequence: int, second_sequence: int, expected_code: str
) -> None:
    first = evaluate_freshness_and_order(
        nominal_batch(sequence=first_sequence),
        configuration=configuration(),
        evaluation_time=NOW,
        state=EvaluationState.empty("run:001", initial_sequence=first_sequence),
    )
    later = NOW + timedelta(milliseconds=100)

    with pytest.raises(FreshnessError) as captured:
        evaluate_freshness_and_order(
            nominal_batch(
                sequence=second_sequence,
                observed_at=later,
                digests=(
                    "sha256:" + "d" * 64,
                    "sha256:" + "e" * 64,
                    "sha256:" + "f" * 64,
                ),
            ),
            configuration=configuration(),
            evaluation_time=later,
            state=first.state,
        )

    assert captured.value.code == expected_code


def test_initial_sequence_must_match_explicit_state_expectation() -> None:
    with pytest.raises(FreshnessError) as captured:
        evaluate_freshness_and_order(
            nominal_batch(sequence=1),
            configuration=configuration(),
            evaluation_time=NOW,
            state=EvaluationState.empty("run:001"),
        )

    assert captured.value.code == "missing_sequence"


@pytest.mark.parametrize("field", ("observed_at", "received_at"))
def test_future_timestamps_are_rejected_relative_to_explicit_evaluation_time(field: str) -> None:
    future = NOW + timedelta(microseconds=1)
    values = {field: future}
    if field == "observed_at":
        values["received_at"] = future
    item = command(**values)  # type: ignore[arg-type]
    batch = (item, physical(), health())

    with pytest.raises(FreshnessError) as captured:
        evaluate_freshness_and_order(
            batch,
            configuration=configuration(),
            evaluation_time=NOW,
            state=EvaluationState.empty("run:001"),
        )

    assert captured.value.code == "future_timestamp"


def test_configured_future_skew_is_explicit_and_bounded() -> None:
    future = NOW + timedelta(milliseconds=50)
    batch = (
        command(observed_at=future, received_at=future),
        physical(observed_at=future, received_at=future),
        health(observed_at=future, received_at=future),
    )

    result = evaluate_freshness_and_order(
        batch,
        configuration=configuration(future_skew=0.1),
        evaluation_time=NOW,
        state=EvaluationState.empty("run:001"),
    )

    assert result.state.last_evaluation_time == NOW


def test_stale_observation_and_receive_delay_are_rejected() -> None:
    old = NOW - timedelta(seconds=0.500001)
    with pytest.raises(FreshnessError) as captured:
        evaluate_freshness_and_order(
            nominal_batch(observed_at=old),
            configuration=configuration(),
            evaluation_time=NOW,
            state=EvaluationState.empty("run:001"),
        )
    assert captured.value.code == "stale_observation"

    delayed = command(observed_at=NOW - timedelta(seconds=0.200001), received_at=NOW)
    with pytest.raises(FreshnessError) as captured:
        evaluate_freshness_and_order(
            (delayed, physical(), health()),
            configuration=configuration(max_age=1.0),
            evaluation_time=NOW,
            state=EvaluationState.empty("run:001"),
        )
    assert captured.value.code == "receive_delay"


def test_evaluation_and_source_timestamp_rollback_are_rejected() -> None:
    first = evaluate_freshness_and_order(
        nominal_batch(),
        configuration=configuration(),
        evaluation_time=NOW,
        state=EvaluationState.empty("run:001"),
    )
    with pytest.raises(FreshnessError) as captured:
        evaluate_freshness_and_order(
            nominal_batch(
                sequence=1,
                observed_at=NOW + timedelta(milliseconds=1),
                digests=(SHA_D, "sha256:" + "e" * 64, "sha256:" + "f" * 64),
            ),
            configuration=configuration(),
            evaluation_time=NOW - timedelta(microseconds=1),
            state=first.state,
        )
    assert captured.value.code == "evaluation_time_rollback"

    rollback = NOW - timedelta(microseconds=1)
    with pytest.raises(FreshnessError) as captured:
        evaluate_freshness_and_order(
            nominal_batch(
                sequence=1,
                observed_at=rollback,
                digests=(SHA_D, "sha256:" + "e" * 64, "sha256:" + "f" * 64),
            ),
            configuration=configuration(max_age=1.0),
            evaluation_time=NOW + timedelta(milliseconds=1),
            state=first.state,
        )
    assert captured.value.code == "timestamp_rollback"


def test_frozen_source_timestamp_or_exact_input_is_rejected() -> None:
    first = evaluate_freshness_and_order(
        nominal_batch(),
        configuration=configuration(),
        evaluation_time=NOW,
        state=EvaluationState.empty("run:001"),
    )
    evaluation = NOW + timedelta(milliseconds=100)

    with pytest.raises(FreshnessError) as captured:
        evaluate_freshness_and_order(
            nominal_batch(
                sequence=1,
                observed_at=NOW,
                digests=(SHA_D, "sha256:" + "e" * 64, "sha256:" + "f" * 64),
            ),
            configuration=configuration(),
            evaluation_time=evaluation,
            state=first.state,
        )
    assert captured.value.code == "frozen_source"

    with pytest.raises(FreshnessError) as captured:
        evaluate_freshness_and_order(
            nominal_batch(
                sequence=1,
                observed_at=evaluation,
                digests=(SHA_A, "sha256:" + "e" * 64, "sha256:" + "f" * 64),
            ),
            configuration=configuration(),
            evaluation_time=evaluation,
            state=first.state,
        )
    assert captured.value.code == "frozen_source"


@pytest.mark.parametrize(
    ("replacement", "expected_code"),
    (
        (physical(occupancy="contradictory", quality="contradictory"), "contradictory_state"),
        (physical(occupancy="unknown", quality="degraded"), "unverifiable_state"),
        (physical(quality="missing"), "missing_source_state"),
        (health(source_state="failed"), "unhealthy_source"),
        (health(clock_state="unknown"), "unhealthy_clock"),
    ),
)
def test_missing_contradictory_unknown_and_unhealthy_source_state_is_rejected(
    replacement: PhysicalObservation | SourceHealthObservation, expected_code: str
) -> None:
    batch = tuple(
        replacement if item.source_id == replacement.source_id else item for item in nominal_batch()
    )

    with pytest.raises(FreshnessError) as captured:
        evaluate_freshness_and_order(
            batch,
            configuration=configuration(),
            evaluation_time=NOW,
            state=EvaluationState.empty("run:001"),
        )

    assert captured.value.code == expected_code


def test_health_sequence_mismatch_and_cross_source_contradiction_are_rejected() -> None:
    mismatched = (command(), physical(), health(last_source_sequence=1))
    with pytest.raises(FreshnessError) as captured:
        evaluate_freshness_and_order(
            mismatched,
            configuration=configuration(),
            evaluation_time=NOW,
            state=EvaluationState.empty("run:001"),
        )
    assert captured.value.code == "health_sequence_contradiction"

    required = (
        "independent-zone-sensor:a",
        "independent-zone-sensor:b",
        "production-ai:planner",
    )
    contradictory = (
        command(),
        physical(source_id="independent-zone-sensor:a", digest=SHA_B, occupancy="clear"),
        physical(source_id="independent-zone-sensor:b", digest=SHA_C, occupancy="present"),
    )
    with pytest.raises(FreshnessError) as captured:
        evaluate_freshness_and_order(
            contradictory,
            configuration=configuration(required_source_ids=required),
            evaluation_time=NOW,
            state=EvaluationState.empty("run:001"),
        )
    assert captured.value.code == "cross_source_contradiction"


def test_run_mismatch_and_naive_explicit_times_are_rejected() -> None:
    wrong_run = command().model_copy(update={"run_id": "run:other"})
    with pytest.raises(FreshnessError) as captured:
        evaluate_freshness_and_order(
            (wrong_run, physical(), health()),
            configuration=configuration(),
            evaluation_time=NOW,
            state=EvaluationState.empty("run:001"),
        )
    assert captured.value.code == "run_mismatch"

    with pytest.raises(FreshnessError, match="timezone-aware"):
        evaluate_freshness_and_order(
            nominal_batch(),
            configuration=configuration(),
            evaluation_time=NOW.replace(tzinfo=None),
            state=EvaluationState.empty("run:001"),
        )
