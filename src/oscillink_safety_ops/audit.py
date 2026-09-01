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


def _finding_state(
    constraint: EvidenceConstraint,
    source: SourceRevision,
    plan: ProposedPlan,
) -> FindingState:
    if constraint.content_state is ContentState.AMBIGUOUS:
        return FindingState.AMBIGUOUS
    if constraint.content_state is ContentState.UNREADABLE:
        return FindingState.UNREADABLE
    if constraint.conflict_with:
        return FindingState.SOURCE_CONFLICT
    if not constraint.interpretation_supported:
        return FindingState.UNSUPPORTED_INTERPRETATION
    if source.superseded_by is not None:
        return FindingState.REVISION_STALE
    applies = constraint.applicability
    if applies.asset_model is not None and applies.asset_model != plan.asset_model:
        return FindingState.ASSET_MISMATCH
    if applies.asset_serial is not None and applies.asset_serial != plan.asset_serial:
        return FindingState.ASSET_MISMATCH
    if constraint.kind is ConstraintKind.REVIEW_GATE:
        return FindingState.REQUIRES_AUTHORIZED_REVIEW
    if constraint.evidence_key in plan.declared_evidence_keys:
        return FindingState.MATCHED
    return FindingState.MISSING_EVIDENCE


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
        AuditFinding(
            constraint_id=constraint.constraint_id,
            evidence_key=constraint.evidence_key,
            state=_finding_state(
                constraint,
                sources[constraint.citation.source_id],
                plan,
            ),
            citation=constraint.citation,
            related_ids=constraint.conflict_with,
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
        AuditFinding(
            constraint_id=constraint.constraint_id,
            evidence_key=constraint.evidence_key,
            state=_finding_state(constraint, sources[constraint.citation.source_id], plan_view),
            citation=constraint.citation,
            related_ids=constraint.conflict_with,
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
            observed_at=envelope.observed_at,
            task_id=episode.task_id,
        ),
        source_record_sha256=episode.source_record_sha256,
        findings=findings,
    )
