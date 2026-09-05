"""Pure deterministic observation freshness and ordering evaluation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from types import MappingProxyType
from typing import Self, TypeAlias

from .contracts import (
    CommandObservation,
    PhysicalObservation,
    SharedDependencyObservation,
    SourceHealthObservation,
    SupervisorConfiguration,
)

Observation: TypeAlias = (
    CommandObservation | PhysicalObservation | SourceHealthObservation | SharedDependencyObservation
)


class FreshnessError(ValueError):
    """Typed fail-closed freshness or ordering result."""

    def __init__(self, code: str, source_ids: tuple[str, ...] = ()) -> None:
        self.code = code
        self.source_ids = tuple(sorted(source_ids))
        suffix = f": {', '.join(self.source_ids)}" if self.source_ids else ""
        super().__init__(code + suffix)


@dataclass(frozen=True, slots=True)
class SourceCursor:
    """Last accepted ordering and exact-byte identity for one source."""

    source_id: str
    sequence_number: int
    observed_at: datetime
    received_at: datetime
    input_sha256: str


@dataclass(frozen=True, slots=True)
class EvaluationState:
    """Explicit immutable state supplied to pure observation evaluation."""

    run_id: str
    cursors: Mapping[str, SourceCursor]
    last_evaluation_time: datetime | None = None
    initial_sequence: int = 0

    def __post_init__(self) -> None:
        if type(self.run_id) is not str or not self.run_id:
            raise FreshnessError("invalid_run_id")
        if type(self.initial_sequence) is not int or self.initial_sequence < 0:
            raise FreshnessError("invalid_initial_sequence")
        copied = dict(sorted(self.cursors.items()))
        if any(key != cursor.source_id for key, cursor in copied.items()):
            raise FreshnessError("cursor_identity_mismatch")
        object.__setattr__(self, "cursors", MappingProxyType(copied))

    @classmethod
    def empty(cls, run_id: str, *, initial_sequence: int = 0) -> Self:
        return cls(run_id=run_id, cursors={}, initial_sequence=initial_sequence)


@dataclass(frozen=True, slots=True)
class FreshnessEvaluation:
    """Accepted exact input hashes and next immutable ordering state."""

    evaluation_time: datetime
    input_sha256: tuple[str, ...]
    state: EvaluationState


def _require_aware_time(value: datetime, name: str) -> None:
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise FreshnessError(f"{name}_must_be_timezone-aware")


def _validate_source_set(
    observations: tuple[Observation, ...], configuration: SupervisorConfiguration
) -> tuple[Observation, ...]:
    by_source: dict[str, list[Observation]] = {}
    observation_ids: set[str] = set()
    input_hashes: set[str] = set()
    for observation in observations:
        by_source.setdefault(observation.source_id, []).append(observation)
        if observation.observation_id in observation_ids:
            raise FreshnessError("duplicate_observation_id", (observation.source_id,))
        observation_ids.add(observation.observation_id)
        if observation.input_sha256 in input_hashes:
            raise FreshnessError("duplicate_input", (observation.source_id,))
        input_hashes.add(observation.input_sha256)

    duplicates = tuple(source for source, items in by_source.items() if len(items) > 1)
    if duplicates:
        raise FreshnessError("duplicate_source", duplicates)

    required = set(configuration.required_source_ids)
    observed = set(by_source)
    missing = tuple(required - observed)
    if missing:
        raise FreshnessError("missing_source", missing)
    unexpected = tuple(observed - required)
    if unexpected:
        raise FreshnessError("unexpected_source", unexpected)
    return tuple(by_source[source][0] for source in sorted(by_source))


def _validate_sequence(observation: Observation, state: EvaluationState) -> None:
    cursor = state.cursors.get(observation.source_id)
    if cursor is None:
        if observation.sequence_number != state.initial_sequence:
            code = (
                "missing_sequence"
                if observation.sequence_number > state.initial_sequence
                else "sequence_rollback"
            )
            raise FreshnessError(code, (observation.source_id,))
        return

    if observation.sequence_number == cursor.sequence_number:
        raise FreshnessError("duplicate_sequence", (observation.source_id,))
    if observation.sequence_number < cursor.sequence_number:
        raise FreshnessError("sequence_rollback", (observation.source_id,))
    if observation.sequence_number > cursor.sequence_number + 1:
        raise FreshnessError("missing_sequence", (observation.source_id,))


def _validate_times(
    observation: Observation,
    *,
    configuration: SupervisorConfiguration,
    evaluation_time: datetime,
    state: EvaluationState,
) -> None:
    latest_allowed = evaluation_time + timedelta(seconds=configuration.max_future_skew_seconds)
    if observation.observed_at > latest_allowed or observation.received_at > latest_allowed:
        raise FreshnessError("future_timestamp", (observation.source_id,))
    if (
        evaluation_time - observation.observed_at
    ).total_seconds() > configuration.max_observation_age_seconds:
        raise FreshnessError("stale_observation", (observation.source_id,))
    if (
        observation.received_at - observation.observed_at
    ).total_seconds() > configuration.max_receive_delay_seconds:
        raise FreshnessError("receive_delay", (observation.source_id,))

    cursor = state.cursors.get(observation.source_id)
    if cursor is None:
        return
    if observation.observed_at < cursor.observed_at or observation.received_at < cursor.received_at:
        raise FreshnessError("timestamp_rollback", (observation.source_id,))
    if (
        observation.observed_at == cursor.observed_at
        or observation.input_sha256 == cursor.input_sha256
    ):
        raise FreshnessError("frozen_source", (observation.source_id,))


def _validate_declared_state(observation: Observation) -> None:
    if isinstance(observation, PhysicalObservation):
        if observation.quality == "missing":
            raise FreshnessError("missing_source_state", (observation.source_id,))
        if observation.quality in {"invalid", "contradictory"} or (
            observation.occupancy == "contradictory" or observation.motion_state == "contradictory"
        ):
            raise FreshnessError("contradictory_state", (observation.source_id,))
        if observation.quality != "good" or (
            observation.occupancy == "unknown" or observation.motion_state == "unknown"
        ):
            raise FreshnessError("unverifiable_state", (observation.source_id,))
    elif isinstance(observation, SourceHealthObservation):
        if observation.source_state == "missing":
            raise FreshnessError("missing_source_state", (observation.source_id,))
        if observation.source_state != "healthy":
            raise FreshnessError("unhealthy_source", (observation.source_id,))
        if observation.clock_state != "healthy":
            raise FreshnessError("unhealthy_clock", (observation.source_id,))
    elif isinstance(observation, SharedDependencyObservation):
        if observation.dependency_state != "healthy":
            raise FreshnessError("unhealthy_shared_dependency", (observation.source_id,))


def _validate_cross_source_state(observations: tuple[Observation, ...]) -> None:
    by_source = {observation.source_id: observation for observation in observations}
    for observation in observations:
        if isinstance(observation, SourceHealthObservation):
            target = by_source.get(observation.monitored_source_id)
            if target is None:
                raise FreshnessError(
                    "health_target_missing",
                    (observation.source_id, observation.monitored_source_id),
                )
            if observation.last_source_sequence != target.sequence_number:
                raise FreshnessError(
                    "health_sequence_contradiction",
                    (observation.source_id, observation.monitored_source_id),
                )

    physical = [item for item in observations if isinstance(item, PhysicalObservation)]
    zones: dict[str, list[PhysicalObservation]] = {}
    for item in physical:
        zones.setdefault(item.zone_id, []).append(item)
    for items in zones.values():
        occupancies = {item.occupancy for item in items}
        motions = {item.motion_state for item in items}
        if {"clear", "present"}.issubset(occupancies) or {"stopped", "moving"}.issubset(motions):
            raise FreshnessError(
                "cross_source_contradiction", tuple(item.source_id for item in items)
            )


def evaluate_freshness_and_order(
    observations: tuple[Observation, ...],
    *,
    configuration: SupervisorConfiguration,
    evaluation_time: datetime,
    state: EvaluationState,
) -> FreshnessEvaluation:
    """Evaluate only explicit inputs/state; this function never reads a wall clock."""

    _require_aware_time(evaluation_time, "evaluation_time")
    if state.last_evaluation_time is not None:
        _require_aware_time(state.last_evaluation_time, "last_evaluation_time")
        if evaluation_time < state.last_evaluation_time:
            raise FreshnessError("evaluation_time_rollback")

    ordered = _validate_source_set(observations, configuration)
    for observation in ordered:
        if observation.run_id != state.run_id:
            raise FreshnessError("run_mismatch", (observation.source_id,))
        _validate_sequence(observation, state)
        _validate_times(
            observation,
            configuration=configuration,
            evaluation_time=evaluation_time,
            state=state,
        )
        _validate_declared_state(observation)
    _validate_cross_source_state(ordered)

    cursors = {
        observation.source_id: SourceCursor(
            source_id=observation.source_id,
            sequence_number=observation.sequence_number,
            observed_at=observation.observed_at,
            received_at=observation.received_at,
            input_sha256=observation.input_sha256,
        )
        for observation in ordered
    }
    next_state = EvaluationState(
        run_id=state.run_id,
        cursors=cursors,
        last_evaluation_time=evaluation_time,
        initial_sequence=state.initial_sequence,
    )
    return FreshnessEvaluation(
        evaluation_time=evaluation_time,
        input_sha256=tuple(sorted(observation.input_sha256 for observation in ordered)),
        state=next_state,
    )
