"""Conservative official-change evidence collection for regulatory source review."""

from __future__ import annotations

import hashlib
import re
from calendar import monthrange
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Literal

from defusedxml.ElementTree import fromstring

from .domain import (
    FederalRegisterAction,
    FederalRegisterChangeCandidate,
    FederalRegisterChangeChain,
    LsaCoverageCandidate,
    RegulatoryArtifactVerification,
    RegulatoryChangeEvidenceBundle,
    RegulatoryDifferenceReview,
    RegulatoryDifferenceReviewDecision,
    RegulatoryEvidenceRole,
    RegulatoryReconciliationFinding,
    RegulatoryReconciliationStatus,
    RegulatorySectionComparison,
    RegulatorySourceEvidence,
    ReviewedRegulatoryDifference,
)
from .regulatory_artifacts import RegulatoryArtifactIntegrityError, verify_regulatory_artifact


class _GovInfoHtmlTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._in_pre = False
        self._in_title = False
        self.pre: list[str] = []
        self.title: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        self._in_pre = tag.lower() == "pre" or self._in_pre
        self._in_title = tag.lower() == "title" or self._in_title

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "pre":
            self._in_pre = False
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_pre:
            self.pre.append(data)
        if self._in_title:
            self.title.append(data)


def _verified_content(
    evidence: RegulatorySourceEvidence,
    *,
    artifact_ref: str,
    root: Path,
) -> tuple[RegulatoryArtifactVerification, bytes]:
    verification = verify_regulatory_artifact(evidence, artifact_ref=artifact_ref, root=root)
    return verification, (root.resolve() / artifact_ref).resolve().read_bytes()


def _parse_english_date(value: str) -> date:
    for pattern in ("%A, %B %d, %Y", "%B %d, %Y", "%B %d %Y"):
        try:
            return datetime.strptime(value, pattern).date()
        except ValueError:
            continue
    raise ValueError(f"unsupported official publication date: {value}")


def _normalized_element_text(element: object) -> str:
    if not hasattr(element, "itertext"):
        return ""
    return " ".join("".join(element.itertext()).split())


def _fr_action(raw_instruction: str) -> FederalRegisterAction:
    lowered = raw_instruction.lower()
    if "redesignat" in lowered:
        return FederalRegisterAction.REDESIGNATE
    if "removed" in lowered or "remove " in lowered:
        return FederalRegisterAction.REMOVE
    if "correct" in lowered:
        return FederalRegisterAction.CORRECT
    if "delay" in lowered and "effective" in lowered:
        return FederalRegisterAction.DELAY_EFFECTIVE_DATE
    if any(token in lowered for token in ("amend", "revis", "add")):
        return FederalRegisterAction.AMEND
    return FederalRegisterAction.UNKNOWN


