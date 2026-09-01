"""Provider-neutral governed safety-memory contracts."""

from __future__ import annotations

import hashlib
from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Literal, Self
from urllib.parse import urlparse

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictFloat,
    StrictInt,
    StrictStr,
    model_validator,
)

Sha256 = Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")]
NonEmptyStr = Annotated[str, Field(min_length=1)]
JsonScalar = StrictStr | StrictInt | StrictFloat | StrictBool | None


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


class OperationalSourceType(StrEnum):
    FIRE_SUPPRESSION = "fire_suppression"
    AMMONIA_DETECTION = "ammonia_detection"
    AUTONOMOUS_SYSTEM = "autonomous_system"


class OperationalRecordKind(StrEnum):
    MEASUREMENT = "measurement"
    EVENT = "event"
    LOG = "log"


class ObservationQuality(StrEnum):
    GOOD = "good"
    BAD = "bad"
    UNCERTAIN = "uncertain"
    MISSING = "missing"


class OperationalReviewDecision(StrEnum):
    ACCEPTED_INTERPRETATION = "accepted_interpretation"
    REJECTED_INTERPRETATION = "rejected_interpretation"
    CORRECTED_INTERPRETATION = "corrected_interpretation"
    RETRACTED_INTERPRETATION = "retracted_interpretation"


class OperationalImpactState(StrEnum):
    CURRENT = "current"
    STALE_RECORD_CHANGED = "stale_record_changed"
    STALE_RECORD_MISSING = "stale_record_missing"
    STALE_ARTIFACT_CHANGED = "stale_artifact_changed"
    STALE_SOURCE_REVISION_CHANGED = "stale_source_revision_changed"
    STALE_ADAPTER_CONFIG_CHANGED = "stale_adapter_config_changed"


class RegulatoryEvidenceRole(StrEnum):
    ANNUAL_CFR_BASELINE = "annual_cfr_baseline"
    ECFR_POINT_IN_TIME = "ecfr_point_in_time"
    FEDERAL_REGISTER_CHANGE = "federal_register_change"
    LSA_CHANGE_INDEX = "lsa_change_index"


class RegulatoryReconciliationStatus(StrEnum):
    VERIFIED_MATCH = "verified_match"
    EXPLAINED_OFFICIAL_CHANGE = "explained_official_change"
    UNRESOLVED_DIFFERENCE = "unresolved_difference"
    MISSING_EVIDENCE = "missing_evidence"


class RegulatorySourceReviewDecision(StrEnum):
    PROMOTE_VERIFIED_REGULATORY_SOURCE = "promote_verified_regulatory_source"
    REJECT_SOURCE_VERIFICATION = "reject_source_verification"


class RegulatoryDifferenceReviewDecision(StrEnum):
    ACCEPT_EXPLAINED_OFFICIAL_CHANGE = "accept_explained_official_change"
    REJECT_CHANGE_EXPLANATION = "reject_change_explanation"


class FederalRegisterAction(StrEnum):
    AMEND = "amend"
    CORRECT = "correct"
    DELAY_EFFECTIVE_DATE = "delay_effective_date"
    REDESIGNATE = "redesignate"
    REMOVE = "remove"
    WITHDRAW = "withdraw"
    UNKNOWN = "unknown"


class OperationalEvidenceRecord(ContractModel):
    """One untrusted record from a read-only facility or autonomous-system export."""

    schema_version: Literal[1] = 1
    record_id: NonEmptyStr
    source_type: OperationalSourceType
    record_kind: OperationalRecordKind
    scope_id: NonEmptyStr
    system_id: NonEmptyStr
    component_id: NonEmptyStr
    source_tag: NonEmptyStr
    observed_at: AwareDatetime
    raw_record_sha256: Sha256
    raw_value: JsonScalar
    units: NonEmptyStr | None = None
    quality: ObservationQuality
    calibration_revision: NonEmptyStr | None = None
    event_code: NonEmptyStr | None = None
    message: NonEmptyStr | None = None
    missing_fields: tuple[NonEmptyStr, ...] = ()
    unsupported_fields: tuple[NonEmptyStr, ...] = ()
    authority_state: Literal["observational_evidence"] = "observational_evidence"
    access_mode: Literal["read_only"] = "read_only"
    content_treatment: Literal["untrusted_data"] = "untrusted_data"

    @model_validator(mode="after")
    def preserve_missing_and_unsupported_state(self) -> Self:
        overlap = set(self.missing_fields) & set(self.unsupported_fields)
        if overlap:
            raise ValueError("a field cannot be both missing and unsupported")
        if self.quality is ObservationQuality.MISSING and self.raw_value is not None:
            raise ValueError("missing quality requires raw_value to be null")
        if self.raw_value is None and "raw_value" not in self.missing_fields:
            raise ValueError("null raw_value must be declared missing")
        return self


