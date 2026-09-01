from __future__ import annotations

from datetime import UTC, datetime

import pytest

from oscillink_safety_ops.audit import audit_plan
from oscillink_safety_ops.domain import (
    Applicability,
    Approval,
    ApprovalState,
    Citation,
    ConstraintKind,
    ContentState,
    EvidenceConstraint,
    FindingState,
    PhysicalIntelligenceEvidenceEnvelope,
    ProposedPlan,
    SafetyMemoryPacket,
    SourceClass,
    SourceRevision,
)

NOW = datetime(2026, 8, 31, tzinfo=UTC)
HASHES = ["sha256:" + char * 64 for char in "abcdef"]


def constraint(
    constraint_id: str,
    evidence_key: str,
    *,
    source_id: str = "manual-current",
    applicability: Applicability | None = None,
    conflict_with: tuple[str, ...] = (),
    content_state: ContentState = ContentState.READABLE,
    interpretation_supported: bool = True,
    kind: ConstraintKind = ConstraintKind.REQUIRED_EVIDENCE,
) -> EvidenceConstraint:
    return EvidenceConstraint(
        constraint_id=constraint_id,
        kind=kind,
        evidence_key=evidence_key,
        statement=f"Synthetic reviewed requirement {constraint_id}",
        citation=Citation(
            source_id=source_id,
            locator=f"section:{constraint_id}",
            quote_sha256=HASHES[1],
        ),
        applicability=applicability
        or Applicability(asset_model="SYN-PRESS-7", asset_serial="SP7-0042"),
        approval=Approval(
            state=ApprovalState.APPROVED,
            reviewer_id="reviewer:synthetic-authorized-role",
            reviewed_at=NOW,
        ),
        conflict_with=conflict_with,
        content_state=content_state,
        interpretation_supported=interpretation_supported,
    )


def source(source_id: str, *, superseded_by: str | None = None) -> SourceRevision:
    return SourceRevision(
        source_id=source_id,
        source_class=SourceClass.MANUFACTURER_MANUAL,
        revision="rev-2",
        sha256=HASHES[0],
        effective_at=NOW,
        applicability=Applicability(asset_model="SYN-PRESS-7", asset_serial="SP7-0042"),
        superseded_by=superseded_by,
    )


def plan_envelope(plan: ProposedPlan) -> PhysicalIntelligenceEvidenceEnvelope:
    return PhysicalIntelligenceEvidenceEnvelope(
        platform_id="synthetic-json-sidecar",
        platform_version="1",
        adapter_id="oscillink-safety-ops-json-reader",
        adapter_version="0.1.0",
        adapter_config_sha256=HASHES[3],
        artifact_type="proposed_plan",
        source_ref="plan.json",
        source_revision="synthetic-plan-v1",
        content_sha256=HASHES[4],
        observed_at=NOW,
        task_id=plan.plan_id,
        payload_ref="plan.json",
    )


def test_offline_audit_emits_closed_evidence_findings_with_exact_citations() -> None:
    packet = SafetyMemoryPacket(
        packet_id="packet-synthetic-press-7",
        policy_sha256=HASHES[2],
        sources=(source("manual-current"), source("manual-old", superseded_by="manual-current")),
        constraints=(
            constraint("matched", "isolation.main"),
            constraint("missing", "verification.zero_energy"),
            constraint(
                "wrong-asset",
                "asset.identity",
                applicability=Applicability(asset_model="OTHER-MODEL"),
            ),
            constraint("stale", "revision.current", source_id="manual-old"),
            constraint("conflict", "energy.type", conflict_with=("matched",)),
            constraint("ambiguous", "role.identity", content_state=ContentState.AMBIGUOUS),
            constraint("unreadable", "label.serial", content_state=ContentState.UNREADABLE),
            constraint("unsupported", "inferred.limit", interpretation_supported=False),
            constraint("review", "authorization.evidence", kind=ConstraintKind.REVIEW_GATE),
        ),
    )
    plan = ProposedPlan(
        plan_id="plan-maintenance-001",
        asset_model="SYN-PRESS-7",
        asset_serial="SP7-0042",
        declared_evidence_keys=("isolation.main",),
    )

    report = audit_plan(packet, plan, envelope=plan_envelope(plan))

    # Findings are stable across packet construction order: constraint ID is the report key.
    assert [finding.state for finding in report.findings] == [
        FindingState.AMBIGUOUS,
        FindingState.SOURCE_CONFLICT,
        FindingState.MATCHED,
        FindingState.MISSING_EVIDENCE,
        FindingState.REQUIRES_AUTHORIZED_REVIEW,
        FindingState.REVISION_STALE,
        FindingState.UNREADABLE,
        FindingState.UNSUPPORTED_INTERPRETATION,
        FindingState.ASSET_MISMATCH,
    ]
    assert all(finding.citation.source_id for finding in report.findings)
    assert report.packet_id == packet.packet_id
    assert report.plan_id == plan.plan_id
    assert report.policy_sha256 == packet.policy_sha256


