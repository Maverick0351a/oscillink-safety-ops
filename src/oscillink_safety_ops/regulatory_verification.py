"""Exact regulatory-source verification and externally reviewed promotion."""

from __future__ import annotations

import hashlib

from .domain import (
    RegulatoryReconciliationStatus,
    RegulatorySourceReviewDecision,
    RegulatorySourceVerificationCandidate,
    RegulatorySourceVerificationReview,
    VerifiedRegulatorySource,
)


def regulatory_candidate_sha256(candidate: RegulatorySourceVerificationCandidate) -> str:
    """Hash one exact, canonical regulatory source-verification candidate."""
    payload = candidate.model_dump_json().encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def promote_verified_regulatory_source(
    candidate: RegulatorySourceVerificationCandidate,
    review: RegulatorySourceVerificationReview,
) -> VerifiedRegulatorySource:
    """Promote exact source bytes only; never promote interpretation or applicability."""
    candidate_sha256 = regulatory_candidate_sha256(candidate)
    if review.candidate_id != candidate.candidate_id:
        raise ValueError("source review references a different verification candidate")
    if review.candidate_sha256 != candidate_sha256:
        raise ValueError("source review candidate hash mismatch")
    if review.decision is not RegulatorySourceReviewDecision.PROMOTE_VERIFIED_REGULATORY_SOURCE:
        raise ValueError("source review does not authorize source verification promotion")
    allowed_findings = {
        RegulatoryReconciliationStatus.VERIFIED_MATCH,
        RegulatoryReconciliationStatus.EXPLAINED_OFFICIAL_CHANGE,
    }
    if not candidate.findings or any(
        finding.status not in allowed_findings for finding in candidate.findings
    ):
        raise ValueError("unresolved or missing reconciliation evidence blocks source promotion")
    finding_evidence_ids = {
        evidence_id for finding in candidate.findings for evidence_id in finding.evidence_ids
    }
    if finding_evidence_ids != {item.evidence_id for item in candidate.evidence}:
        raise ValueError("source promotion requires findings covering all required evidence")
    return VerifiedRegulatorySource(
        verification_candidate_id=candidate.candidate_id,
        verification_candidate_sha256=candidate_sha256,
        source_review_id=review.review_id,
        reviewer_id=review.reviewer_id,
        reviewed_at=review.reviewed_at,
        jurisdiction=candidate.jurisdiction,
        citation=candidate.citation,
        annual_cfr_edition=candidate.annual_cfr_edition,
        ecfr_as_of=candidate.ecfr_as_of,
        evidence=candidate.evidence,
        findings=candidate.findings,
    )