class OperationalEvidenceBatch(ContractModel):
    """Deterministic batch normalized from one immutable operational export."""

    schema_version: Literal[1] = 1
    batch_id: NonEmptyStr
    source_revision: NonEmptyStr
    source_artifact_sha256: Sha256
    adapter_config_sha256: Sha256
    records: tuple[OperationalEvidenceRecord, ...]
    authority_state: Literal["observational_evidence"] = "observational_evidence"
    access_mode: Literal["read_only"] = "read_only"
    content_treatment: Literal["untrusted_data"] = "untrusted_data"

    @model_validator(mode="after")
    def reject_duplicate_records(self) -> Self:
        identities = [item.record_id for item in self.records]
        if len(identities) != len(set(identities)):
            raise ValueError("duplicate record_id")
        return self


class OperationalInterpretationRule(ContractModel):
    """Exact event-code mapping that can create candidates but cannot approve them."""

    schema_version: Literal[1] = 1
    rule_id: NonEmptyStr
    source_type: OperationalSourceType
    event_code: NonEmptyStr
    category: NonEmptyStr
    statement: NonEmptyStr


class OperationalInterpretationCandidate(ContractModel):
    """Reviewable interpretation candidate bound to one immutable raw record."""

    schema_version: Literal[1] = 1
    candidate_id: NonEmptyStr
    rule_id: NonEmptyStr
    record_id: NonEmptyStr
    raw_record_sha256: Sha256
    source_revision: NonEmptyStr
    source_artifact_sha256: Sha256
    adapter_config_sha256: Sha256
    category: NonEmptyStr
    statement: NonEmptyStr
    interpreter_id: NonEmptyStr
    interpreter_version: NonEmptyStr
    interpreter_config_sha256: Sha256
    interpreted_at: AwareDatetime
    review_state: Literal["candidate"] = "candidate"
    authority_state: Literal["no_operational_authority"] = "no_operational_authority"

    def content_sha256(self) -> Sha256:
        digest = hashlib.sha256(self.model_dump_json().encode("utf-8")).hexdigest()
        return f"sha256:{digest}"


class OperationalInterpretationReview(ContractModel):
    """Externally authored review of an interpretation, never of operational permission."""

    schema_version: Literal[1] = 1
    review_id: NonEmptyStr
    candidate_id: NonEmptyStr
    candidate_sha256: Sha256
    decision: OperationalReviewDecision
    reviewer_id: NonEmptyStr
    reviewer_role: NonEmptyStr
    reviewer_authority_ref: NonEmptyStr
    reviewed_at: AwareDatetime
    rationale: NonEmptyStr
    corrected_statement: NonEmptyStr | None = None
    supersedes_review_id: NonEmptyStr | None = None
    authority_state: Literal["review_record_only"] = "review_record_only"
    operational_authority: Literal["none"] = "none"

    @model_validator(mode="after")
    def require_correction_and_retraction_lineage(self) -> Self:
        if (
            self.decision is OperationalReviewDecision.CORRECTED_INTERPRETATION
            and self.corrected_statement is None
        ):
            raise ValueError("corrected interpretation requires corrected_statement")
        if (
            self.decision is OperationalReviewDecision.RETRACTED_INTERPRETATION
            and self.supersedes_review_id is None
        ):
            raise ValueError("retracted interpretation requires supersedes_review_id")
        return self


