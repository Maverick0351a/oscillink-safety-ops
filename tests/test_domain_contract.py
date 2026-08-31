from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from oscillink_safety_ops.domain import (
    Applicability,
    Approval,
    ApprovalState,
    Citation,
    ConstraintKind,
    EvidenceConstraint,
    ProposedPlan,
    SafetyMemoryPacket,
    SourceClass,
    SourceRevision,
)

SHA_A = "sha256:" + "a" * 64
SHA_B = "sha256:" + "b" * 64
NOW = datetime(2026, 8, 31, tzinfo=UTC)


def approved_constraint() -> EvidenceConstraint:
    return EvidenceConstraint(
        constraint_id="constraint-isolate-main",
        kind=ConstraintKind.REQUIRED_EVIDENCE,
        evidence_key="energy_isolation.main_disconnect",
        statement="Evidence of main disconnect isolation is required.",
        citation=Citation(
            source_id="manual-exact-model",
            locator="page:2#lines:4-6",
            quote_sha256=SHA_B,
        ),
        applicability=Applicability(asset_model="SYN-PRESS-7", asset_serial="SP7-0042"),
        approval=Approval(
            state=ApprovalState.APPROVED,
            reviewer_id="reviewer:synthetic-authorized-role",
            reviewed_at=NOW,
        ),
    )


def packet_with(constraint: EvidenceConstraint) -> SafetyMemoryPacket:
    return SafetyMemoryPacket(
        packet_id="packet-synthetic-press-7",
        policy_sha256=SHA_A,
        sources=(
            SourceRevision(
                source_id="manual-exact-model",
                source_class=SourceClass.MANUFACTURER_MANUAL,
                revision="rev-2",
                sha256=SHA_A,
                effective_at=NOW,
                applicability=Applicability(asset_model="SYN-PRESS-7", asset_serial="SP7-0042"),
            ),
        ),
        constraints=(constraint,),
    )


def test_packet_accepts_only_externally_approved_constraints() -> None:
    constraint = approved_constraint()
    unapproved = constraint.model_copy(update={"approval": Approval(state=ApprovalState.CANDIDATE)})

    with pytest.raises(ValidationError, match="externally approved"):
        packet_with(unapproved)


def test_approved_constraint_requires_review_identity_and_timestamp() -> None:
    with pytest.raises(ValidationError, match="reviewer_id"):
        Approval(state=ApprovalState.APPROVED)


def test_citation_must_reference_an_immutable_packet_source() -> None:
    constraint = approved_constraint().model_copy(
        update={
            "citation": Citation(source_id="not-in-packet", locator="page:1", quote_sha256=SHA_B)
        }
    )

    with pytest.raises(ValidationError, match="unknown source"):
        packet_with(constraint)


def test_packet_rejects_duplicate_source_identities() -> None:
    packet = packet_with(approved_constraint())

    with pytest.raises(ValidationError, match="duplicate source_id"):
        SafetyMemoryPacket(
            packet_id=packet.packet_id,
            policy_sha256=packet.policy_sha256,
            sources=(packet.sources[0], packet.sources[0]),
            constraints=packet.constraints,
        )


def test_packet_rejects_duplicate_constraint_identities() -> None:
    constraint = approved_constraint()

    with pytest.raises(ValidationError, match="duplicate constraint_id"):
        SafetyMemoryPacket(
            packet_id="packet-synthetic-press-7",
            policy_sha256=SHA_A,
            sources=packet_with(constraint).sources,
            constraints=(constraint, constraint),
        )


def test_packet_rejects_unknown_supersession_target() -> None:
    packet = packet_with(approved_constraint())
    stale_source = packet.sources[0].model_copy(update={"superseded_by": "absent-revision"})

    with pytest.raises(ValidationError, match="unknown superseded_by"):
        SafetyMemoryPacket(
            packet_id=packet.packet_id,
            policy_sha256=packet.policy_sha256,
            sources=(stale_source,),
            constraints=packet.constraints,
        )


def test_packet_rejects_self_supersession() -> None:
    packet = packet_with(approved_constraint())
    self_superseding = packet.sources[0].model_copy(
        update={"superseded_by": packet.sources[0].source_id}
    )

    with pytest.raises(ValidationError, match="cannot supersede itself"):
        SafetyMemoryPacket(
            packet_id=packet.packet_id,
            policy_sha256=packet.policy_sha256,
            sources=(self_superseding,),
            constraints=packet.constraints,
        )


def test_packet_rejects_unknown_conflict_target() -> None:
    constraint = approved_constraint().model_copy(update={"conflict_with": ("absent-constraint",)})

    with pytest.raises(ValidationError, match="unknown conflict target"):
        packet_with(constraint)


def test_packet_rejects_self_conflict() -> None:
    constraint = approved_constraint()
    self_conflicting = constraint.model_copy(update={"conflict_with": (constraint.constraint_id,)})

    with pytest.raises(ValidationError, match="cannot conflict itself"):
        packet_with(self_conflicting)


def test_contracts_accept_only_schema_version_one() -> None:
    with pytest.raises(ValidationError):
        SafetyMemoryPacket.model_validate(
            {
                "schema_version": 2,
                "packet_id": "packet-synthetic-press-7",
                "policy_sha256": SHA_A,
                "sources": [],
                "constraints": [],
            }
        )

    with pytest.raises(ValidationError):
        ProposedPlan.model_validate(
            {
                "schema_version": 2,
                "plan_id": "plan-maintenance-001",
                "asset_model": "SYN-PRESS-7",
                "declared_evidence_keys": [],
            }
        )


def test_plan_rejects_duplicate_declared_evidence_keys() -> None:
    with pytest.raises(ValidationError, match="duplicate declared evidence_key"):
        ProposedPlan(
            plan_id="plan-maintenance-001",
            asset_model="SYN-PRESS-7",
            declared_evidence_keys=("isolation.main", "isolation.main"),
        )
