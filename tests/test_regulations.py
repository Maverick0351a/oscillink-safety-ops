from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from oscillink_safety_ops.io import FixtureIntegrityError
from oscillink_safety_ops.regulations import (
    parse_osha_regulation_index,
    render_osha_catalog,
    validate_osha_catalog,
    write_content_addressed_regulation,
)

ROOT = Path(__file__).resolve().parents[1]


def test_osha_catalog_parser_preserves_every_official_part_as_unreviewed_authority() -> None:
    html = b"""
    <a href="/laws-regs/regulations/standardnumber/1910">
      Part 1910 - Occupational Safety and Health Standards
    </a>
    <a href="/laws-regs/regulations/standardnumber/1926">
      Part 1926 - Safety and Health Regulations for Construction
    </a>
    <a href="/laws-regs/regulations/standardnumber/1993">Part 1993 - [Reserved]</a>
    <a href="/unrelated">Ignore this link</a>
    """

    entries = parse_osha_regulation_index(html)

    assert [entry.part for entry in entries] == ["1910", "1926", "1993"]
    assert entries[0].title == "Occupational Safety and Health Standards"
    assert entries[0].osha_url == ("https://www.osha.gov/laws-regs/regulations/standardnumber/1910")
    assert entries[0].ecfr_url == "https://www.ecfr.gov/current/title-29/part-1910"
    assert entries[0].review_state == "unreviewed_source"
    assert entries[2].reserved is True


def test_osha_catalog_is_deterministic_and_does_not_approve_regulatory_text() -> None:
    html = b"""
    <a href="/laws-regs/regulations/standardnumber/70a">
      Part 70a - Protection of Individual Privacy in Records
    </a>
    <a href="/laws-regs/regulations/standardnumber/1910">
      Part 1910 - Occupational Safety and Health Standards
    </a>
    """

    first = render_osha_catalog(html, ecfr_as_of="2026-08-27")
    second = render_osha_catalog(html, ecfr_as_of="2026-08-27")

    catalog = json.loads(first)
    assert first == second
    assert catalog["catalog_id"] == "osha-regulations-standardnumber"
    assert catalog["source_count"] == 2
    assert catalog["sources"][0]["review_state"] == "unreviewed_source"
    assert catalog["sources"][0]["content_endpoint"] is None
    assert catalog["sources"][0]["content_status"] == "unavailable_in_ecfr_snapshot"
    assert catalog["sources"][1]["content_endpoint"] == (
        "https://www.ecfr.gov/api/versioner/v1/full/2026-08-27/title-29.xml?part=1910"
    )
    assert catalog["authority_notice"] == (
        "Source discovery only; no regulation is approved, applicable, or interpreted by this "
        "catalog."
    )


def test_committed_osha_catalog_covers_the_complete_official_index_without_approval() -> None:
    catalog = json.loads((ROOT / "knowledge" / "osha" / "catalog.json").read_text())

    assert validate_osha_catalog(catalog) == 67

    tampered = {**catalog, "sources": [*catalog["sources"]]}
    tampered["sources"][0] = {**tampered["sources"][0], "review_state": "approved"}
    with pytest.raises(ValueError, match="unreviewed_source"):
        validate_osha_catalog(tampered)


def test_regulation_bytes_are_stored_by_content_hash(tmp_path: Path) -> None:
    content = b"<ECFR><DIV1 N='1910'>Synthetic regulation bytes</DIV1></ECFR>\n"

    artifact = write_content_addressed_regulation(tmp_path, content)

    assert artifact.sha256 == (
        "sha256:a9bb9378a5b533d1a7b36c7b8d2a978d7aef7340aaef6b1cdbca80a356284149"
    )
    assert artifact.relative_path == (
        "artifacts/sha256/a9/a9bb9378a5b533d1a7b36c7b8d2a978d7aef7340aaef6b1cdbca80a356284149.xml"
    )
    assert (tmp_path / artifact.relative_path).read_bytes() == content


def test_regulation_storage_rejects_poisoned_existing_digest_path(tmp_path: Path) -> None:
    content = b"<ECFR><DIV1 N='1910'>Synthetic regulation bytes</DIV1></ECFR>\n"
    digest = hashlib.sha256(content).hexdigest()
    destination = tmp_path / "artifacts" / "sha256" / digest[:2] / f"{digest}.xml"
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"poisoned")

    with pytest.raises(FixtureIntegrityError, match="content-addressed destination hash mismatch"):
        write_content_addressed_regulation(tmp_path, content)

    assert destination.read_bytes() == b"poisoned"
