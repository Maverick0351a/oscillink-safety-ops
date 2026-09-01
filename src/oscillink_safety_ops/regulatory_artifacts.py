"""Bounded intake and deterministic extraction of untrusted regulatory artifacts."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal
from xml.etree.ElementTree import Element, ParseError

from defusedxml.ElementTree import fromstring

from .domain import (
    RegulatoryArtifactVerification,
    RegulatoryEvidenceRole,
    RegulatorySectionComparison,
    RegulatorySectionSnapshot,
    RegulatorySourceEvidence,
)

MAX_REGULATORY_ARTIFACT_BYTES = 16 * 1024 * 1024


class RegulatoryArtifactIntegrityError(ValueError):
    """Raised when local regulatory bytes do not match their declared evidence identity."""


def verify_regulatory_artifact(
    evidence: RegulatorySourceEvidence,
    *,
    artifact_ref: str,
    root: Path,
) -> RegulatoryArtifactVerification:
    """Verify bounded exact bytes under root without granting source or interpretation authority."""
    resolved_root = root.resolve()
    artifact = (resolved_root / artifact_ref).resolve()
    if not artifact.is_relative_to(resolved_root) or not artifact.is_file():
        raise RegulatoryArtifactIntegrityError(f"invalid regulatory artifact_ref: {artifact_ref}")
    byte_count = artifact.stat().st_size
    if byte_count > MAX_REGULATORY_ARTIFACT_BYTES:
        raise RegulatoryArtifactIntegrityError(
            f"regulatory artifact exceeds {MAX_REGULATORY_ARTIFACT_BYTES} bytes"
        )
    if byte_count != evidence.byte_count:
        raise RegulatoryArtifactIntegrityError("regulatory artifact byte count mismatch")
    digest = hashlib.sha256()
    with artifact.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    actual_sha256 = "sha256:" + digest.hexdigest()
    if actual_sha256 != evidence.artifact_sha256:
        raise RegulatoryArtifactIntegrityError("regulatory artifact hash mismatch")
    return RegulatoryArtifactVerification(
        evidence_id=evidence.evidence_id,
        artifact_ref=artifact_ref,
        artifact_sha256=actual_sha256,
        byte_count=byte_count,
    )


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].upper()


def _section_number(value: str) -> str:
    normalized = " ".join(value.replace("§", " ").split()).strip()
    lowered = normalized.lower()
    for prefix in ("sec. ", "section "):
        if lowered.startswith(prefix):
            return normalized[len(prefix) :].strip()
    return normalized


def _first_descendant_text(element: Element, name: str) -> str:
    match = next((item for item in element.iter() if _local_name(item.tag) == name), None)
    if match is None:
        return ""
    return " ".join("".join(match.itertext()).split())


def _section_identifier(element: Element) -> str:
    if element.attrib.get("TYPE", "").upper() == "SECTION":
        return element.attrib.get("N", "")
    if _local_name(element.tag) == "SECTION":
        return _first_descendant_text(element, "SECTNO")
    return ""


def extract_regulatory_section_xml(
    evidence: RegulatorySourceEvidence,
    *,
    artifact_ref: str,
    root: Path,
    citation: str,
    parser_config_sha256: str,
) -> RegulatorySectionSnapshot:
    """Extract one exact CFR section as untrusted candidate text from verified XML bytes."""
    verification = verify_regulatory_artifact(evidence, artifact_ref=artifact_ref, root=root)
    content = (root.resolve() / artifact_ref).resolve().read_bytes()
    upper_content = content.upper()
    if b"<!DOCTYPE" in upper_content or b"<!ENTITY" in upper_content:
        raise RegulatoryArtifactIntegrityError(
            "regulatory artifact contains unsafe XML declaration"
        )
    target = _section_number(citation.rsplit(" ", 1)[-1])
    try:
        document = fromstring(content)
    except ParseError as exc:
        raise RegulatoryArtifactIntegrityError("regulatory artifact is not valid XML") from exc
    matches = [
        element
        for element in document.iter()
        if _section_identifier(element) and _section_number(_section_identifier(element)) == target
    ]
    if len(matches) != 1:
        raise RegulatoryArtifactIntegrityError(
            f"expected exactly one XML section for {citation}; found {len(matches)}"
        )
    section = matches[0]
    heading = _first_descendant_text(section, "HEAD")
    source_number = _section_identifier(section)
    locator_key = "N"
    if not heading:
        subject = _first_descendant_text(section, "SUBJECT")
        heading = " ".join(part for part in (source_number, subject) if part)
        locator_key = "SECTNO"
    if not heading:
        raise RegulatoryArtifactIntegrityError(f"XML section has no heading: {citation}")
    normalized_text = " ".join(" ".join(section.itertext()).split())
    if not normalized_text:
        raise RegulatoryArtifactIntegrityError(f"XML section has no text: {citation}")
    return RegulatorySectionSnapshot(
        evidence_id=evidence.evidence_id,
        evidence_role=evidence.role,
        artifact_ref=verification.artifact_ref,
        source_artifact_sha256=verification.artifact_sha256,
        citation=citation,
        source_locator=f"{_local_name(section.tag)}[{locator_key}={source_number}]",
        heading=heading,
        normalized_text=normalized_text,
        normalized_text_sha256=(
            "sha256:" + hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
        ),
        parser_config_sha256=parser_config_sha256,
    )


def compare_cfr_section_snapshots(
    annual: RegulatorySectionSnapshot,
    ecfr: RegulatorySectionSnapshot,
) -> RegulatorySectionComparison:
    """Compare exact normalized source text without explaining or approving differences."""
    if annual.evidence_role is not RegulatoryEvidenceRole.ANNUAL_CFR_BASELINE:
        raise ValueError("annual snapshot must use annual_cfr_baseline evidence")
    if ecfr.evidence_role is not RegulatoryEvidenceRole.ECFR_POINT_IN_TIME:
        raise ValueError("eCFR snapshot must use ecfr_point_in_time evidence")
    if annual.citation != ecfr.citation:
        raise ValueError("regulatory section citations do not match")
    comparison_digest = hashlib.sha256(
        annual.model_dump_json().encode("utf-8") + b"\n" + ecfr.model_dump_json().encode("utf-8")
    ).hexdigest()
    matches = annual.normalized_text_sha256 == ecfr.normalized_text_sha256
    status: Literal["verified_match", "unresolved_difference"] = (
        "verified_match" if matches else "unresolved_difference"
    )
    rationale = (
        "normalized annual CFR and dated eCFR section text hashes match"
        if matches
        else (
            "annual CFR and dated eCFR section text differ; cited Federal Register and LSA "
            "evidence is required before the difference can be explained"
        )
    )
    return RegulatorySectionComparison(
        comparison_id="comparison:sha256:" + comparison_digest,
        citation=annual.citation,
        annual_evidence_id=annual.evidence_id,
        annual_artifact_sha256=annual.source_artifact_sha256,
        annual_text_sha256=annual.normalized_text_sha256,
        ecfr_evidence_id=ecfr.evidence_id,
        ecfr_artifact_sha256=ecfr.source_artifact_sha256,
        ecfr_text_sha256=ecfr.normalized_text_sha256,
        evidence_ids=(annual.evidence_id, ecfr.evidence_id),
        status=status,
        rationale=rationale,
    )
