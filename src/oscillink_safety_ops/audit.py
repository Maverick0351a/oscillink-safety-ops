"""Deterministic, offline, read-only audit behavior."""

from __future__ import annotations

from .domain import (
    AuditFinding,
    AuditReport,
    ConstraintKind,
    ContentState,
    EvidenceConstraint,
    FindingState,
    ProposedPlan,
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


def audit_plan(packet: SafetyMemoryPacket, plan: ProposedPlan) -> AuditReport:
    """Compare a proposed plan with approved memory without mutating either input."""
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
        findings=findings,
    )
