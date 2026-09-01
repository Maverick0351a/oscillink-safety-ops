from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from oscillink_safety_ops.domain import (
    RegulatoryEvidenceRole,
    RegulatoryReconciliationFinding,
    RegulatoryReconciliationStatus,
    RegulatorySourceEvidence,
    RegulatorySourceReviewDecision,
    RegulatorySourceVerificationCandidate,
    RegulatorySourceVerificationReview,
)
from oscillink_safety_ops.regulatory_verification import (
    promote_verified_regulatory_source,
    regulatory_candidate_sha256,
)
from scripts.export_schemas import SCHEMAS

SHA_A = "sha256:" + "a" * 64
SHA_B = "sha256:" + "b" * 64
SHA_C = "sha256:" + "c" * 64
SHA_D = "sha256:" + "d" * 64
NOW = datetime(2026, 8, 31, tzinfo=UTC)


def evidence(
    *, role: RegulatoryEvidenceRole, evidence_id: str, sha256: str
) -> RegulatorySourceEvidence:
    source = {
        RegulatoryEvidenceRole.ANNUAL_CFR_BASELINE: (
            "govinfo:CFR-2025-title29-vol5",
            "https://www.govinfo.gov/app/details/CFR-2025-title29-vol5",
        ),
        RegulatoryEvidenceRole.ECFR_POINT_IN_TIME: (
            "ecfr:2026-08-27:title29:part1910",
            "https://www.ecfr.gov/api/versioner/v1/full/2026-08-27/title-29.xml?part=1910",
        ),
        RegulatoryEvidenceRole.FEDERAL_REGISTER_CHANGE: (
            "federal-register:2026-search-title29-part1910",
            "https://www.federalregister.gov/documents/search?conditions%5Bcfr%5D%5Btitle%5D=29",
        ),
        RegulatoryEvidenceRole.LSA_CHANGE_INDEX: (
            "govinfo:LSA-2026-08",
            "https://www.govinfo.gov/app/collection/lsa/2026/08",
        ),
    }[role]
    return RegulatorySourceEvidence(
        evidence_id=evidence_id,
        role=role,
        authority="United States Government",
        citation="29 CFR 1910.147",
        package_id=source[0],
        source_url=source[1],
        artifact_sha256=sha256,
        byte_count=100,
        section_citations=("29 CFR 1910.147",),
        retrieved_at=NOW,
    )


def reconciled_candidate() -> RegulatorySourceVerificationCandidate:
    sources = (
        evidence(
            role=RegulatoryEvidenceRole.ANNUAL_CFR_BASELINE,
            evidence_id="evidence:annual-cfr",
            sha256=SHA_A,
        ),
        evidence(
            role=RegulatoryEvidenceRole.ECFR_POINT_IN_TIME,
            evidence_id="evidence:ecfr",
            sha256=SHA_B,
        ),
        evidence(
            role=RegulatoryEvidenceRole.FEDERAL_REGISTER_CHANGE,
            evidence_id="evidence:federal-register",
            sha256=SHA_C,
        ),
        evidence(
            role=RegulatoryEvidenceRole.LSA_CHANGE_INDEX,
            evidence_id="evidence:lsa",
            sha256=SHA_D,
        ),
    )
    return RegulatorySourceVerificationCandidate(
        candidate_id="reg-source-candidate:29-cfr-1910-147:2026-08-27",
        jurisdiction="US-federal",
        citation="29 CFR 1910.147",
        annual_cfr_edition=2025,
        ecfr_as_of=date(2026, 8, 27),
        evidence=sources,
        findings=(
            RegulatoryReconciliationFinding(
                finding_id="reg-finding:29-cfr-1910-147:match",
                citation="29 CFR 1910.147",
                status=RegulatoryReconciliationStatus.VERIFIED_MATCH,
                evidence_ids=tuple(source.evidence_id for source in sources),
                statement="Synthetic sources reconcile for contract testing.",
            ),
        ),
        reconciler_id="reconciler:synthetic-section-diff",
        reconciler_version="1.0.0",
        reconciler_config_sha256=SHA_A,
        generated_at=NOW,
    )


def test_verification_candidate_requires_all_four_official_evidence_roles() -> None:
    candidate = reconciled_candidate()

    assert candidate.source_state == "verification_candidate"
    assert candidate.interpretation_state == "not_approved"
    assert candidate.applicability_state == "undetermined"
    assert candidate.compliance_state == "no_conclusion"
    assert candidate.operational_authority == "none"

    with pytest.raises(ValidationError, match="required official evidence roles"):
        candidate.model_copy(update={"evidence": candidate.evidence[:-1]}).model_dump()
        RegulatorySourceVerificationCandidate.model_validate(
            {**candidate.model_dump(), "evidence": candidate.evidence[:-1]}
        )


def test_regulatory_evidence_role_rejects_nonofficial_source_host() -> None:
    item = evidence(
        role=RegulatoryEvidenceRole.ANNUAL_CFR_BASELINE,
        evidence_id="evidence:annual-cfr",
        sha256=SHA_A,
    )

    with pytest.raises(ValidationError, match="official host"):
        RegulatorySourceEvidence.model_validate(
            {**item.model_dump(), "source_url": "https://example.com/cfr-2025.xml"}
        )


