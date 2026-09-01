from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pytest

from oscillink_safety_ops import regulatory_artifacts
from oscillink_safety_ops.domain import (
    RegulatoryEvidenceRole,
    RegulatorySectionSnapshot,
    RegulatorySourceEvidence,
)
from oscillink_safety_ops.regulatory_artifacts import (
    RegulatoryArtifactIntegrityError,
    compare_cfr_section_snapshots,
    extract_regulatory_section_xml,
    verify_regulatory_artifact,
)
from scripts.export_schemas import SCHEMAS

NOW = datetime(2026, 8, 31, tzinfo=UTC)


def section_snapshot(
    *, role: RegulatoryEvidenceRole, evidence_id: str, artifact_sha256: str, text: str
) -> RegulatorySectionSnapshot:
    return RegulatorySectionSnapshot(
        evidence_id=evidence_id,
        evidence_role=role,
        artifact_ref=f"artifacts/{evidence_id.rsplit(':', 1)[-1]}.xml",
        source_artifact_sha256=artifact_sha256,
        citation="29 CFR 1910.147",
        source_locator="synthetic-section-locator",
        heading="1910.147 Synthetic heading",
        normalized_text=text,
        normalized_text_sha256="sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest(),
        parser_config_sha256="sha256:" + "c" * 64,
    )


def ecfr_evidence(content: bytes) -> RegulatorySourceEvidence:
    return RegulatorySourceEvidence(
        evidence_id="evidence:ecfr:29-cfr-1910-147:2026-08-27",
        role=RegulatoryEvidenceRole.ECFR_POINT_IN_TIME,
        authority="United States eCFR",
        citation="29 CFR 1910.147",
        package_id="ecfr:2026-08-27:title29:part1910",
        source_url=("https://www.ecfr.gov/api/versioner/v1/full/2026-08-27/title-29.xml?part=1910"),
        artifact_sha256="sha256:" + hashlib.sha256(content).hexdigest(),
        byte_count=len(content),
        section_citations=("29 CFR 1910.147",),
        retrieved_at=NOW,
    )


def annual_cfr_evidence(content: bytes) -> RegulatorySourceEvidence:
    return RegulatorySourceEvidence(
        evidence_id="evidence:govinfo:2025:29-cfr-1910-147",
        role=RegulatoryEvidenceRole.ANNUAL_CFR_BASELINE,
        authority="United States Code of Federal Regulations",
        citation="29 CFR 1910.147",
        package_id="CFR-2025-title29-vol5",
        source_url="https://www.govinfo.gov/app/details/CFR-2025-title29-vol5",
        artifact_sha256="sha256:" + hashlib.sha256(content).hexdigest(),
        byte_count=len(content),
        section_citations=("29 CFR 1910.147",),
        retrieved_at=NOW,
    )


def test_regulatory_artifact_verification_binds_exact_bytes_inside_root(tmp_path: Path) -> None:
    content = b"<DIV8 TYPE='SECTION' N='1910.147'><HEAD>Synthetic section</HEAD></DIV8>\n"
    artifact = tmp_path / "artifacts" / "ecfr.xml"
    artifact.parent.mkdir()
    artifact.write_bytes(content)

    verified = verify_regulatory_artifact(
        ecfr_evidence(content), artifact_ref="artifacts/ecfr.xml", root=tmp_path
    )

    assert verified.evidence_id == "evidence:ecfr:29-cfr-1910-147:2026-08-27"
    assert verified.artifact_ref == "artifacts/ecfr.xml"
    assert verified.artifact_sha256 == "sha256:" + hashlib.sha256(content).hexdigest()
    assert verified.integrity_state == "integrity_verified"
    assert verified.content_treatment == "untrusted_source_bytes"
    assert verified.operational_authority == "none"


