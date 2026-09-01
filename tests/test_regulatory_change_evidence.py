from __future__ import annotations

import hashlib
from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from oscillink_safety_ops.domain import (
    FederalRegisterAction,
    FederalRegisterChangeCandidate,
    FederalRegisterChangeChain,
    LsaCoverageCandidate,
    RegulatoryDifferenceReview,
    RegulatoryDifferenceReviewDecision,
    RegulatoryEvidenceRole,
    RegulatorySectionComparison,
    RegulatorySectionSnapshot,
)
from oscillink_safety_ops.regulatory_artifacts import compare_cfr_section_snapshots
from oscillink_safety_ops.regulatory_changes import (
    build_federal_register_change_chain,
    build_regulatory_change_evidence_bundle,
    record_reviewed_regulatory_difference,
    regulatory_change_bundle_sha256,
)
from scripts.export_schemas import SCHEMAS

NOW = datetime(2026, 9, 1, tzinfo=UTC)
SHA_A = "sha256:" + "a" * 64
SHA_B = "sha256:" + "b" * 64
SHA_C = "sha256:" + "c" * 64
SHA_D = "sha256:" + "d" * 64
SHA_E = "sha256:" + "e" * 64
CONFIG_SHA = "sha256:" + "f" * 64
CITATION = "29 CFR 1910.147"


def text_sha256(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode()).hexdigest()


def snapshot(
    *,
    role: RegulatoryEvidenceRole,
    evidence_id: str,
    artifact_sha256: str,
    text: str,
) -> RegulatorySectionSnapshot:
    return RegulatorySectionSnapshot(
        evidence_id=evidence_id,
        evidence_role=role,
        artifact_ref=f"artifacts/{evidence_id}.xml",
        source_artifact_sha256=artifact_sha256,
        citation=CITATION,
        source_locator="SECTION[1]",
        heading="The control of hazardous energy (lockout/tagout).",
        normalized_text=text,
        normalized_text_sha256=text_sha256(text),
        parser_config_sha256=CONFIG_SHA,
    )


def unresolved_comparison() -> RegulatorySectionComparison:
    return compare_cfr_section_snapshots(
        snapshot(
            role=RegulatoryEvidenceRole.ANNUAL_CFR_BASELINE,
            evidence_id="evidence:annual",
            artifact_sha256=SHA_A,
            text="Annual edition text.",
        ),
        snapshot(
            role=RegulatoryEvidenceRole.ECFR_POINT_IN_TIME,
            evidence_id="evidence:ecfr",
            artifact_sha256=SHA_B,
            text="Changed point-in-time text.",
        ),
    )


def matched_comparison() -> RegulatorySectionComparison:
    return compare_cfr_section_snapshots(
        snapshot(
            role=RegulatoryEvidenceRole.ANNUAL_CFR_BASELINE,
            evidence_id="evidence:annual",
            artifact_sha256=SHA_A,
            text="Same official text.",
        ),
        snapshot(
            role=RegulatoryEvidenceRole.ECFR_POINT_IN_TIME,
            evidence_id="evidence:ecfr",
            artifact_sha256=SHA_B,
            text="Same official text.",
        ),
    )


def amendment(*, effective_date: date | None = date(2026, 7, 1)) -> FederalRegisterChangeCandidate:
    instruction = f"In {CITATION}, revise paragraph (a)."
    return FederalRegisterChangeCandidate(
        candidate_id="fr-change:2026-12345:29-cfr-1910-147",
        evidence_id="evidence:fr",
        source_artifact_sha256=SHA_C,
        document_number="2026-12345",
        publication_date=date(2026, 6, 1),
        effective_date=effective_date,
        action=FederalRegisterAction.AMEND,
        affected_citations=(CITATION,),
        source_locator="DOCUMENT[1]/AMDPAR[1]",
        raw_instruction=instruction,
        raw_instruction_sha256=text_sha256(instruction),
        parser_config_sha256=CONFIG_SHA,
    )


def lsa(*, document_numbers: tuple[str, ...] = ("2026-12345",)) -> LsaCoverageCandidate:
    raw_entry = f"{CITATION} ... 2026-12345"
    return LsaCoverageCandidate(
        candidate_id="lsa:2026-07:29-cfr-1910-147",
        evidence_id="evidence:lsa",
        source_artifact_sha256=SHA_D,
        through_date=date(2026, 8, 31),
        citation=CITATION,
        federal_register_document_numbers=document_numbers,
        source_locator="LSA[1]/ENTRY[1]",
        raw_entry=raw_entry,
        raw_entry_sha256=text_sha256(raw_entry),
        parser_config_sha256=CONFIG_SHA,
    )