class OperationalReviewLedger(ContractModel):
    """Immutable candidate and external-review lineage with exact content binding."""

    schema_version: Literal[1] = 1
    candidates: tuple[OperationalInterpretationCandidate, ...]
    reviews: tuple[OperationalInterpretationReview, ...]
    authority_state: Literal["evidence_review_only"] = "evidence_review_only"
    operational_authority: Literal["none"] = "none"

    @model_validator(mode="after")
    def enforce_review_lineage(self) -> Self:
        candidate_ids = [item.candidate_id for item in self.candidates]
        review_ids = [item.review_id for item in self.reviews]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("duplicate candidate_id")
        if len(review_ids) != len(set(review_ids)):
            raise ValueError("duplicate review_id")
        candidates = {item.candidate_id: item for item in self.candidates}
        reviews = {item.review_id: item for item in self.reviews}
        for review in self.reviews:
            candidate = candidates.get(review.candidate_id)
            if candidate is None:
                raise ValueError(f"review {review.review_id} references unknown candidate")
            if review.candidate_sha256 != candidate.content_sha256():
                raise ValueError(f"review {review.review_id} candidate_sha256 does not match")
            if review.supersedes_review_id is not None:
                prior = reviews.get(review.supersedes_review_id)
                if prior is None:
                    raise ValueError(f"review {review.review_id} supersedes unknown review")
                if prior.review_id == review.review_id:
                    raise ValueError(f"review {review.review_id} cannot supersede itself")
                if prior.candidate_id != review.candidate_id:
                    raise ValueError("a review can supersede only a review of the same candidate")
        return self


class OperationalChangeImpact(ContractModel):
    """Deterministic evidence that a candidate/review lineage is current or stale."""

    schema_version: Literal[1] = 1
    candidate_id: NonEmptyStr
    state: OperationalImpactState
    prior_source_revision: NonEmptyStr
    current_source_revision: NonEmptyStr
    prior_source_artifact_sha256: Sha256
    current_source_artifact_sha256: Sha256
    prior_adapter_config_sha256: Sha256
    current_adapter_config_sha256: Sha256
    prior_record_sha256: Sha256
    current_record_sha256: Sha256 | None
    affected_review_ids: tuple[NonEmptyStr, ...] = ()
    authority_state: Literal["change_evidence_only"] = "change_evidence_only"
    operational_authority: Literal["none"] = "none"


class OperationalImpactReport(ContractModel):
    """Portable change-impact report bound to an exact ledger and current source batch."""

    schema_version: Literal[1] = 1
    review_ledger_sha256: Sha256
    current_batch_id: NonEmptyStr
    current_source_revision: NonEmptyStr
    current_source_artifact_sha256: Sha256
    current_adapter_config_sha256: Sha256
    impacts: tuple[OperationalChangeImpact, ...]
    authority_state: Literal["change_evidence_only"] = "change_evidence_only"
    operational_authority: Literal["none"] = "none"


class RegulatorySourceEvidence(ContractModel):
    """Exact official-source bytes used by a regulatory reconciliation candidate."""

    schema_version: Literal[1] = 1
    evidence_id: NonEmptyStr
    role: RegulatoryEvidenceRole
    authority: NonEmptyStr
    citation: NonEmptyStr
    package_id: NonEmptyStr
    source_url: NonEmptyStr
    artifact_sha256: Sha256
    byte_count: Annotated[StrictInt, Field(gt=0)]
    section_citations: tuple[NonEmptyStr, ...]
    retrieved_at: AwareDatetime
    content_treatment: Literal["untrusted_source_bytes"] = "untrusted_source_bytes"

    @model_validator(mode="after")
    def require_official_source_host(self) -> Self:
        if not self.section_citations:
            raise ValueError("regulatory evidence requires an exact section citation")
        allowed_hosts = {
            RegulatoryEvidenceRole.ANNUAL_CFR_BASELINE: {"govinfo.gov", "www.govinfo.gov"},
            RegulatoryEvidenceRole.ECFR_POINT_IN_TIME: {"ecfr.gov", "www.ecfr.gov"},
            RegulatoryEvidenceRole.FEDERAL_REGISTER_CHANGE: {
                "federalregister.gov",
                "www.federalregister.gov",
                "govinfo.gov",
                "www.govinfo.gov",
            },
            RegulatoryEvidenceRole.LSA_CHANGE_INDEX: {"govinfo.gov", "www.govinfo.gov"},
        }
        parsed = urlparse(self.source_url)
        if parsed.scheme != "https" or parsed.hostname not in allowed_hosts[self.role]:
            raise ValueError("regulatory evidence URL must use the official host for its role")
        return self