def test_regulatory_artifact_verification_rejects_root_escape(tmp_path: Path) -> None:
    content = b"<DIV8 TYPE='SECTION' N='1910.147'/>\n"
    outside = tmp_path.parent / "outside-regulatory.xml"
    outside.write_bytes(content)

    try:
        with pytest.raises(
            RegulatoryArtifactIntegrityError, match="invalid regulatory artifact_ref"
        ):
            verify_regulatory_artifact(
                ecfr_evidence(content), artifact_ref="../outside-regulatory.xml", root=tmp_path
            )
    finally:
        outside.unlink(missing_ok=True)


def test_regulatory_artifact_verification_rejects_changed_bytes(tmp_path: Path) -> None:
    expected = b"<SECTION>expected</SECTION>\n"
    changed = b"<SECTION>tampered</SECTION>\n"
    assert len(expected) == len(changed)
    artifact = tmp_path / "regulatory.xml"
    artifact.write_bytes(changed)

    with pytest.raises(RegulatoryArtifactIntegrityError, match="hash mismatch"):
        verify_regulatory_artifact(
            ecfr_evidence(expected), artifact_ref=artifact.name, root=tmp_path
        )


def test_regulatory_artifact_verification_rejects_oversized_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    content = b"123456789"
    artifact = tmp_path / "oversized.xml"
    artifact.write_bytes(content)
    monkeypatch.setattr(regulatory_artifacts, "MAX_REGULATORY_ARTIFACT_BYTES", 8)

    with pytest.raises(RegulatoryArtifactIntegrityError, match="exceeds 8 bytes"):
        verify_regulatory_artifact(
            ecfr_evidence(content), artifact_ref=artifact.name, root=tmp_path
        )


def test_extracts_one_deterministic_ecfr_section_from_verified_xml(tmp_path: Path) -> None:
    content = b"""<ROOT>
  <DIV8 TYPE="SECTION" N="1910.146"><HEAD>1910.146 Other</HEAD><P>Other text.</P></DIV8>
  <DIV8 TYPE="SECTION" N="\xc2\xa7 1910.147">
    <HEAD>\xc2\xa7 1910.147 The control of hazardous energy</HEAD>
    <P>(a) Scope.</P><P>(c) General.</P>
  </DIV8>
</ROOT>
"""
    artifact = tmp_path / "ecfr.xml"
    artifact.write_bytes(content)
    evidence = ecfr_evidence(content)

    section = extract_regulatory_section_xml(
        evidence,
        artifact_ref=artifact.name,
        root=tmp_path,
        citation="29 CFR 1910.147",
        parser_config_sha256="sha256:" + "f" * 64,
    )

    expected_text = "\u00a7 1910.147 The control of hazardous energy (a) Scope. (c) General."
    assert section.evidence_id == evidence.evidence_id
    assert section.source_artifact_sha256 == evidence.artifact_sha256
    assert section.citation == "29 CFR 1910.147"
    assert section.heading == "\u00a7 1910.147 The control of hazardous energy"
    assert section.normalized_text == expected_text
    assert section.normalized_text_sha256 == (
        "sha256:" + hashlib.sha256(expected_text.encode("utf-8")).hexdigest()
    )
    assert section.source_locator == "DIV8[N=\u00a7 1910.147]"
    assert section.extraction_state == "source_extraction_candidate"
    assert section.interpretation_authority == "none"


def test_extracts_govinfo_section_and_subject_from_verified_xml(tmp_path: Path) -> None:
    content = b"""<CFRDOC><SECTION>
  <SECTNO>\xc2\xa7 1910.147</SECTNO>
  <SUBJECT>The control of hazardous energy (lockout/tagout).</SUBJECT>
  <P>(a) Scope, application, and purpose.</P>
</SECTION></CFRDOC>
"""
    artifact = tmp_path / "annual-cfr.xml"
    artifact.write_bytes(content)
    evidence = annual_cfr_evidence(content)

    section = extract_regulatory_section_xml(
        evidence,
        artifact_ref=artifact.name,
        root=tmp_path,
        citation="29 CFR 1910.147",
        parser_config_sha256="sha256:" + "e" * 64,
    )

    assert section.heading == ("\u00a7 1910.147 The control of hazardous energy (lockout/tagout).")
    assert section.source_locator == "SECTION[SECTNO=\u00a7 1910.147]"
    assert section.evidence_role is RegulatoryEvidenceRole.ANNUAL_CFR_BASELINE