def test_unresolved_difference_collects_exact_fr_and_lsa_candidates_for_review() -> None:
    comparison = unresolved_comparison()

    bundle = build_regulatory_change_evidence_bundle(
        comparison,
        amendments=(amendment(),),
        lsa_coverage=lsa(),
        ecfr_as_of=date(2026, 8, 27),
        generated_at=NOW,
    )

    assert bundle.comparison.status == "unresolved_difference"
    assert bundle.comparison_sha256.startswith("sha256:")
    assert bundle.amendments[0].evidence_role is RegulatoryEvidenceRole.FEDERAL_REGISTER_CHANGE
    assert bundle.lsa_coverage.evidence_role is RegulatoryEvidenceRole.LSA_CHANGE_INDEX
    assert bundle.bundle_state == "requires_authorized_source_review"
    assert bundle.interpretation_authority == "none"
    assert bundle.operational_authority == "none"


def test_change_candidates_reject_raw_text_hash_mismatch() -> None:
    amendment_payload = amendment().model_dump(mode="json")
    amendment_payload["raw_instruction_sha256"] = SHA_E
    with pytest.raises(ValidationError, match="raw instruction hash mismatch"):
        FederalRegisterChangeCandidate.model_validate(amendment_payload)

    raw_entry = f"{CITATION} ... 2026-12345"
    with pytest.raises(ValidationError, match="raw LSA entry hash mismatch"):
        LsaCoverageCandidate(
            candidate_id="lsa:bad-hash",
            evidence_id="evidence:lsa",
            source_artifact_sha256=SHA_D,
            through_date=date(2026, 8, 31),
            citation=CITATION,
            federal_register_document_numbers=("2026-12345",),
            source_locator="LSA[1]/ENTRY[1]",
            raw_entry=raw_entry,
            raw_entry_sha256=SHA_E,
            parser_config_sha256=CONFIG_SHA,
        )


def test_change_candidates_require_exact_citation_and_document_coverage() -> None:
    amendment_payload = amendment().model_dump(mode="json")
    amendment_payload["affected_citations"] = []
    with pytest.raises(ValidationError, match="affected citation"):
        FederalRegisterChangeCandidate.model_validate(amendment_payload)

    lsa_payload = lsa().model_dump(mode="json")
    lsa_payload["federal_register_document_numbers"] = []
    with pytest.raises(ValidationError, match="Federal Register page or document number"):
        LsaCoverageCandidate.model_validate(lsa_payload)


def test_change_bundle_rejects_already_matched_comparison() -> None:
    with pytest.raises(ValueError, match="unresolved section comparison"):
        build_regulatory_change_evidence_bundle(
            matched_comparison(),
            amendments=(amendment(),),
            lsa_coverage=lsa(),
            ecfr_as_of=date(2026, 8, 27),
            generated_at=NOW,
        )


def test_change_bundle_requires_at_least_one_federal_register_candidate() -> None:
    with pytest.raises(ValueError, match="Federal Register change candidate"):
        build_regulatory_change_evidence_bundle(
            unresolved_comparison(),
            amendments=(),
            lsa_coverage=lsa(),
            ecfr_as_of=date(2026, 8, 27),
            generated_at=NOW,
        )


def test_change_bundle_rejects_federal_register_candidate_for_other_section() -> None:
    unrelated = amendment().model_copy(update={"affected_citations": ("29 CFR 1910.146",)})

    with pytest.raises(ValueError, match="comparison citation"):
        build_regulatory_change_evidence_bundle(
            unresolved_comparison(),
            amendments=(unrelated,),
            lsa_coverage=lsa(),
            ecfr_as_of=date(2026, 8, 27),
            generated_at=NOW,
        )


def test_change_bundle_rejects_lsa_candidate_for_other_section() -> None:
    unrelated = lsa().model_copy(update={"citation": "29 CFR 1910.146"})

    with pytest.raises(ValueError, match="LSA candidate does not cover"):
        build_regulatory_change_evidence_bundle(
            unresolved_comparison(),
            amendments=(amendment(),),
            lsa_coverage=unrelated,
            ecfr_as_of=date(2026, 8, 27),
            generated_at=NOW,
        )


def test_change_bundle_requires_lsa_reference_for_every_fr_document() -> None:
    with pytest.raises(ValueError, match="LSA coverage is missing Federal Register document"):
        build_regulatory_change_evidence_bundle(
            unresolved_comparison(),
            amendments=(amendment(),),
            lsa_coverage=lsa(document_numbers=("2026-99999",)),
            ecfr_as_of=date(2026, 8, 27),
            generated_at=NOW,
        )


