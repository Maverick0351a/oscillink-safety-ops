"""Exact regulatory-source verification and externally reviewed promotion."""

from __future__ import annotations

import hashlib
from datetime import date
from typing import Literal

from .domain import (
    RegulatoryEvidenceRole,
    RegulatoryReconciliationStatus,
    RegulatorySourceEvidence,
    RegulatorySourceEvidenceImpact,
    RegulatorySourceImpactReport,
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


def assess_verified_regulatory_source_impact(
    verified: VerifiedRegulatorySource,
    *,
    current_evidence: tuple[RegulatorySourceEvidence, ...],
    current_ecfr_as_of: date,
) -> RegulatorySourceImpactReport:
    """Compare current official bytes with one exact externally reviewed source revision."""
    current_roles = [item.role for item in current_evidence]
    if len(current_roles) != len(set(current_roles)):
        raise ValueError("duplicate current regulatory evidence role")
    current_by_role = {item.role: item for item in current_evidence}
    impacts: list[RegulatorySourceEvidenceImpact] = []
    for prior in verified.evidence:
        current = current_by_role.get(prior.role)
        reasons: tuple[
            Literal["artifact_changed", "as_of_changed", "evidence_missing", "package_changed"],
            ...,
        ]
        if current is None:
            reasons = ("evidence_missing",)
        else:
            reason_list: list[
                Literal["artifact_changed", "as_of_changed", "evidence_missing", "package_changed"]
            ] = []
            if current.artifact_sha256 != prior.artifact_sha256:
                reason_list.append("artifact_changed")
            if current.package_id != prior.package_id:
                reason_list.append("package_changed")
            if (
                prior.role is RegulatoryEvidenceRole.ECFR_POINT_IN_TIME
                and current_ecfr_as_of != verified.ecfr_as_of
            ):
                reason_list.append("as_of_changed")
            reasons = tuple(reason_list)
        impacts.append(
            RegulatorySourceEvidenceImpact(
                role=prior.role,
                prior_evidence_id=prior.evidence_id,
                prior_package_id=prior.package_id,
                prior_artifact_sha256=prior.artifact_sha256,
                current_evidence_id=current.evidence_id if current else None,
                current_package_id=current.package_id if current else None,
                current_artifact_sha256=current.artifact_sha256 if current else None,
                state="stale" if reasons else "current",
                reasons=reasons,
                affected_review_ids=(verified.source_review_id,) if reasons else (),
            )
        )
    source_state: Literal["verified_regulatory_source", "source_verification_stale"] = (
        "source_verification_stale"
        if any(impact.state == "stale" for impact in impacts)
        else "verified_regulatory_source"
    )
    return RegulatorySourceImpactReport(
        verification_candidate_id=verified.verification_candidate_id,
        verification_candidate_sha256=verified.verification_candidate_sha256,
        source_review_id=verified.source_review_id,
        prior_ecfr_as_of=verified.ecfr_as_of,
        current_ecfr_as_of=current_ecfr_as_of,
        impacts=tuple(impacts),
        source_state=source_state,
    )