def test_audit_is_deterministic_and_does_not_mutate_inputs() -> None:
    packet = SafetyMemoryPacket(
        packet_id="packet-synthetic-press-7",
        policy_sha256=HASHES[2],
        sources=(source("manual-current"),),
        constraints=(constraint("matched", "isolation.main"),),
    )
    plan = ProposedPlan(
        plan_id="plan-maintenance-001",
        asset_model="SYN-PRESS-7",
        asset_serial="SP7-0042",
        declared_evidence_keys=("isolation.main",),
    )
    packet_before = packet.model_dump_json()
    plan_before = plan.model_dump_json()

    first = audit_plan(packet, plan, envelope=plan_envelope(plan)).model_dump_json()
    second = audit_plan(packet, plan, envelope=plan_envelope(plan)).model_dump_json()

    assert first == second
    assert packet.model_dump_json() == packet_before
    assert plan.model_dump_json() == plan_before


def test_report_contains_no_operational_authority_or_action_surface() -> None:
    packet = SafetyMemoryPacket(
        packet_id="packet-synthetic-press-7",
        policy_sha256=HASHES[2],
        sources=(source("manual-current"),),
        constraints=(constraint("missing", "verification.zero_energy"),),
    )
    plan = ProposedPlan(
        plan_id="plan-maintenance-001",
        asset_model="SYN-PRESS-7",
        asset_serial="SP7-0042",
        declared_evidence_keys=(),
    )

    serialized = audit_plan(packet, plan, envelope=plan_envelope(plan)).model_dump_json().lower()

    for forbidden in (
        '"safe"',
        '"compliant"',
        '"certified"',
        '"approved_to_operate"',
        '"command"',
        '"permit"',
        '"action"',
    ):
        assert forbidden not in serialized


def test_audit_report_binds_the_exact_read_only_evidence_envelope() -> None:
    packet = SafetyMemoryPacket(
        packet_id="packet-synthetic-press-7",
        policy_sha256=HASHES[2],
        sources=(source("manual-current"),),
        constraints=(constraint("matched", "isolation.main"),),
    )
    plan = ProposedPlan(
        plan_id="plan-maintenance-001",
        asset_model="SYN-PRESS-7",
        asset_serial="SP7-0042",
        declared_evidence_keys=("isolation.main",),
    )
    envelope = PhysicalIntelligenceEvidenceEnvelope(
        platform_id="synthetic-json-sidecar",
        platform_version="1",
        adapter_id="oscillink-safety-ops-json-reader",
        adapter_version="0.1.0",
        adapter_config_sha256=HASHES[3],
        artifact_type="proposed_plan",
        source_ref="plan.json",
        source_revision="synthetic-plan-v1",
        content_sha256=HASHES[4],
        observed_at=NOW,
        task_id=plan.plan_id,
        payload_ref="plan.json",
    )

    report = audit_plan(packet, plan, envelope=envelope)

    assert report.envelope.platform_id == envelope.platform_id
    assert report.envelope.adapter_config_sha256 == envelope.adapter_config_sha256
    assert report.envelope.source_revision == envelope.source_revision
    assert report.envelope.content_sha256 == envelope.content_sha256


def test_audit_rejects_an_envelope_for_a_different_plan() -> None:
    packet = SafetyMemoryPacket(
        packet_id="packet-synthetic-press-7",
        policy_sha256=HASHES[2],
        sources=(source("manual-current"),),
        constraints=(constraint("matched", "isolation.main"),),
    )
    plan = ProposedPlan(
        plan_id="plan-maintenance-001",
        asset_model="SYN-PRESS-7",
        asset_serial="SP7-0042",
        declared_evidence_keys=("isolation.main",),
    )
    wrong_envelope = plan_envelope(plan).model_copy(update={"task_id": "different-plan"})

    with pytest.raises(ValueError, match="must identify the audited proposed plan"):
        audit_plan(packet, plan, envelope=wrong_envelope)