def test_regulatory_xml_extraction_rejects_doctype_and_entity_declarations(
    tmp_path: Path,
) -> None:
    content = b"""<!DOCTYPE ROOT [<!ENTITY injected "expanded">]>
<ROOT><DIV8 TYPE="SECTION" N="1910.147">
<HEAD>1910.147 Synthetic</HEAD><P>&injected;</P>
</DIV8></ROOT>"""
    artifact = tmp_path / "unsafe.xml"
    artifact.write_bytes(content)

    with pytest.raises(RegulatoryArtifactIntegrityError, match="unsafe XML declaration"):
        extract_regulatory_section_xml(
            ecfr_evidence(content),
            artifact_ref=artifact.name,
            root=tmp_path,
            citation="29 CFR 1910.147",
            parser_config_sha256="sha256:" + "d" * 64,
        )


def test_exact_annual_and_ecfr_section_text_produces_match_evidence() -> None:
    text = "1910.147 Synthetic heading (a) Scope."
    annual = section_snapshot(
        role=RegulatoryEvidenceRole.ANNUAL_CFR_BASELINE,
        evidence_id="evidence:annual",
        artifact_sha256="sha256:" + "a" * 64,
        text=text,
    )
    ecfr = section_snapshot(
        role=RegulatoryEvidenceRole.ECFR_POINT_IN_TIME,
        evidence_id="evidence:ecfr",
        artifact_sha256="sha256:" + "b" * 64,
        text=text,
    )

    comparison = compare_cfr_section_snapshots(annual, ecfr)

    assert comparison.status == "verified_match"
    assert comparison.evidence_ids == ("evidence:annual", "evidence:ecfr")
    assert comparison.annual_text_sha256 == comparison.ecfr_text_sha256
    assert comparison.authority_state == "reconciliation_evidence_only"
    assert comparison.interpretation_authority == "none"
    assert comparison.operational_authority == "none"


def test_changed_section_text_remains_unresolved_without_amendment_evidence() -> None:
    annual = section_snapshot(
        role=RegulatoryEvidenceRole.ANNUAL_CFR_BASELINE,
        evidence_id="evidence:annual",
        artifact_sha256="sha256:" + "a" * 64,
        text="1910.147 Synthetic heading (a) Annual baseline text.",
    )
    ecfr = section_snapshot(
        role=RegulatoryEvidenceRole.ECFR_POINT_IN_TIME,
        evidence_id="evidence:ecfr",
        artifact_sha256="sha256:" + "b" * 64,
        text="1910.147 Synthetic heading (a) Changed point-in-time text.",
    )

    comparison = compare_cfr_section_snapshots(annual, ecfr)

    assert comparison.status == "unresolved_difference"
    assert "Federal Register and LSA evidence is required" in comparison.rationale
    assert comparison.annual_text_sha256 != comparison.ecfr_text_sha256
    assert comparison.interpretation_authority == "none"


def test_regulatory_artifact_schemas_preserve_candidate_only_authority() -> None:
    artifact = SCHEMAS["regulatory-artifact-verification.schema.json"]
    section = SCHEMAS["regulatory-section-snapshot.schema.json"]
    comparison = SCHEMAS["regulatory-section-comparison.schema.json"]

    assert artifact["properties"]["integrity_state"]["const"] == "integrity_verified"
    assert artifact["properties"]["operational_authority"]["const"] == "none"
    assert section["properties"]["extraction_state"]["const"] == ("source_extraction_candidate")
    assert section["properties"]["interpretation_authority"]["const"] == "none"
    assert comparison["properties"]["authority_state"]["const"] == ("reconciliation_evidence_only")
    assert comparison["properties"]["compliance_authority"]["const"] == "none"