class RegulatoryArtifactVerification(ContractModel):
    """Integrity result for exact regulatory artifact bytes under a controlled local root."""

    schema_version: Literal[1] = 1
    evidence_id: NonEmptyStr
    artifact_ref: NonEmptyStr
    artifact_sha256: Sha256
    byte_count: Annotated[StrictInt, Field(gt=0)]
    integrity_state: Literal["integrity_verified"] = "integrity_verified"
    content_treatment: Literal["untrusted_source_bytes"] = "untrusted_source_bytes"
    operational_authority: Literal["none"] = "none"


class RegulatorySectionSnapshot(ContractModel):
    """Deterministic source-text extraction candidate bound to exact regulatory bytes."""

    schema_version: Literal[1] = 1
    evidence_id: NonEmptyStr
    evidence_role: RegulatoryEvidenceRole
    artifact_ref: NonEmptyStr
    source_artifact_sha256: Sha256
    citation: NonEmptyStr
    source_locator: NonEmptyStr
    heading: NonEmptyStr
    normalized_text: NonEmptyStr
    normalized_text_sha256: Sha256
    parser_identity: Literal["stdlib-elementtree-cfr-section"] = "stdlib-elementtree-cfr-section"
    parser_version: Literal[1] = 1
    parser_config_sha256: Sha256
    extraction_state: Literal["source_extraction_candidate"] = "source_extraction_candidate"
    interpretation_authority: Literal["none"] = "none"
    applicability_authority: Literal["none"] = "none"
    compliance_authority: Literal["none"] = "none"
    operational_authority: Literal["none"] = "none"


class RegulatorySectionComparison(ContractModel):
    """Conservative source-text comparison evidence for annual CFR and dated eCFR sections."""

    schema_version: Literal[1] = 1
    comparison_id: NonEmptyStr
    citation: NonEmptyStr
    annual_evidence_id: NonEmptyStr
    annual_artifact_sha256: Sha256
    annual_text_sha256: Sha256
    ecfr_evidence_id: NonEmptyStr
    ecfr_artifact_sha256: Sha256
    ecfr_text_sha256: Sha256
    evidence_ids: tuple[NonEmptyStr, NonEmptyStr]
    status: Literal["verified_match", "unresolved_difference"]
    rationale: NonEmptyStr
    authority_state: Literal["reconciliation_evidence_only"] = "reconciliation_evidence_only"
    interpretation_authority: Literal["none"] = "none"
    applicability_authority: Literal["none"] = "none"
    compliance_authority: Literal["none"] = "none"
    operational_authority: Literal["none"] = "none"


class FederalRegisterChangeCandidate(ContractModel):
    """Candidate extraction of one Federal Register change instruction."""

    schema_version: Literal[1] = 1
    candidate_id: NonEmptyStr
    evidence_id: NonEmptyStr
    evidence_role: Literal[RegulatoryEvidenceRole.FEDERAL_REGISTER_CHANGE] = (
        RegulatoryEvidenceRole.FEDERAL_REGISTER_CHANGE
    )
    source_artifact_sha256: Sha256
    document_number: NonEmptyStr
    publication_date: date
    effective_date: date | None
    federal_register_start_page: Annotated[StrictInt, Field(gt=0)] | None = None
    related_document_number: NonEmptyStr | None = None
    action: FederalRegisterAction
    affected_citations: tuple[NonEmptyStr, ...]
    source_locator: NonEmptyStr
    raw_instruction: NonEmptyStr
    raw_instruction_sha256: Sha256
    parser_identity: NonEmptyStr = "federal-register-change-candidate"
    parser_version: Literal[1] = 1
    parser_config_sha256: Sha256
    extraction_state: Literal["source_extraction_candidate"] = "source_extraction_candidate"
    interpretation_authority: Literal["none"] = "none"
    applicability_authority: Literal["none"] = "none"
    compliance_authority: Literal["none"] = "none"
    operational_authority: Literal["none"] = "none"

    @model_validator(mode="after")
    def verify_raw_instruction_hash(self) -> Self:
        if not self.affected_citations:
            raise ValueError("Federal Register candidate requires an affected citation")
        digest = "sha256:" + hashlib.sha256(self.raw_instruction.encode("utf-8")).hexdigest()
        if digest != self.raw_instruction_sha256:
            raise ValueError("raw instruction hash mismatch")
        return self