def test_change_bundle_accepts_exact_official_lsa_page_coverage() -> None:
    exact_page_amendment = amendment().model_copy(update={"federal_register_start_page": 27999})
    official_lsa = lsa().model_copy(
        update={
            "federal_register_document_numbers": (),
            "federal_register_pages": (27999,),
        }
    )

    bundle = build_regulatory_change_evidence_bundle(
        unresolved_comparison(),
        amendments=(exact_page_amendment,),
        lsa_coverage=official_lsa,
        ecfr_as_of=date(2026, 8, 27),
        generated_at=NOW,
    )

    assert bundle.lsa_coverage.federal_register_pages == (27999,)


def test_federal_register_delay_chain_establishes_controlling_effective_date() -> None:
    original = amendment(effective_date=date(2026, 7, 1))
    delay = amendment(effective_date=date(2026, 8, 15)).model_copy(
        update={
            "candidate_id": "fr-change:2026-23456:delay",
            "document_number": "2026-23456",
            "publication_date": date(2026, 6, 20),
            "action": FederalRegisterAction.DELAY_EFFECTIVE_DATE,
            "related_document_number": original.document_number,
        }
    )

    chain = build_federal_register_change_chain(CITATION, (original, delay))

    assert isinstance(chain, FederalRegisterChangeChain)
    assert chain.chain_state == "effective_date_established"
    assert chain.controlling_effective_date == date(2026, 8, 15)
    assert chain.interpretation_authority == "none"


def test_federal_register_correction_chain_requires_explicit_prior_document() -> None:
    correction = amendment().model_copy(
        update={
            "candidate_id": "fr-change:2026-23456:correction",
            "document_number": "2026-23456",
            "publication_date": date(2026, 6, 20),
            "action": FederalRegisterAction.CORRECT,
            "related_document_number": None,
        }
    )

    with pytest.raises(ValueError, match="explicit related Federal Register document"):
        build_federal_register_change_chain(CITATION, (amendment(), correction))


def test_federal_register_withdrawal_chain_remains_explicitly_withdrawn() -> None:
    original = amendment()
    withdrawal = amendment(effective_date=None).model_copy(
        update={
            "candidate_id": "fr-change:2026-23456:withdrawal",
            "document_number": "2026-23456",
            "publication_date": date(2026, 6, 20),
            "action": FederalRegisterAction.WITHDRAW,
            "related_document_number": original.document_number,
        }
    )

    chain = build_federal_register_change_chain(CITATION, (original, withdrawal))

    assert chain.chain_state == "withdrawn"
    assert chain.controlling_effective_date is None
    assert chain.operational_authority == "none"


@pytest.mark.parametrize("effective_date", [None, date(2026, 9, 1)])
def test_change_bundle_rejects_missing_or_future_effective_date(
    effective_date: date | None,
) -> None:
    with pytest.raises(ValueError, match="effective date is not established as of"):
        build_regulatory_change_evidence_bundle(
            unresolved_comparison(),
            amendments=(amendment(effective_date=effective_date),),
            lsa_coverage=lsa(),
            ecfr_as_of=date(2026, 8, 27),
            generated_at=NOW,
        )


def test_change_bundle_rejects_lsa_coverage_ending_before_ecfr_date() -> None:
    incomplete = lsa().model_copy(update={"through_date": date(2026, 8, 1)})

    with pytest.raises(ValueError, match="LSA coverage does not extend through"):
        build_regulatory_change_evidence_bundle(
            unresolved_comparison(),
            amendments=(amendment(),),
            lsa_coverage=incomplete,
            ecfr_as_of=date(2026, 8, 27),
            generated_at=NOW,
        )


def test_external_review_can_mark_exact_change_bundle_as_explained_source_change() -> None:
    bundle = build_regulatory_change_evidence_bundle(
        unresolved_comparison(),
        amendments=(amendment(),),
        lsa_coverage=lsa(),
        ecfr_as_of=date(2026, 8, 27),
        generated_at=NOW,
    )
    review = RegulatoryDifferenceReview(
        review_id="review:regulatory-difference:001",
        bundle_id=bundle.bundle_id,
        bundle_sha256=regulatory_change_bundle_sha256(bundle),
        decision=RegulatoryDifferenceReviewDecision.ACCEPT_EXPLAINED_OFFICIAL_CHANGE,
        reviewer_id="reviewer:external-regulatory-source",
        reviewer_role="role:authorized-regulatory-source-reviewer",
        reviewer_authority_ref="authority:synthetic-regulatory-review-matrix-v1",
        reviewed_at=NOW,
        rationale="Synthetic source-only acceptance of the cited official change evidence.",
    )

    reviewed = record_reviewed_regulatory_difference(bundle, review)

    assert reviewed.finding.status == "explained_official_change"
    assert set(reviewed.finding.evidence_ids) == {
        "evidence:annual",
        "evidence:ecfr",
        "evidence:fr",
        "evidence:lsa",
    }
    assert reviewed.bundle_sha256 == review.bundle_sha256
    assert reviewed.authority_state == "reviewed_source_explanation_only"
    assert reviewed.interpretation_authority == "none"
    assert reviewed.operational_authority == "none"


