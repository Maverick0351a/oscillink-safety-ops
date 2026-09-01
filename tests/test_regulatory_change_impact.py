from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from oscillink_safety_ops.domain import (
    RegulatoryEvidenceRole,
    RegulatoryReconciliationFinding,
    RegulatoryReconciliationStatus,
    RegulatorySourceEvidence,
    VerifiedRegulatorySource,
)
from oscillink_safety_ops.regulatory_verification import (
    assess_verified_regulatory_source_impact,
)

NOW = datetime(2026, 9, 1, tzinfo=UTC)
SHA_A = "sha256:" + "a" * 64
SHA_B = "sha256:" + "b" * 64
SHA_C = "sha256:" + "c" * 64
SHA_D = "sha256:" + "d" * 64
SHA_E = "sha256:" + "e" * 64


def source(
    role: RegulatoryEvidenceRole,
    evidence_id: str,
    sha256: str,
    *,
    package_id: str | None = None,
) -> RegulatorySourceEvidence:
    urls = {
        RegulatoryEvidenceRole.ANNUAL_CFR_BASELINE: "https://www.govinfo.gov/app/details/CFR-2025-title29-vol5",
        RegulatoryEvidenceRole.ECFR_POINT_IN_TIME: (
            "https://www.ecfr.gov/api/versioner/v1/full/2026-08-27/title-29.xml?part=1910"
        ),
        RegulatoryEvidenceRole.FEDERAL_REGISTER_CHANGE: (
            "https://www.federalregister.gov/documents/2026/01/15/2026-00001/synthetic"
        ),
        RegulatoryEvidenceRole.LSA_CHANGE_INDEX: (
            "https://www.govinfo.gov/app/details/LSA-2026-08"
        ),
    }
    return RegulatorySourceEvidence(
        evidence_id=evidence_id,
        role=role,
        authority="United States official publication",
        citation="29 CFR 1910.147",
        package_id=package_id or f"package:{role.value}:v1",
        source_url=urls[role],
        artifact_sha256=sha256,
        byte_count=100,
        section_citations=("29 CFR 1910.147",),
        retrieved_at=NOW,
    )


def verified_source() -> VerifiedRegulatorySource:
    evidence = (
        source(RegulatoryEvidenceRole.ANNUAL_CFR_BASELINE, "evidence:annual", SHA_A),
        source(RegulatoryEvidenceRole.ECFR_POINT_IN_TIME, "evidence:ecfr", SHA_B),
        source(RegulatoryEvidenceRole.FEDERAL_REGISTER_CHANGE, "evidence:fr", SHA_C),
        source(RegulatoryEvidenceRole.LSA_CHANGE_INDEX, "evidence:lsa", SHA_D),
    )
    return VerifiedRegulatorySource(
        verification_candidate_id="candidate:29-cfr-1910-147:2026-08-27",
        verification_candidate_sha256=SHA_E,
        source_review_id="review:regulatory-source:001",
        reviewer_id="reviewer:external-regulatory-source",
        reviewed_at=NOW,
        jurisdiction="US federal",
        citation="29 CFR 1910.147",
        annual_cfr_edition=2025,
        ecfr_as_of=date(2026, 8, 27),
        evidence=evidence,
        findings=(
            RegulatoryReconciliationFinding(
                finding_id="finding:source-match",
                citation="29 CFR 1910.147",
                status=RegulatoryReconciliationStatus.VERIFIED_MATCH,
                evidence_ids=tuple(item.evidence_id for item in evidence),
                statement="Synthetic exact source reconciliation.",
            ),
        ),
    )


def test_changed_official_artifact_stales_exact_verified_source_and_review() -> None:
    verified = verified_source()
    current = tuple(
        item.model_copy(update={"artifact_sha256": SHA_E})
        if item.role is RegulatoryEvidenceRole.ANNUAL_CFR_BASELINE
        else item
        for item in verified.evidence
    )

    report = assess_verified_regulatory_source_impact(
        verified,
        current_evidence=current,
        current_ecfr_as_of=verified.ecfr_as_of,
    )

    annual = next(
        impact
        for impact in report.impacts
        if impact.role is RegulatoryEvidenceRole.ANNUAL_CFR_BASELINE
    )
    assert report.source_state == "source_verification_stale"
    assert annual.state == "stale"
    assert annual.reasons == ("artifact_changed",)
    assert annual.affected_review_ids == ("review:regulatory-source:001",)
    assert annual.prior_artifact_sha256 == SHA_A
    assert annual.current_artifact_sha256 == SHA_E
    assert report.interpretation_authority == "none"
    assert report.operational_authority == "none"


def test_missing_required_official_role_remains_explicit_stale_evidence() -> None:
    verified = verified_source()
    current = tuple(
        item
        for item in verified.evidence
        if item.role is not RegulatoryEvidenceRole.LSA_CHANGE_INDEX
    )

    report = assess_verified_regulatory_source_impact(
        verified,
        current_evidence=current,
        current_ecfr_as_of=verified.ecfr_as_of,
    )

    lsa = next(
        impact
        for impact in report.impacts
        if impact.role is RegulatoryEvidenceRole.LSA_CHANGE_INDEX
    )
    assert lsa.state == "stale"
    assert lsa.reasons == ("evidence_missing",)
    assert lsa.current_evidence_id is None
    assert lsa.current_artifact_sha256 is None
    assert report.source_state == "source_verification_stale"


def test_changed_official_package_identity_stales_prior_review_even_when_hash_matches() -> None:
    verified = verified_source()
    current = tuple(
        item.model_copy(update={"package_id": "CFR-2025-title29-vol5-corrected"})
        if item.role is RegulatoryEvidenceRole.ANNUAL_CFR_BASELINE
        else item
        for item in verified.evidence
    )

    report = assess_verified_regulatory_source_impact(
        verified,
        current_evidence=current,
        current_ecfr_as_of=verified.ecfr_as_of,
    )

    annual = next(
        impact
        for impact in report.impacts
        if impact.role is RegulatoryEvidenceRole.ANNUAL_CFR_BASELINE
    )
    assert annual.state == "stale"
    assert annual.reasons == ("package_changed",)
    assert annual.prior_artifact_sha256 == annual.current_artifact_sha256


def test_changed_ecfr_as_of_date_stales_exact_point_in_time_review() -> None:
    verified = verified_source()

    report = assess_verified_regulatory_source_impact(
        verified,
        current_evidence=verified.evidence,
        current_ecfr_as_of=date(2026, 8, 28),
    )

    ecfr = next(
        impact
        for impact in report.impacts
        if impact.role is RegulatoryEvidenceRole.ECFR_POINT_IN_TIME
    )
    assert ecfr.state == "stale"
    assert ecfr.reasons == ("as_of_changed",)
    assert ecfr.affected_review_ids == (verified.source_review_id,)
    assert report.current_ecfr_as_of == date(2026, 8, 28)


def test_duplicate_current_official_role_fails_closed() -> None:
    verified = verified_source()
    duplicate = verified.evidence[0].model_copy(update={"evidence_id": "evidence:annual:duplicate"})

    with pytest.raises(ValueError, match="duplicate current regulatory evidence role"):
        assess_verified_regulatory_source_impact(
            verified,
            current_evidence=(*verified.evidence, duplicate),
            current_ecfr_as_of=verified.ecfr_as_of,
        )
