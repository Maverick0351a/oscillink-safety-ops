from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pytest

from oscillink_safety_ops.domain import (
    FederalRegisterAction,
    RegulatoryEvidenceRole,
    RegulatorySourceEvidence,
)
from oscillink_safety_ops.regulatory_changes import (
    extract_federal_register_change_candidates,
    extract_lsa_coverage_candidate,
)

NOW = datetime(2026, 9, 1, tzinfo=UTC)
CITATION = "29 CFR 1911.10"
CONFIG_SHA = "sha256:" + "f" * 64


def _evidence(
    artifact: Path,
    *,
    role: RegulatoryEvidenceRole,
    evidence_id: str,
    package_id: str,
    source_url: str,
) -> RegulatorySourceEvidence:
    content = artifact.read_bytes()
    return RegulatorySourceEvidence(
        evidence_id=evidence_id,
        role=role,
        authority="United States Government Publishing Office",
        citation=CITATION,
        package_id=package_id,
        source_url=source_url,
        artifact_sha256="sha256:" + hashlib.sha256(content).hexdigest(),
        byte_count=len(content),
        section_citations=(CITATION,),
        retrieved_at=NOW,
    )


@pytest.mark.parametrize("effective_tag", ["DATES", "EFFDATE"])
@pytest.mark.parametrize("publication_text", ["July 1, 2025", "Tuesday, July 1, 2025"])
def test_extracts_exact_federal_register_amendment_from_verified_issue_xml(
    tmp_path: Path, effective_tag: str, publication_text: str
) -> None:
    artifact = tmp_path / "official" / "FR-2025-07-01.xml"
    artifact.parent.mkdir()
    artifact.write_text(
        f"<FEDREG><DATE>{publication_text}</DATE><RULES><RULE>"
        "<PREAMB><CFR>29 CFR Part 1911</CFR><ACT>ACTION: Final rule.</ACT>"
        f"<{effective_tag}><P>This rule is effective July 2, 2025.</P></{effective_tag}>"
        "</PREAMB>"
        '<PRTPAGE P="27999"/><REGTEXT><AMDPAR>§ 1911.10 is removed.</AMDPAR></REGTEXT>'
        "<FRDOC>[FR Doc. 2025-12345 Filed 6-30-25; 8:45 am]</FRDOC>"
        "</RULE></RULES></FEDREG>",
        encoding="utf-8",
    )
    evidence = _evidence(
        artifact,
        role=RegulatoryEvidenceRole.FEDERAL_REGISTER_CHANGE,
        evidence_id="evidence:fr:2025-12345",
        package_id="FR-2025-07-01",
        source_url="https://www.govinfo.gov/content/pkg/FR-2025-07-01/xml/FR-2025-07-01.xml",
    )

    candidates = extract_federal_register_change_candidates(
        evidence,
        artifact_ref="official/FR-2025-07-01.xml",
        root=tmp_path,
        citation=CITATION,
        parser_config_sha256=CONFIG_SHA,
    )

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.document_number == "2025-12345"
    assert candidate.publication_date.isoformat() == "2025-07-01"
    assert candidate.effective_date is not None
    assert candidate.effective_date.isoformat() == "2025-07-02"
    assert candidate.action is FederalRegisterAction.REMOVE
    assert candidate.federal_register_start_page == 27999
    assert candidate.raw_instruction == "§ 1911.10 is removed."
    assert candidate.parser_identity == "govinfo-federal-register-xml"
    assert candidate.operational_authority == "none"


def test_extracts_exact_lsa_entry_and_page_reference_from_verified_html(tmp_path: Path) -> None:
    artifact = tmp_path / "official" / "LSA-2025-07-title29.htm"
    artifact.parent.mkdir()
    artifact.write_text(
        "<html><head><title>List of CFR Sections Affected (LSA), July 2025 - "
        "Title 29 - Labor</title></head><body><pre>\n"
        "TITLE 29_LABOR\n1911.10 Removed....................................................27999\n"
        "</pre></body></html>",
        encoding="utf-8",
    )
    evidence = _evidence(
        artifact,
        role=RegulatoryEvidenceRole.LSA_CHANGE_INDEX,
        evidence_id="evidence:lsa:2025-07:title29",
        package_id="LSA-2025-07",
        source_url="https://www.govinfo.gov/content/pkg/LSA-2025-07/html/LSA-2025-07-title29.htm",
    )

    candidate = extract_lsa_coverage_candidate(
        evidence,
        artifact_ref="official/LSA-2025-07-title29.htm",
        root=tmp_path,
        citation=CITATION,
        parser_config_sha256=CONFIG_SHA,
    )

    assert candidate.through_date.isoformat() == "2025-07-31"
    assert candidate.status_text == "Removed"
    assert candidate.federal_register_pages == (27999,)
    assert candidate.raw_entry.startswith("1911.10 Removed")
    assert candidate.parser_identity == "govinfo-lsa-html"
    assert candidate.operational_authority == "none"


def test_publication_parsers_reject_role_mismatch(tmp_path: Path) -> None:
    artifact = tmp_path / "wrong.xml"
    artifact.write_text("<FEDREG/>", encoding="utf-8")
    evidence = _evidence(
        artifact,
        role=RegulatoryEvidenceRole.LSA_CHANGE_INDEX,
        evidence_id="evidence:wrong-role",
        package_id="LSA-2025-07",
        source_url="https://www.govinfo.gov/content/pkg/LSA-2025-07/html/title29.htm",
    )

    with pytest.raises(ValueError, match="Federal Register evidence role"):
        extract_federal_register_change_candidates(
            evidence,
            artifact_ref="wrong.xml",
            root=tmp_path,
            citation=CITATION,
            parser_config_sha256=CONFIG_SHA,
        )