def test_difference_review_cannot_transfer_to_changed_bundle_bytes() -> None:
    bundle = build_regulatory_change_evidence_bundle(
        unresolved_comparison(),
        amendments=(amendment(),),
        lsa_coverage=lsa(),
        ecfr_as_of=date(2026, 8, 27),
        generated_at=NOW,
    )
    review = RegulatoryDifferenceReview(
        review_id="review:regulatory-difference:hash-bound",
        bundle_id=bundle.bundle_id,
        bundle_sha256=regulatory_change_bundle_sha256(bundle),
        decision=RegulatoryDifferenceReviewDecision.ACCEPT_EXPLAINED_OFFICIAL_CHANGE,
        reviewer_id="reviewer:external-regulatory-source",
        reviewer_role="role:authorized-regulatory-source-reviewer",
        reviewer_authority_ref="authority:synthetic-regulatory-review-matrix-v1",
        reviewed_at=NOW,
        rationale="Synthetic source-only acceptance of exact bytes.",
    )
    changed = bundle.model_copy(update={"generated_at": datetime(2026, 9, 1, 0, 0, 1, tzinfo=UTC)})

    with pytest.raises(ValueError, match="bundle hash mismatch"):
        record_reviewed_regulatory_difference(changed, review)


def test_unknown_federal_register_action_cannot_be_marked_explained() -> None:
    unknown = amendment().model_copy(update={"action": FederalRegisterAction.UNKNOWN})
    bundle = build_regulatory_change_evidence_bundle(
        unresolved_comparison(),
        amendments=(unknown,),
        lsa_coverage=lsa(),
        ecfr_as_of=date(2026, 8, 27),
        generated_at=NOW,
    )
    review = RegulatoryDifferenceReview(
        review_id="review:regulatory-difference:unknown-action",
        bundle_id=bundle.bundle_id,
        bundle_sha256=regulatory_change_bundle_sha256(bundle),
        decision=RegulatoryDifferenceReviewDecision.ACCEPT_EXPLAINED_OFFICIAL_CHANGE,
        reviewer_id="reviewer:external-regulatory-source",
        reviewer_role="role:authorized-regulatory-source-reviewer",
        reviewer_authority_ref="authority:synthetic-regulatory-review-matrix-v1",
        reviewed_at=NOW,
        rationale="Synthetic review must not override unsupported extraction state.",
    )

    with pytest.raises(ValueError, match="unsupported Federal Register action"):
        record_reviewed_regulatory_difference(bundle, review)


def test_rejected_difference_review_cannot_create_explained_finding() -> None:
    bundle = build_regulatory_change_evidence_bundle(
        unresolved_comparison(),
        amendments=(amendment(),),
        lsa_coverage=lsa(),
        ecfr_as_of=date(2026, 8, 27),
        generated_at=NOW,
    )
    review = RegulatoryDifferenceReview(
        review_id="review:regulatory-difference:rejected",
        bundle_id=bundle.bundle_id,
        bundle_sha256=regulatory_change_bundle_sha256(bundle),
        decision=RegulatoryDifferenceReviewDecision.REJECT_CHANGE_EXPLANATION,
        reviewer_id="reviewer:external-regulatory-source",
        reviewer_role="role:authorized-regulatory-source-reviewer",
        reviewer_authority_ref="authority:synthetic-regulatory-review-matrix-v1",
        reviewed_at=NOW,
        rationale="Synthetic rejection because the source evidence is insufficient.",
    )

    with pytest.raises(ValueError, match="does not accept"):
        record_reviewed_regulatory_difference(bundle, review)


def test_change_evidence_schemas_preserve_source_only_authority() -> None:
    expected = {
        "federal-register-change-candidate.schema.json": (
            "extraction_state",
            "source_extraction_candidate",
        ),
        "federal-register-change-chain.schema.json": (
            "authority_state",
            "source_change_lineage_only",
        ),
        "lsa-coverage-candidate.schema.json": (
            "extraction_state",
            "source_extraction_candidate",
        ),
        "regulatory-change-evidence-bundle.schema.json": (
            "bundle_state",
            "requires_authorized_source_review",
        ),
        "regulatory-difference-review.schema.json": ("authority_state", "source_review_only"),
        "reviewed-regulatory-difference.schema.json": (
            "authority_state",
            "reviewed_source_explanation_only",
        ),
        "regulatory-source-impact-report.schema.json": (
            "authority_state",
            "change_evidence_only",
        ),
    }

    for filename, (field, expected_const) in expected.items():
        schema = SCHEMAS[filename]
        assert schema["properties"][field]["const"] == expected_const
        assert schema["properties"]["operational_authority"]["const"] == "none"
