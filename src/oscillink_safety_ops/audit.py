"""Deterministic, offline, read-only audit behavior."""

from __future__ import annotations

from .domain import (
    AuditFinding,
    AuditReport,
    ConstraintKind,
    ContentState,
    EpisodeEvaluationReport,
    EvidenceConstraint,
    EvidenceEnvelopeBinding,
    FindingState,
    PhysicalIntelligenceEvidenceEnvelope,
    ProposedPlan,
    RecordedEpisodeEvidence,
    SafetyEvidencePacket,
    SafetyMemoryPacket,
    SourceRevision,
)


def _finding_states(
    constraint: EvidenceConstraint,
    source: SourceRevision,
    plan: ProposedPlan,
) -> tuple[FindingState, ...]:
    states: list[FindingState] = []
    if constraint.content_state is ContentState.AMBIGUOUS:
        states.append(FindingState.AMBIGUOUS)
    if constraint.content_state is ContentState.UNREADABLE:
        states.append(FindingState.UNREADABLE)
    if constraint.conflict_with:
        states.append(FindingState.SOURCE_CONFLICT)
    if not constraint.interpretation_supported:
        states.append(FindingState.UNSUPPORTED_INTERPRETATION)
    if source.superseded_by is not None:
        states.append(FindingState.REVISION_STALE)
    applies = constraint.applicability
    if (applies.asset_model is not None and applies.asset_model != plan.asset_model) or (
        applies.asset_serial is not None and applies.asset_serial != plan.asset_serial
    ):
        states.append(FindingState.ASSET_MISMATCH)
    if constraint.kind is ConstraintKind.REVIEW_GATE:
        states.append(FindingState.REQUIRES_AUTHORIZED_REVIEW)
    elif constraint.kind is ConstraintKind.PROHIBITED_CONDITION:
        if constraint.evidence_key in plan.declared_evidence_keys:
            states.append(FindingState.PROHIBITED_CONDITION_EVIDENCE_PRESENT)
        else:
            states.append(FindingState.PROHIBITED_CONDITION_EVIDENCE_NOT_DECLARED)
    elif constraint.evidence_key in plan.declared_evidence_keys:
        states.append(FindingState.MATCHED)
    else:
        states.append(FindingState.MISSING_EVIDENCE)
    return tuple(states)


def _audit_finding(
    constraint: EvidenceConstraint,
    source: SourceRevision,
    plan: ProposedPlan,
) -> AuditFinding:
    states = _finding_states(constraint, source, plan)
    return AuditFinding(
        constraint_id=constraint.constraint_id,
        evidence_key=constraint.evidence_key,
        state=states[0],
        contributing_states=states[1:],
        citation=constraint.citation,
        related_ids=constraint.conflict_with,
    )


def audit_plan(
    packet: SafetyMemoryPacket,
    plan: ProposedPlan,
    *,
    envelope: PhysicalIntelligenceEvidenceEnvelope,
) -> AuditReport:
    """Compare a proposed plan with approved memory without mutating either input."""
    if envelope.artifact_type != "proposed_plan" or envelope.task_id != plan.plan_id:
        raise ValueError("envelope must identify the audited proposed plan")
    sources = {source.source_id: source for source in packet.sources}
    findings = tuple(
        _audit_finding(
            constraint,
            sources[constraint.citation.source_id],
            plan,
        )
        for constraint in sorted(packet.constraints, key=lambda item: item.constraint_id)
    )
    return AuditReport(
        packet_id=packet.packet_id,
        plan_id=plan.plan_id,
        policy_sha256=packet.policy_sha256,
        envelope=EvidenceEnvelopeBinding(
            platform_id=envelope.platform_id,
            platform_version=envelope.platform_version,
            adapter_id=envelope.adapter_id,
            adapter_version=envelope.adapter_version,
            adapter_config_sha256=envelope.adapter_config_sha256,
            artifact_type=envelope.artifact_type,
            source_ref=envelope.source_ref,
            source_revision=envelope.source_revision,
            content_sha256=envelope.content_sha256,
            content_byte_count=envelope.content_byte_count,
            observed_at=envelope.observed_at,
            task_id=envelope.task_id,
        ),
        findings=findings,
    )


def evaluate_recorded_episode(
    packet: SafetyEvidencePacket,
    episode: RecordedEpisodeEvidence,
    *,
    envelope: PhysicalIntelligenceEvidenceEnvelope,
) -> EpisodeEvaluationReport:
    """Compare an immutable recorded episode with one exact reviewable evidence packet."""
    if (
        envelope.artifact_type != "recorded_episode_evidence"
        or envelope.task_id != episode.task_id
        or envelope.episode_id != episode.episode_id
    ):
        raise ValueError("envelope must identify the exact recorded episode")
    if packet.context.task_id != episode.task_id:
        raise ValueError("packet context must identify the exact episode task")
    if (
        packet.context.asset_model != episode.asset_model
        or packet.context.asset_serial != episode.asset_serial
    ):
        raise ValueError("packet context must identify the exact episode asset")
    plan_view = ProposedPlan(
        plan_id=episode.task_id,
        asset_model=episode.asset_model,
        asset_serial=episode.asset_serial,
        declared_evidence_keys=episode.observed_evidence_keys,
    )
    sources = {source.source_id: source for source in packet.memory.sources}
    findings = tuple(
        _audit_finding(
            constraint,
            sources[constraint.citation.source_id],
            plan_view,
        )
        for constraint in sorted(packet.memory.constraints, key=lambda item: item.constraint_id)
    )
    return EpisodeEvaluationReport(
        packet_id=packet.packet_id,
        packet_revision=packet.packet_revision,
        packet_sha256=packet.content_sha256(),
        episode_id=episode.episode_id,
        task_id=episode.task_id,
        envelope=EvidenceEnvelopeBinding(
            platform_id=envelope.platform_id,
            platform_version=envelope.platform_version,
            adapter_id=envelope.adapter_id,
            adapter_version=envelope.adapter_version,
            adapter_config_sha256=envelope.adapter_config_sha256,
            artifact_type=envelope.artifact_type,
            source_ref=envelope.source_ref,
            source_revision=envelope.source_revision,
            content_sha256=envelope.content_sha256,
            content_byte_count=envelope.content_byte_count,
            observed_at=envelope.observed_at,
            task_id=episode.task_id,
        ),
        source_record_sha256=episode.source_record_sha256,
        findings=findings,
    )