class FederalRegisterChangeChain(ContractModel):
    """Deterministic publication lineage without legal or semantic interpretation."""

    schema_version: Literal[1] = 1
    chain_id: NonEmptyStr
    citation: NonEmptyStr
    candidates: tuple[FederalRegisterChangeCandidate, ...]
    chain_state: Literal["effective_date_established", "withdrawn", "unsupported_chain"]
    controlling_effective_date: date | None
    unresolved_reasons: tuple[NonEmptyStr, ...] = ()
    authority_state: Literal["source_change_lineage_only"] = "source_change_lineage_only"
    interpretation_authority: Literal["none"] = "none"
    applicability_authority: Literal["none"] = "none"
    compliance_authority: Literal["none"] = "none"
    operational_authority: Literal["none"] = "none"


class LsaCoverageCandidate(ContractModel):
    """Candidate extraction of LSA coverage for one exact CFR citation."""

    schema_version: Literal[1] = 1
    candidate_id: NonEmptyStr
    evidence_id: NonEmptyStr
    evidence_role: Literal[RegulatoryEvidenceRole.LSA_CHANGE_INDEX] = (
        RegulatoryEvidenceRole.LSA_CHANGE_INDEX
    )
    source_artifact_sha256: Sha256
    through_date: date
    citation: NonEmptyStr
    status_text: NonEmptyStr | None = None
    federal_register_pages: tuple[Annotated[StrictInt, Field(gt=0)], ...] = ()
    federal_register_document_numbers: tuple[NonEmptyStr, ...] = ()
    source_locator: NonEmptyStr
    raw_entry: NonEmptyStr
    raw_entry_sha256: Sha256
    parser_identity: NonEmptyStr = "lsa-coverage-candidate"
    parser_version: Literal[1] = 1
    parser_config_sha256: Sha256
    extraction_state: Literal["source_extraction_candidate"] = "source_extraction_candidate"
    interpretation_authority: Literal["none"] = "none"
    applicability_authority: Literal["none"] = "none"
    compliance_authority: Literal["none"] = "none"
    operational_authority: Literal["none"] = "none"

    @model_validator(mode="after")
    def verify_raw_entry_hash(self) -> Self:
        if not self.federal_register_pages and not self.federal_register_document_numbers:
            raise ValueError("LSA candidate requires a Federal Register page or document number")
        digest = "sha256:" + hashlib.sha256(self.raw_entry.encode("utf-8")).hexdigest()
        if digest != self.raw_entry_sha256:
            raise ValueError("raw LSA entry hash mismatch")
        return self


class RegulatoryChangeEvidenceBundle(ContractModel):
    """Exact change evidence collected for an unresolved section difference."""

    schema_version: Literal[1] = 1
    bundle_id: NonEmptyStr
    comparison: RegulatorySectionComparison
    comparison_sha256: Sha256
    amendments: tuple[FederalRegisterChangeCandidate, ...]
    lsa_coverage: LsaCoverageCandidate
    ecfr_as_of: date
    generated_at: AwareDatetime
    bundle_state: Literal["requires_authorized_source_review"] = "requires_authorized_source_review"
    authority_state: Literal["change_evidence_only"] = "change_evidence_only"
    interpretation_authority: Literal["none"] = "none"
    applicability_authority: Literal["none"] = "none"
    compliance_authority: Literal["none"] = "none"
    operational_authority: Literal["none"] = "none"


