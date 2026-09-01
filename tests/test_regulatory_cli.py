from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from oscillink_safety_ops.cli import run
from oscillink_safety_ops.domain import (
    RegulatoryEvidenceRole,
    RegulatorySectionSnapshot,
    RegulatorySourceEvidence,
)

NOW = datetime(2026, 9, 1, tzinfo=UTC)
CONFIG_SHA = "sha256:" + "f" * 64
CITATION = "29 CFR 1910.147"


def write_ecfr_evidence(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "evidence-root"
    artifact = root / "ecfr.xml"
    artifact.parent.mkdir()
    artifact.write_text(
        '<ECFR><DIV8 TYPE="SECTION" N="§ 1910.147">'
        "<HEAD>§ 1910.147 The control of hazardous energy.</HEAD>"
        "<P>Candidate source text.</P></DIV8></ECFR>",
        encoding="utf-8",
    )
    raw = artifact.read_bytes()
    evidence = RegulatorySourceEvidence(
        evidence_id="evidence:ecfr:2026-08-27",
        role=RegulatoryEvidenceRole.ECFR_POINT_IN_TIME,
        authority="United States official publication",
        citation=CITATION,
        package_id="ecfr:2026-08-27:title29:part1910",
        source_url="https://www.ecfr.gov/api/versioner/v1/full/2026-08-27/title-29.xml?part=1910",
        artifact_sha256="sha256:" + hashlib.sha256(raw).hexdigest(),
        byte_count=len(raw),
        section_citations=(CITATION,),
        retrieved_at=NOW,
    )
    evidence_path = tmp_path / "ecfr-evidence.json"
    evidence_path.write_text(evidence.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return root, evidence_path


def test_cli_verifies_exact_regulatory_artifact_bytes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root, evidence_path = write_ecfr_evidence(tmp_path)

    assert (
        run(
            [
                "regulatory",
                "artifact-verify",
                "--evidence",
                str(evidence_path),
                "--artifact-ref",
                "ecfr.xml",
                "--root",
                str(root),
            ]
        )
        == 0
    )

    result = json.loads(capsys.readouterr().out)
    assert result["integrity_state"] == "integrity_verified"
    assert result["content_treatment"] == "untrusted_source_bytes"
    assert result["operational_authority"] == "none"


def test_cli_extracts_section_only_after_exact_artifact_verification(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root, evidence_path = write_ecfr_evidence(tmp_path)

    assert (
        run(
            [
                "regulatory",
                "section-extract",
                "--evidence",
                str(evidence_path),
                "--artifact-ref",
                "ecfr.xml",
                "--root",
                str(root),
                "--citation",
                CITATION,
                "--parser-config-sha256",
                CONFIG_SHA,
            ]
        )
        == 0
    )

    result = json.loads(capsys.readouterr().out)
    assert result["citation"] == CITATION
    assert result["source_artifact_sha256"].startswith("sha256:")
    assert result["extraction_state"] == "source_extraction_candidate"
    assert result["interpretation_authority"] == "none"
    assert result["operational_authority"] == "none"


def test_cli_conservatively_compares_exact_section_snapshots(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    paths: list[Path] = []
    for role, evidence_id, text in (
        (RegulatoryEvidenceRole.ANNUAL_CFR_BASELINE, "evidence:annual", "Annual text."),
        (RegulatoryEvidenceRole.ECFR_POINT_IN_TIME, "evidence:ecfr", "Changed text."),
    ):
        text_hash = "sha256:" + hashlib.sha256(text.encode()).hexdigest()
        snapshot = RegulatorySectionSnapshot(
            evidence_id=evidence_id,
            evidence_role=role,
            artifact_ref=f"{evidence_id}.xml",
            source_artifact_sha256=text_hash,
            citation=CITATION,
            source_locator="SECTION[1]",
            heading="Synthetic heading.",
            normalized_text=text,
            normalized_text_sha256=text_hash,
            parser_config_sha256=CONFIG_SHA,
        )
        path = tmp_path / f"{role.value}.json"
        path.write_text(snapshot.model_dump_json(indent=2) + "\n", encoding="utf-8")
        paths.append(path)

    assert (
        run(
            [
                "regulatory",
                "section-compare",
                "--annual",
                str(paths[0]),
                "--ecfr",
                str(paths[1]),
            ]
        )
        == 0
    )

    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "unresolved_difference"
    assert result["authority_state"] == "reconciliation_evidence_only"
    assert result["operational_authority"] == "none"
