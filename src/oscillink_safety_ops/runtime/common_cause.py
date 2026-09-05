"""Pure deterministic evaluation of represented shared dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .contracts import (
    SharedDependencyObservation,
    SourceHealthObservation,
    SupervisorConfiguration,
)


@dataclass(frozen=True, slots=True)
class CommonCauseEvaluation:
    """Authority-free dependency findings; never an independence or certification claim."""

    integrity_state: Literal["represented_healthy_unvalidated", "unresolved"]
    reason_codes: tuple[str, ...]
    independence_established: Literal[False] = False
    certification_state: Literal["not_established"] = "not_established"
    operational_authority: Literal["none"] = "none"


def evaluate_common_cause(
    observations: tuple[SharedDependencyObservation, ...],
    *,
    configuration: SupervisorConfiguration,
    configuration_sha256: str,
    source_health: tuple[SourceHealthObservation, ...] = (),
) -> CommonCauseEvaluation:
    """Compare dependency evidence with exact signed declarations without external effects."""

    if type(observations) is not tuple or type(source_health) is not tuple:
        raise TypeError("dependency and source health observations must be tuples")
    reasons = {"common_cause_unassessed"}
    by_dependency: dict[str, list[SharedDependencyObservation]] = {}
    for observation in observations:
        by_dependency.setdefault(observation.dependency_id, []).append(observation)

    configured_ids = {item.dependency_id for item in configuration.dependency_bindings}
    if set(by_dependency) - configured_ids:
        reasons.add("shared_dependency_unconfigured")

    health_by_target = {item.monitored_source_id: item for item in source_health}
    for binding in configuration.dependency_bindings:
        candidates = by_dependency.get(binding.dependency_id, [])
        if not candidates:
            reasons.add("shared_dependency_observation_missing")
            continue
        if len(candidates) != 1:
            reasons.add("shared_dependency_observation_ambiguous")
            continue
        observation = candidates[0]
        if (
            observation.source_id != binding.monitor_source_id
            or observation.dependency_kind != binding.dependency_kind
            or observation.affected_source_ids != binding.affected_source_ids
        ):
            reasons.add("shared_dependency_binding_mismatch")
        if observation.configuration_sha256 != configuration_sha256:
            reasons.add("shared_dependency_configuration_mismatch")
        if observation.dependency_state != "healthy":
            reasons.add(
                f"shared_dependency_{observation.dependency_state}:{observation.dependency_kind}"
            )
            if any(
                (health := health_by_target.get(source_id)) is not None
                and health.source_state == "healthy"
                for source_id in observation.affected_source_ids
            ):
                reasons.add("shared_dependency_health_contradiction")

    ordered = tuple(sorted(reasons))
    integrity: Literal["represented_healthy_unvalidated", "unresolved"] = (
        "represented_healthy_unvalidated"
        if ordered == ("common_cause_unassessed",)
        else "unresolved"
    )
    return CommonCauseEvaluation(integrity, ordered)