class RegulatoryDifferenceReview(ContractModel):
    """External source-only review of one exact official-change evidence bundle."""

    schema_version: Literal[1] = 1
    review_id: NonEmptyStr
    bundle_id: NonEmptyStr
    bundle_sha256: Sha256
    decision: RegulatoryDifferenceReviewDecision
    reviewer_id: NonEmptyStr
    reviewer_role: NonEmptyStr
    reviewer_authority_ref: NonEmptyStr
    reviewed_at: AwareDatetime
    rationale: NonEmptyStr
    authority_state: Literal["source_review_only"] = "source_review_only"
    interpretation_authority: Literal["none"] = "none"
    applicability_authority: Literal["none"] = "none"
    compliance_authority: Literal["none"] = "none"
    operational_authority: Literal["none"] = "none"


class RegulatoryReconciliationFinding(ContractModel):
    """A deterministic section-level source comparison outcome."""

    schema_version: Literal[1] = 1
    finding_id: NonEmptyStr
    citation: NonEmptyStr
    status: RegulatoryReconciliationStatus
    evidence_ids: tuple[NonEmptyStr, ...]
    statement: NonEmptyStr
    authority_state: Literal["source_comparison_only"] = "source_comparison_only"


class ReviewedRegulatoryDifference(ContractModel):
    """Externally reviewed source explanation preserving exact bundle and finding lineage."""

    schema_version: Literal[1] = 1
    bundle_id: NonEmptyStr
    bundle_sha256: Sha256
    review_id: NonEmptyStr
    reviewer_id: NonEmptyStr
    reviewed_at: AwareDatetime
    finding: RegulatoryReconciliationFinding
    authority_state: Literal["reviewed_source_explanation_only"] = (
        "reviewed_source_explanation_only"
    )
    interpretation_authority: Literal["none"] = "none"
    applicability_authority: Literal["none"] = "none"
    compliance_authority: Literal["none"] = "none"
    operational_authority: Literal["none"] = "none"


