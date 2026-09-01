"""Conservative official-change evidence collection for regulatory source review."""

from __future__ import annotations

import hashlib
from datetime import date, datetime

from .domain import (
    FederalRegisterAction,
    FederalRegisterChangeCandidate,
    LsaCoverageCandidate,
    RegulatoryChangeEvidenceBundle,
    RegulatoryDifferenceReview,
    RegulatoryDifferenceReviewDecision,
    RegulatoryReconciliationFinding,
    RegulatoryReconciliationStatus,
    RegulatorySectionComparison,
    ReviewedRegulatoryDifference,
)


def regulatory_section_comparison_sha256(comparison: RegulatorySectionComparison) -> str:
    """Hash one exact deterministic section-comparison record."""
    payload = comparison.model_dump_json().encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def regulatory_change_bundle_sha256(bundle: RegulatoryChangeEvidenceBundle) -> str:
    """Hash one exact official-change evidence bundle."""
    payload = bundle.model_dump_json().encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def build_regulatory_change_evidence_bundle(
    comparison: RegulatorySectionComparison,
    *,
    amendments: tuple[FederalRegisterChangeCandidate, ...],
    lsa_coverage: LsaCoverageCandidate,
    ecfr_as_of: date,
    generated_at: datetime,
) -> RegulatoryChangeEvidenceBundle:
    """Collect exact change candidates without claiming they explain a legal difference."""
    if comparison.status != "unresolved_difference":
        raise ValueError("change evidence requires an unresolved section comparison")
    if not amendments:
        raise ValueError("change evidence requires a Federal Register change candidate")
    if any(comparison.citation not in item.affected_citations for item in amendments):
        raise ValueError("Federal Register candidate does not cover the comparison citation")
    if lsa_coverage.citation != comparison.citation:
        raise ValueError("LSA candidate does not cover the comparison citation")
    amendment_documents = {item.document_number for item in amendments}
    if not amendment_documents <= set(lsa_coverage.federal_register_document_numbers):
        raise ValueError("LSA coverage is missing Federal Register document evidence")
    if any(item.effective_date is None or item.effective_date > ecfr_as_of for item in amendments):
        raise ValueError("Federal Register effective date is not established as of the eCFR date")
    if lsa_coverage.through_date < ecfr_as_of:
        raise ValueError("LSA coverage does not extend through the eCFR date")
    comparison_sha256 = regulatory_section_comparison_sha256(comparison)
    identity = hashlib.sha256(
        "\n".join(
            (
                comparison_sha256,
                *(item.candidate_id for item in amendments),
                lsa_coverage.candidate_id,
                ecfr_as_of.isoformat(),
            )
        ).encode("utf-8")
    ).hexdigest()
    return RegulatoryChangeEvidenceBundle(
        bundle_id=f"regulatory-change-bundle:{identity}",
        comparison=comparison,
        comparison_sha256=comparison_sha256,
        amendments=amendments,
        lsa_coverage=lsa_coverage,
        ecfr_as_of=ecfr_as_of,
        generated_at=generated_at,
    )


def record_reviewed_regulatory_difference(
    bundle: RegulatoryChangeEvidenceBundle,
    review: RegulatoryDifferenceReview,
) -> ReviewedRegulatoryDifference:
    """Record source-only external acceptance of an exact official-change evidence bundle."""
    bundle_sha256 = regulatory_change_bundle_sha256(bundle)
    if review.bundle_id != bundle.bundle_id:
        raise ValueError("difference review references a different change bundle")
    if review.bundle_sha256 != bundle_sha256:
        raise ValueError("difference review bundle hash mismatch")
    supported_actions = {
        FederalRegisterAction.AMEND,
        FederalRegisterAction.CORRECT,
        FederalRegisterAction.DELAY_EFFECTIVE_DATE,
        FederalRegisterAction.REDESIGNATE,
        FederalRegisterAction.REMOVE,
    }
    if any(item.action not in supported_actions for item in bundle.amendments):
        raise ValueError("unsupported Federal Register action blocks an explained finding")
    if review.decision is not RegulatoryDifferenceReviewDecision.ACCEPT_EXPLAINED_OFFICIAL_CHANGE:
        raise ValueError("difference review does not accept the official change explanation")
    evidence_ids = tuple(
        dict.fromkeys(
            (
                *bundle.comparison.evidence_ids,
                *(item.evidence_id for item in bundle.amendments),
                bundle.lsa_coverage.evidence_id,
            )
        )
    )
    finding_digest = hashlib.sha256(f"{bundle_sha256}\n{review.review_id}".encode()).hexdigest()
    finding = RegulatoryReconciliationFinding(
        finding_id=f"finding:sha256:{finding_digest}",
        citation=bundle.comparison.citation,
        status=RegulatoryReconciliationStatus.EXPLAINED_OFFICIAL_CHANGE,
        evidence_ids=evidence_ids,
        statement=(
            "An externally authorized source reviewer accepted the exact cited Federal Register "
            "and LSA evidence as an official source-change explanation; this grants no "
            "interpretation, applicability, compliance, or operational authority."
        ),
    )
    return ReviewedRegulatoryDifference(
        bundle_id=bundle.bundle_id,
        bundle_sha256=bundle_sha256,
        review_id=review.review_id,
        reviewer_id=review.reviewer_id,
        reviewed_at=review.reviewed_at,
        finding=finding,
    )
