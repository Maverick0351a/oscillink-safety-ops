"""Pure deterministic correlation of command intent and represented physical state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from .contracts import CommandObservation, PhysicalObservation, SupervisorConfiguration

CorrelatableObservation: TypeAlias = CommandObservation | PhysicalObservation


@dataclass(frozen=True, slots=True)
class CorrelationResult:
    """Authority-free facts derived only from supplied immutable records."""

    run_id: str
    commanded_motion: bool
    measured_motion: bool
    occupancy_states: tuple[str, ...]
    reason_codes: tuple[str, ...]
    input_sha256: tuple[str, ...]


def correlate_command_and_state(
    observations: tuple[CorrelatableObservation, ...],
    *,
    configuration: SupervisorConfiguration,
) -> CorrelationResult:
    """Correlate explicit inputs without clocks, I/O, randomness, or mutable state."""

    if type(observations) is not tuple or not observations:
        raise ValueError("correlation requires a nonempty observation tuple")
    run_ids = {item.run_id for item in observations}
    if len(run_ids) != 1:
        raise ValueError("correlation inputs must share one run_id")
    hashes = tuple(sorted(item.input_sha256 for item in observations))
    if len(hashes) != len(set(hashes)):
        raise ValueError("correlation inputs must have unique exact-byte hashes")

    commands = tuple(item for item in observations if isinstance(item, CommandObservation))
    physical = tuple(item for item in observations if isinstance(item, PhysicalObservation))
    commanded_motion = any(item.motion_requested for item in commands)
    measured_motion = any(item.motion_state == "moving" for item in physical)
    occupancies = tuple(sorted({item.occupancy for item in physical}))
    reasons: set[str] = set()

    if len({item.motion_requested for item in commands}) > 1:
        reasons.add("command_observation_contradiction")
    if commanded_motion != measured_motion:
        reasons.add("command_actual_mismatch")
    if measured_motion and not commanded_motion:
        reasons.update(("orphan_motion", "unexpected_motion"))

    for item in physical:
        if item.occupancy in {"present", "entering", "unknown"}:
            if commanded_motion:
                reasons.add(f"human_{item.occupancy}_with_commanded_motion")
            if item.motion_state == "moving":
                reasons.add(f"human_{item.occupancy}_with_measured_motion")
        if item.speed_mps is not None and item.speed_mps > configuration.max_speed_mps:
            reasons.add("excessive_speed")
        if (
            item.acceleration_mps2 is not None
            and item.acceleration_mps2 > configuration.max_acceleration_mps2
        ):
            reasons.add("excessive_acceleration")
        if item.motion_state == "moving" and item.acceleration_mps2 is None:
            reasons.add("acceleration_unavailable")

    return CorrelationResult(
        run_id=next(iter(run_ids)),
        commanded_motion=commanded_motion,
        measured_motion=measured_motion,
        occupancy_states=occupancies,
        reason_codes=tuple(sorted(reasons)),
        input_sha256=hashes,
    )