class RegulatorySourceVerificationCandidate(ContractModel):
    """Candidate verification of source bytes, never interpretation or applicability."""

    schema_version: Literal[1] = 1
    candidate_id: NonEmptyStr
    jurisdiction: NonEmptyStr
    citation: NonEmptyStr
    annual_cfr_edition: StrictInt
    ecfr_as_of: date
    evidence: tuple[RegulatorySourceEvidence, ...]
    findings: tuple[RegulatoryReconciliationFinding, ...]
    reconciler_id: NonEmptyStr
    reconciler_version: NonEmptyStr
    reconciler_config_sha256: Sha256
    generated_at: AwareDatetime
    source_state: Literal["verification_candidate"] = "verification_candidate"
    interpretation_state: Literal["not_approved"] = "not_approved"
    applicability_state: Literal["undetermined"] = "undetermined"
    compliance_state: Literal["no_conclusion"] = "no_conclusion"
    operational_authority: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_evidence_bundle(self) -> Self:
        required_roles = set(RegulatoryEvidenceRole)
        if {item.role for item in self.evidence} != required_roles:
            raise ValueError("candidate must include all required official evidence roles")
        if len(self.evidence) != len(required_roles):
            raise ValueError("candidate must include exactly one source per official evidence role")
        evidence_ids = [item.evidence_id for item in self.evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("regulatory evidence IDs must be unique")
        known_ids = set(evidence_ids)
        for finding in self.findings:
            if not set(finding.evidence_ids) <= known_ids:
                raise ValueError("reconciliation finding references unknown evidence")
        return self


class RegulatorySourceVerificationReview(ContractModel):
    """External review of source reconciliation, without interpretation authority."""

    schema_version: Literal[1] = 1
    review_id: NonEmptyStr
    candidate_id: NonEmptyStr
    candidate_sha256: Sha256
    decision: RegulatorySourceReviewDecision
    reviewer_id: NonEmptyStr
    reviewer_role: NonEmptyStr
    reviewer_authority_ref: NonEmptyStr
    reviewed_at: AwareDatetime
    rationale: NonEmptyStr
    authority_state: Literal["source_review_only"] = "source_review_only"
    interpretation_authority: Literal["none"] = "none"
    applicability_authority: Literal["none"] = "none"
    compliance_authority: Literal["none"] = "none"
    operational_authority: Literal["none"] = "none"


class VerifiedRegulatorySource(ContractModel):
    """Externally reviewed verification of an exact regulatory source revision."""

    schema_version: Literal[1] = 1
    verification_candidate_id: NonEmptyStr
    verification_candidate_sha256: Sha256
    source_review_id: NonEmptyStr
    reviewer_id: NonEmptyStr
    reviewed_at: AwareDatetime
    jurisdiction: NonEmptyStr
    citation: NonEmptyStr
    annual_cfr_edition: StrictInt
    ecfr_as_of: date
    evidence: tuple[RegulatorySourceEvidence, ...]
    findings: tuple[RegulatoryReconciliationFinding, ...]
    source_state: Literal["verified_regulatory_source"] = "verified_regulatory_source"
    interpretation_state: Literal["not_approved"] = "not_approved"
    applicability_state: Literal["undetermined"] = "undetermined"
    constraint_state: Literal["not_approved"] = "not_approved"
    compliance_state: Literal["no_conclusion"] = "no_conclusion"
    operational_authority: Literal["none"] = "none"


class RegulatorySourceEvidenceImpact(ContractModel):
    """Change evidence for one exact official-source role in a verified revision."""

    schema_version: Literal[1] = 1
    role: RegulatoryEvidenceRole
    prior_evidence_id: NonEmptyStr
    prior_package_id: NonEmptyStr
    prior_artifact_sha256: Sha256
    current_evidence_id: NonEmptyStr | None
    current_package_id: NonEmptyStr | None
    current_artifact_sha256: Sha256 | None
    state: Literal["current", "stale"]
    reasons: tuple[
        Literal["artifact_changed", "as_of_changed", "evidence_missing", "package_changed"],
        ...,
    ]
    affected_review_ids: tuple[NonEmptyStr, ...]
    authority_state: Literal["change_evidence_only"] = "change_evidence_only"
    interpretation_authority: Literal["none"] = "none"
    applicability_authority: Literal["none"] = "none"
    compliance_authority: Literal["none"] = "none"
    operational_authority: Literal["none"] = "none"


class RegulatorySourceImpactReport(ContractModel):
    """Staleness report for an exact externally reviewed regulatory source revision."""

    schema_version: Literal[1] = 1
    verification_candidate_id: NonEmptyStr
    verification_candidate_sha256: Sha256
    source_review_id: NonEmptyStr
    prior_ecfr_as_of: date
    current_ecfr_as_of: date
    impacts: tuple[RegulatorySourceEvidenceImpact, ...]
    source_state: Literal["verified_regulatory_source", "source_verification_stale"]
    authority_state: Literal["change_evidence_only"] = "change_evidence_only"
    interpretation_authority: Literal["none"] = "none"
    applicability_authority: Literal["none"] = "none"
    compliance_authority: Literal["none"] = "none"
    operational_authority: Literal["none"] = "none"


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


class SafetyEvidencePacketContext(ContractModel):
    """Exact asset/task context and explicit unknowns for one reviewable packet."""

    jurisdiction: NonEmptyStr | None = None
    site: NonEmptyStr | None = None
    asset_model: NonEmptyStr
    asset_serial: NonEmptyStr | None = None
    task_id: NonEmptyStr
    task_phase: NonEmptyStr | None = None
    role: NonEmptyStr | None = None
    applicability_unknowns: tuple[NonEmptyStr, ...] = ()


class SafetyEvidenceIssue(ContractModel):
    """One unresolved, cited evidence condition; never an automated safety conclusion."""

    issue_id: NonEmptyStr
    state: FindingState
    statement: NonEmptyStr
    related_source_ids: tuple[NonEmptyStr, ...] = ()
    related_constraint_ids: tuple[NonEmptyStr, ...] = ()

    @model_validator(mode="after")
    def reject_resolved_state(self) -> Self:
        if self.state is FindingState.MATCHED:
            raise ValueError("unresolved evidence cannot use matched state")
        return self


class SafetyEvidencePacket(ContractModel):
    """Frozen v1 review packet for one exact context, with no compliance or physical authority."""

    schema_version: Literal[1] = 1
    packet_id: NonEmptyStr
    packet_revision: NonEmptyStr
    context: SafetyEvidencePacketContext
    memory: SafetyMemoryPacket
    unresolved_evidence: tuple[SafetyEvidenceIssue, ...] = ()
    packet_config_sha256: Sha256
    generated_at: AwareDatetime
    packet_state: Literal["reviewable_evidence_packet"] = "reviewable_evidence_packet"
    interpretation_authority: Literal["none"] = "none"
    applicability_authority: Literal["none"] = "none"
    compliance_state: Literal["no_conclusion"] = "no_conclusion"
    operational_authority: Literal["none"] = "none"

    @model_validator(mode="after")
    def enforce_exact_packet_references(self) -> Self:
        if self.packet_id != self.memory.packet_id:
            raise ValueError("packet_id must match exact safety memory packet")
        issue_ids = [item.issue_id for item in self.unresolved_evidence]
        if len(issue_ids) != len(set(issue_ids)):
            raise ValueError("duplicate evidence issue_id")
        source_ids = {item.source_id for item in self.memory.sources}
        constraint_ids = {item.constraint_id for item in self.memory.constraints}
        for issue in self.unresolved_evidence:
            unknown_sources = set(issue.related_source_ids) - source_ids
            if unknown_sources:
                raise ValueError(
                    f"evidence issue references unknown source: {sorted(unknown_sources)}"
                )
            unknown_constraints = set(issue.related_constraint_ids) - constraint_ids
            if unknown_constraints:
                raise ValueError(
                    f"evidence issue references unknown constraint: {sorted(unknown_constraints)}"
                )
        return self

    def content_sha256(self) -> Sha256:
        digest = hashlib.sha256(self.model_dump_json().encode("utf-8")).hexdigest()
        return f"sha256:{digest}"


class PhysicalIntelligenceEvidenceEnvelope(ContractModel):
    """Portable identity and provenance for one read-only platform artifact."""

    schema_version: Literal[1] = 1
    platform_id: NonEmptyStr
    platform_version: NonEmptyStr
    adapter_id: NonEmptyStr
    adapter_version: NonEmptyStr
    adapter_config_sha256: Sha256
    artifact_type: NonEmptyStr
    source_ref: NonEmptyStr
    source_revision: NonEmptyStr
    content_sha256: Sha256
    observed_at: AwareDatetime
    asset_ids: tuple[NonEmptyStr, ...] = ()
    task_id: NonEmptyStr | None = None
    run_id: NonEmptyStr | None = None
    episode_id: NonEmptyStr | None = None
    simulation_id: NonEmptyStr | None = None
    provenance_refs: tuple[NonEmptyStr, ...] = ()
    payload_ref: NonEmptyStr
    missing_fields: tuple[NonEmptyStr, ...] = ()
    unsupported_fields: tuple[NonEmptyStr, ...] = ()
    access_mode: Literal["read_only"] = "read_only"
    content_treatment: Literal["untrusted_data"] = "untrusted_data"

    @model_validator(mode="after")
    def require_disjoint_field_accounting(self) -> Self:
        overlap = set(self.missing_fields) & set(self.unsupported_fields)
        if overlap:
            raise ValueError("a field cannot be both missing and unsupported")
        if len(self.provenance_refs) != len(set(self.provenance_refs)):
            raise ValueError("duplicate provenance_refs")
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


class EvidenceEnvelopeBinding(ContractModel):
    platform_id: NonEmptyStr
    platform_version: NonEmptyStr
    adapter_id: NonEmptyStr
    adapter_version: NonEmptyStr
    adapter_config_sha256: Sha256
    artifact_type: NonEmptyStr
    source_ref: NonEmptyStr
    source_revision: NonEmptyStr
    content_sha256: Sha256
    observed_at: AwareDatetime
    task_id: NonEmptyStr


class AuditReport(ContractModel):
    schema_version: Literal[2] = 2
    packet_id: str
    plan_id: str
    policy_sha256: Sha256
    envelope: EvidenceEnvelopeBinding
    findings: tuple[AuditFinding, ...]