def extract_federal_register_change_candidates(
    evidence: RegulatorySourceEvidence,
    *,
    artifact_ref: str,
    root: Path,
    citation: str,
    parser_config_sha256: str,
) -> tuple[FederalRegisterChangeCandidate, ...]:
    """Extract exact amendment paragraphs from one verified GovInfo Federal Register XML issue."""
    if evidence.role is not RegulatoryEvidenceRole.FEDERAL_REGISTER_CHANGE:
        raise ValueError("Federal Register evidence role is required")
    verification, content = _verified_content(evidence, artifact_ref=artifact_ref, root=root)
    upper_content = content.upper()
    if b"<!DOCTYPE" in upper_content or b"<!ENTITY" in upper_content:
        raise RegulatoryArtifactIntegrityError(
            "regulatory artifact contains unsafe XML declaration"
        )
    document = fromstring(content)
    issue_date_element = next((node for node in document if node.tag.upper() == "DATE"), None)
    if issue_date_element is None:
        raise ValueError("Federal Register issue has no publication date")
    publication_date = _parse_english_date(_normalized_element_text(issue_date_element))
    section_number = citation.rsplit(" ", 1)[-1]
    candidates: list[FederalRegisterChangeCandidate] = []
    documents = [node for node in document.iter() if node.tag.upper() in {"RULE", "CORRECT"}]
    for document_index, item in enumerate(documents, start=1):
        frdoc = next((node for node in item.iter() if node.tag.upper() == "FRDOC"), None)
        page = next((node for node in item.iter() if node.tag.upper() == "PRTPAGE"), None)
        dates = next(
            (node for node in item.iter() if node.tag.upper() in {"DATES", "EFFDATE"}), None
        )
        if frdoc is None or page is None:
            continue
        document_match = re.search(r"FR Doc\.\s+([A-Za-z0-9-]+)", _normalized_element_text(frdoc))
        page_text = page.attrib.get("P", "")
        if document_match is None or not page_text.isdigit():
            continue
        effective_date: date | None = None
        if dates is not None:
            date_match = re.search(
                r"effective(?:\s+date)?(?:\s+is|\s+on)?\s+([A-Z][a-z]+\s+\d{1,2},\s+\d{4})",
                _normalized_element_text(dates),
                flags=re.IGNORECASE,
            )
            if date_match is not None:
                effective_date = _parse_english_date(date_match.group(1).title())
        paragraphs = [node for node in item.iter() if node.tag.upper() == "AMDPAR"]
        for paragraph_index, paragraph in enumerate(paragraphs, start=1):
            raw_instruction = _normalized_element_text(paragraph)
            if not re.search(rf"(?:§\s*)?{re.escape(section_number)}\b", raw_instruction):
                continue
            raw_sha256 = "sha256:" + hashlib.sha256(raw_instruction.encode()).hexdigest()
            identity = hashlib.sha256(
                f"{verification.artifact_sha256}\n{document_match.group(1)}\n{paragraph_index}\n{citation}".encode()
            ).hexdigest()
            candidates.append(
                FederalRegisterChangeCandidate(
                    candidate_id=f"fr-change:sha256:{identity}",
                    evidence_id=evidence.evidence_id,
                    source_artifact_sha256=verification.artifact_sha256,
                    document_number=document_match.group(1),
                    publication_date=publication_date,
                    effective_date=effective_date,
                    federal_register_start_page=int(page_text),
                    action=_fr_action(raw_instruction),
                    affected_citations=(citation,),
                    source_locator=f"{item.tag}[{document_index}]/AMDPAR[{paragraph_index}]",
                    raw_instruction=raw_instruction,
                    raw_instruction_sha256=raw_sha256,
                    parser_identity="govinfo-federal-register-xml",
                    parser_config_sha256=parser_config_sha256,
                )
            )
    if not candidates:
        raise ValueError(f"no exact Federal Register amendment paragraph found for {citation}")
    return tuple(candidates)


def extract_lsa_coverage_candidate(
    evidence: RegulatorySourceEvidence,
    *,
    artifact_ref: str,
    root: Path,
    citation: str,
    parser_config_sha256: str,
) -> LsaCoverageCandidate:
    """Extract one exact section entry from a verified GovInfo monthly LSA HTML granule."""
    if evidence.role is not RegulatoryEvidenceRole.LSA_CHANGE_INDEX:
        raise ValueError("LSA evidence role is required")
    verification, content = _verified_content(evidence, artifact_ref=artifact_ref, root=root)
    parser = _GovInfoHtmlTextParser()
    parser.feed(content.decode("utf-8"))
    title = " ".join("".join(parser.title).split())
    issue_match = re.search(r"LSA\),\s+([A-Z][a-z]+)\s+(\d{4})", title)
    if issue_match is None:
        raise ValueError("unsupported LSA issue title")
    month = datetime.strptime(issue_match.group(1), "%B").month
    year = int(issue_match.group(2))
    through_date = date(year, month, monthrange(year, month)[1])
    section_number = citation.rsplit(" ", 1)[-1]
    entry_pattern = re.compile(
        rf"(?m)^{re.escape(section_number)}\s+(.+?)\.+\s*([0-9][0-9, ]*)\s*$"
    )
    matches = list(entry_pattern.finditer("".join(parser.pre)))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one LSA entry for {citation}; found {len(matches)}")
    match = matches[0]
    raw_entry = match.group(0).strip()
    pages = tuple(int(value) for value in re.findall(r"\d+", match.group(2)))
    raw_sha256 = "sha256:" + hashlib.sha256(raw_entry.encode()).hexdigest()
    identity = hashlib.sha256(
        f"{verification.artifact_sha256}\n{citation}\n{raw_sha256}".encode()
    ).hexdigest()
    return LsaCoverageCandidate(
        candidate_id=f"lsa:sha256:{identity}",
        evidence_id=evidence.evidence_id,
        source_artifact_sha256=verification.artifact_sha256,
        through_date=through_date,
        citation=citation,
        status_text=match.group(1).strip(),
        federal_register_pages=pages,
        source_locator=f"pre/entry[{section_number}]",
        raw_entry=raw_entry,
        raw_entry_sha256=raw_sha256,
        parser_identity="govinfo-lsa-html",
        parser_config_sha256=parser_config_sha256,
    )


