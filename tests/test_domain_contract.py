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
    PhysicalIntelligenceEvidenceEnvelope,
    ProposedPlan,
    SafetyMemoryPacket,
    SourceClass,
    SourceRevision,
)
from scripts.export_schemas import SCHEMAS

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


def test_physical_intelligence_envelope_preserves_provider_neutral_evidence_identity() -> None:
    envelope = PhysicalIntelligenceEvidenceEnvelope(
        platform_id="example-physical-intelligence-platform",
        platform_version="2026.08",
        adapter_id="example-json-export-reader",
        adapter_version="1.0.0",
        adapter_config_sha256=SHA_A,
        artifact_type="recorded_episode_manifest",
        source_ref="exports/run-0042/manifest.json",
        source_revision="revision-17",
        content_sha256=SHA_B,
        observed_at=NOW,
        asset_ids=("robot-cell:synthetic-7",),
        task_id="task-maintenance-001",
        run_id="run-0042",
        episode_id="episode-0003",
        provenance_refs=("manifest:synthetic-press:revision-17",),
        payload_ref="payloads/episode-0003.json",
        missing_fields=("simulation_id",),
        unsupported_fields=("platform_private_state",),
    )

    assert envelope.platform_id == "example-physical-intelligence-platform"
    assert envelope.content_sha256 == SHA_B
    assert envelope.access_mode == "read_only"
    assert envelope.content_treatment == "untrusted_data"

    with pytest.raises(ValidationError):
        PhysicalIntelligenceEvidenceEnvelope.model_validate(
            {**envelope.model_dump(), "access_mode": "read_write"}
        )
    with pytest.raises(ValidationError):
        PhysicalIntelligenceEvidenceEnvelope.model_validate(
            {**envelope.model_dump(), "write_token": "forbidden"}
        )


def test_physical_intelligence_envelope_rejects_blank_required_identity() -> None:
    with pytest.raises(ValidationError):
        PhysicalIntelligenceEvidenceEnvelope(
            platform_id="",
            platform_version="2026.08",
            adapter_id="example-json-export-reader",
            adapter_version="1.0.0",
            adapter_config_sha256=SHA_A,
            artifact_type="recorded_episode_manifest",
            source_ref="exports/run-0042/manifest.json",
            source_revision="revision-17",
            content_sha256=SHA_B,
            observed_at=NOW,
            payload_ref="payloads/episode-0003.json",
        )


def test_physical_intelligence_envelope_rejects_conflicting_field_accounting() -> None:
    with pytest.raises(ValidationError, match="both missing and unsupported"):
        PhysicalIntelligenceEvidenceEnvelope(
            platform_id="example-physical-intelligence-platform",
            platform_version="2026.08",
            adapter_id="example-json-export-reader",
            adapter_version="1.0.0",
            adapter_config_sha256=SHA_A,
            artifact_type="recorded_episode_manifest",
            source_ref="exports/run-0042/manifest.json",
            source_revision="revision-17",
            content_sha256=SHA_B,
            observed_at=NOW,
            payload_ref="payloads/episode-0003.json",
            missing_fields=("simulation_id",),
            unsupported_fields=("simulation_id",),
        )


def test_physical_intelligence_envelope_rejects_duplicate_provenance_references() -> None:
    with pytest.raises(ValidationError, match="duplicate provenance_refs"):
        PhysicalIntelligenceEvidenceEnvelope(
            platform_id="example-physical-intelligence-platform",
            platform_version="2026.08",
            adapter_id="example-json-export-reader",
            adapter_version="1.0.0",
            adapter_config_sha256=SHA_A,
            artifact_type="recorded_episode_manifest",
            source_ref="exports/run-0042/manifest.json",
            source_revision="revision-17",
            content_sha256=SHA_B,
            observed_at=NOW,
            payload_ref="payloads/episode-0003.json",
            provenance_refs=("manifest:revision-17", "manifest:revision-17"),
        )


def test_physical_intelligence_envelope_has_a_portable_json_schema() -> None:
    schema = SCHEMAS["physical-intelligence-evidence-envelope.schema.json"]

    assert schema["additionalProperties"] is False
    assert schema["properties"]["access_mode"]["const"] == "read_only"
    assert schema["properties"]["content_treatment"]["const"] == "untrusted_data"


def test_physical_intelligence_envelope_requires_an_unambiguous_observation_time() -> None:
    with pytest.raises(ValidationError):
        PhysicalIntelligenceEvidenceEnvelope(
            platform_id="example-physical-intelligence-platform",
            platform_version="2026.08",
            adapter_id="example-json-export-reader",
            adapter_version="1.0.0",
            adapter_config_sha256=SHA_A,
            artifact_type="recorded_episode_manifest",
            source_ref="exports/run-0042/manifest.json",
            source_revision="revision-17",
            content_sha256=SHA_B,
            observed_at=datetime(2026, 8, 31),
            payload_ref="payloads/episode-0003.json",
        )