def test_regulatory_evidence_rejects_empty_source_artifacts() -> None:
    item = evidence(
        role=RegulatoryEvidenceRole.ECFR_POINT_IN_TIME,
        evidence_id="evidence:ecfr",
        sha256=SHA_B,
    )

    with pytest.raises(ValidationError, match="greater than 0"):
        RegulatorySourceEvidence.model_validate({**item.model_dump(), "byte_count": 0})


def test_regulatory_evidence_requires_an_exact_section_citation() -> None:
    item = evidence(
        role=RegulatoryEvidenceRole.LSA_CHANGE_INDEX,
        evidence_id="evidence:lsa",
        sha256=SHA_D,
    )

    with pytest.raises(ValidationError, match="section citation"):
        RegulatorySourceEvidence.model_validate({**item.model_dump(), "section_citations": ()})


def test_verification_candidate_requires_exactly_one_source_per_role() -> None:
    candidate = reconciled_candidate()
    duplicate = candidate.evidence[0].model_copy(update={"evidence_id": "evidence:annual-copy"})

    with pytest.raises(ValidationError, match="exactly one source per official evidence role"):
        RegulatorySourceVerificationCandidate.model_validate(
            {**candidate.model_dump(), "evidence": (*candidate.evidence, duplicate)}
        )


def source_review(
    candidate: RegulatorySourceVerificationCandidate,
) -> RegulatorySourceVerificationReview:
    return RegulatorySourceVerificationReview(
        review_id="reg-source-review:29-cfr-1910-147:2026-08-31",
        candidate_id=candidate.candidate_id,
        candidate_sha256=regulatory_candidate_sha256(candidate),
        decision=RegulatorySourceReviewDecision.PROMOTE_VERIFIED_REGULATORY_SOURCE,
        reviewer_id="reviewer:synthetic-regulatory-authority",
        reviewer_role="role:authorized-regulatory-source-reviewer",
        reviewer_authority_ref="authority:synthetic-review-matrix-v1",
        reviewed_at=NOW,
        rationale="Synthetic source-verification review for contract testing only.",
    )


def test_authorized_review_promotes_only_the_exact_regulatory_source_revision() -> None:
    candidate = reconciled_candidate()

    verified = promote_verified_regulatory_source(candidate, source_review(candidate))

    assert verified.verification_candidate_sha256 == regulatory_candidate_sha256(candidate)
    assert verified.source_state == "verified_regulatory_source"
    assert verified.interpretation_state == "not_approved"
    assert verified.applicability_state == "undetermined"
    assert verified.constraint_state == "not_approved"
    assert verified.compliance_state == "no_conclusion"
    assert verified.operational_authority == "none"


def test_unresolved_difference_blocks_source_promotion_even_after_review() -> None:
    candidate = reconciled_candidate()
    unresolved = RegulatorySourceVerificationCandidate.model_validate(
        {
            **candidate.model_dump(),
            "findings": (
                RegulatoryReconciliationFinding(
                    finding_id="reg-finding:29-cfr-1910-147:unresolved",
                    citation=candidate.citation,
                    status=RegulatoryReconciliationStatus.UNRESOLVED_DIFFERENCE,
                    evidence_ids=tuple(item.evidence_id for item in candidate.evidence),
                    statement="Synthetic unexplained section-level difference.",
                ),
            ),
        }
    )

    with pytest.raises(ValueError, match="unresolved or missing"):
        promote_verified_regulatory_source(unresolved, source_review(unresolved))


def test_source_review_cannot_promote_different_candidate_bytes() -> None:
    candidate = reconciled_candidate()
    review = source_review(candidate).model_copy(update={"candidate_sha256": SHA_D})

    with pytest.raises(ValueError, match="candidate hash mismatch"):
        promote_verified_regulatory_source(candidate, review)


def test_promotion_requires_findings_to_cover_all_official_evidence() -> None:
    candidate = reconciled_candidate()
    partial = RegulatorySourceVerificationCandidate.model_validate(
        {
            **candidate.model_dump(),
            "findings": (
                candidate.findings[0].model_copy(
                    update={"evidence_ids": ("evidence:annual-cfr", "evidence:ecfr")}
                ),
            ),
        }
    )

    with pytest.raises(ValueError, match="all required evidence"):
        promote_verified_regulatory_source(partial, source_review(partial))


def test_regulatory_source_schemas_preserve_source_only_authority() -> None:
    candidate = SCHEMAS["regulatory-source-verification-candidate.schema.json"]
    review = SCHEMAS["regulatory-source-verification-review.schema.json"]
    verified = SCHEMAS["verified-regulatory-source.schema.json"]

    assert candidate["properties"]["source_state"]["const"] == "verification_candidate"
    assert review["properties"]["interpretation_authority"]["const"] == "none"
    assert verified["properties"]["source_state"]["const"] == "verified_regulatory_source"
    assert verified["properties"]["interpretation_state"]["const"] == "not_approved"
    assert verified["properties"]["applicability_state"]["const"] == "undetermined"
    assert verified["properties"]["operational_authority"]["const"] == "none"