def build_federal_register_change_chain(
    citation: str,
    candidates: tuple[FederalRegisterChangeCandidate, ...],
) -> FederalRegisterChangeChain:
    """Resolve explicit publication lineage while preserving unsupported and withdrawn states."""
    if not candidates:
        raise ValueError("Federal Register change chain requires at least one candidate")
    if any(citation not in item.affected_citations for item in candidates):
        raise ValueError("Federal Register change chain candidate does not cover citation")
    publication_order = tuple(item.publication_date for item in candidates)
    if publication_order != tuple(sorted(publication_order)):
        raise ValueError("Federal Register change chain must be in publication order")
    document_numbers = [item.document_number for item in candidates]
    if len(document_numbers) != len(set(document_numbers)):
        raise ValueError("Federal Register change chain contains duplicate document numbers")

    seen_documents: set[str] = set()
    controlling_effective_date: date | None = None
    chain_state: Literal["effective_date_established", "withdrawn", "unsupported_chain"] = (
        "unsupported_chain"
    )
    unresolved_reasons: list[str] = []
    linked_actions = {
        FederalRegisterAction.CORRECT,
        FederalRegisterAction.DELAY_EFFECTIVE_DATE,
        FederalRegisterAction.WITHDRAW,
    }
    for item in candidates:
        if item.action in linked_actions:
            if (
                item.related_document_number is None
                or item.related_document_number not in seen_documents
            ):
                raise ValueError(
                    "correction, delay, or withdrawal requires an explicit related "
                    "Federal Register document"
                )
        if item.action is FederalRegisterAction.UNKNOWN:
            unresolved_reasons.append(f"unsupported action in {item.document_number}")
        elif item.action is FederalRegisterAction.WITHDRAW:
            chain_state = "withdrawn"
            controlling_effective_date = None
        elif item.effective_date is not None and chain_state != "withdrawn":
            controlling_effective_date = item.effective_date
            chain_state = "effective_date_established"
        seen_documents.add(item.document_number)

    if unresolved_reasons:
        chain_state = "unsupported_chain"
    elif controlling_effective_date is None and chain_state != "withdrawn":
        unresolved_reasons.append("no controlling effective date established")
        chain_state = "unsupported_chain"
    digest = hashlib.sha256(
        "\n".join((citation, *(item.candidate_id for item in candidates))).encode()
    ).hexdigest()
    return FederalRegisterChangeChain(
        chain_id=f"fr-change-chain:sha256:{digest}",
        citation=citation,
        candidates=candidates,
        chain_state=chain_state,
        controlling_effective_date=controlling_effective_date,
        unresolved_reasons=tuple(unresolved_reasons),
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
    document_numbers = set(lsa_coverage.federal_register_document_numbers)
    page_references = set(lsa_coverage.federal_register_pages)
    if any(
        item.document_number not in document_numbers
        and item.federal_register_start_page not in page_references
        for item in amendments
    ):
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
