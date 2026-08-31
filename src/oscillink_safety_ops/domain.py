"""Provider-neutral governed safety-memory contracts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

Sha256 = Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")]


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SourceClass(StrEnum):
    REGULATOR_TEXT = "regulator_text"
    LICENSED_STANDARD = "licensed_standard"
    MANUFACTURER_MANUAL = "manufacturer_manual"
    SITE_PROCEDURE = "site_procedure"
    TASK_PLAN = "task_plan"
    DATASET_EPISODE = "dataset_episode"


class ApprovalState(StrEnum):
    CANDIDATE = "candidate"
    APPROVED = "approved"
    REJECTED = "rejected"
    RETRACTED = "retracted"


class ConstraintKind(StrEnum):
    REQUIRED_EVIDENCE = "required_evidence"
    PROHIBITED_CONDITION = "prohibited_condition"
    REVIEW_GATE = "review_gate"


class ContentState(StrEnum):
    READABLE = "readable"
    AMBIGUOUS = "ambiguous"
    UNREADABLE = "unreadable"


class FindingState(StrEnum):
    MATCHED = "matched"
    MISSING_EVIDENCE = "missing_evidence"
    ASSET_MISMATCH = "asset_mismatch"
    REVISION_STALE = "revision_stale"
    SOURCE_CONFLICT = "source_conflict"
    AMBIGUOUS = "ambiguous"
    UNREADABLE = "unreadable"
    UNSUPPORTED_INTERPRETATION = "unsupported_interpretation"
    REQUIRES_AUTHORIZED_REVIEW = "requires_authorized_review"


class Applicability(ContractModel):
    jurisdiction: str | None = None
    site: str | None = None
    asset_model: str | None = None
    asset_serial: str | None = None
    role: str | None = None
    task_phase: str | None = None


class Approval(ContractModel):
    state: ApprovalState
    reviewer_id: str | None = None
    reviewed_at: datetime | None = None

    @model_validator(mode="after")
    def require_external_review_metadata(self) -> Self:
        if self.state is ApprovalState.APPROVED and (
            self.reviewer_id is None or self.reviewed_at is None
        ):
            raise ValueError("approved evidence requires reviewer_id and reviewed_at")
        return self


class Citation(ContractModel):
    source_id: str
    locator: str
    quote_sha256: Sha256


class SourceRevision(ContractModel):
    source_id: str
    source_class: SourceClass
    revision: str
    sha256: Sha256
    effective_at: datetime
    applicability: Applicability
    superseded_by: str | None = None


class EvidenceConstraint(ContractModel):
    constraint_id: str
    kind: ConstraintKind
    evidence_key: str
    statement: str
    citation: Citation
    applicability: Applicability
    approval: Approval
    conflict_with: tuple[str, ...] = ()
    interpretation_supported: bool = True
    content_state: ContentState = ContentState.READABLE


class SafetyMemoryPacket(ContractModel):
    schema_version: Literal[1] = 1
    packet_id: str
    policy_sha256: Sha256
    sources: tuple[SourceRevision, ...]
    constraints: tuple[EvidenceConstraint, ...]

    @model_validator(mode="after")
    def enforce_governed_references(self) -> Self:
        source_id_list = [source.source_id for source in self.sources]
        if len(source_id_list) != len(set(source_id_list)):
            raise ValueError("duplicate source_id")
        constraint_id_list = [constraint.constraint_id for constraint in self.constraints]
        if len(constraint_id_list) != len(set(constraint_id_list)):
            raise ValueError("duplicate constraint_id")
        source_ids = set(source_id_list)
        constraint_ids = set(constraint_id_list)
        for source in self.sources:
            if source.superseded_by is not None and source.superseded_by not in source_ids:
                raise ValueError(f"source {source.source_id} has unknown superseded_by target")
            if source.superseded_by == source.source_id:
                raise ValueError(f"source {source.source_id} cannot supersede itself")
        for constraint in self.constraints:
            if constraint.approval.state is not ApprovalState.APPROVED:
                raise ValueError("packet constraints must be externally approved")
            if constraint.citation.source_id not in source_ids:
                raise ValueError(f"constraint {constraint.constraint_id} cites unknown source")
            for conflict_id in constraint.conflict_with:
                if conflict_id not in constraint_ids:
                    raise ValueError(
                        f"constraint {constraint.constraint_id} has unknown conflict target"
                    )
                if conflict_id == constraint.constraint_id:
                    raise ValueError(
                        f"constraint {constraint.constraint_id} cannot conflict itself"
                    )
        return self


class ProposedPlan(ContractModel):
    schema_version: Literal[1] = 1
    plan_id: str
    asset_model: str
    asset_serial: str | None = None
    declared_evidence_keys: tuple[str, ...]

    @model_validator(mode="after")
    def reject_duplicate_evidence_keys(self) -> Self:
        if len(self.declared_evidence_keys) != len(set(self.declared_evidence_keys)):
            raise ValueError("duplicate declared evidence_key")
        return self


class AuditFinding(ContractModel):
    constraint_id: str
    evidence_key: str
    state: FindingState
    citation: Citation
    related_ids: tuple[str, ...] = ()


class AuditReport(ContractModel):
    schema_version: Literal[1] = 1
    packet_id: str
    plan_id: str
    policy_sha256: Sha256
    findings: tuple[AuditFinding, ...]
