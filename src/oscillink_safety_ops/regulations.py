"""Provider-neutral cataloging of official OSHA regulation sources."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Literal

OSHA_INDEX_URL = "https://www.osha.gov/laws-regs/regulations/standardnumber"
_PART_PATH = re.compile(r"^/laws-regs/regulations/standardnumber/([0-9]+[a-z]?)$")
_ECFR_UNAVAILABLE_PARTS = {"70a"}


@dataclass(frozen=True)
class OshaRegulationSource:
    part: str
    title: str
    osha_url: str
    ecfr_url: str
    reserved: bool
    review_state: Literal["unreviewed_source"] = "unreviewed_source"


@dataclass(frozen=True)
class RegulationArtifact:
    sha256: str
    relative_path: str
    byte_count: int


class _OshaIndexParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._href: str | None = None
        self._text: list[str] = []
        self.entries: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or self._href is None:
            return
        match = _PART_PATH.fullmatch(self._href)
        if match is not None:
            text = " ".join("".join(self._text).split())
            self.entries.append((match.group(1), text))
        self._href = None
        self._text = []


def parse_osha_regulation_index(content: bytes) -> tuple[OshaRegulationSource, ...]:
    """Parse the official OSHA standard-number index without approving its content."""
    parser = _OshaIndexParser()
    parser.feed(content.decode("utf-8"))
    entries: list[OshaRegulationSource] = []
    seen: set[str] = set()
    for part, label in parser.entries:
        if part in seen:
            continue
        seen.add(part)
        title = re.sub(rf"^Part\s+{re.escape(part)}\s*-\s*", "", label)
        entries.append(
            OshaRegulationSource(
                part=part,
                title=title,
                osha_url=f"{OSHA_INDEX_URL}/{part}",
                ecfr_url=f"https://www.ecfr.gov/current/title-29/part-{part}",
                reserved=title.casefold() == "[reserved]",
            )
        )
    return tuple(entries)


def render_osha_catalog(content: bytes, *, ecfr_as_of: str) -> str:
    """Render a deterministic source catalog; this does not review or interpret regulations."""
    sources: list[dict[str, object]] = []
    for entry in parse_osha_regulation_index(content):
        source = asdict(entry)
        if entry.part in _ECFR_UNAVAILABLE_PARTS:
            source["content_endpoint"] = None
            source["content_status"] = "unavailable_in_ecfr_snapshot"
        else:
            source["content_endpoint"] = (
                "https://www.ecfr.gov/api/versioner/v1/full/"
                f"{ecfr_as_of}/title-29.xml?part={entry.part}"
            )
            source["content_status"] = "available"
        sources.append(source)
    catalog = {
        "schema_version": 1,
        "catalog_id": "osha-regulations-standardnumber",
        "index_url": OSHA_INDEX_URL,
        "index_sha256": "sha256:" + hashlib.sha256(content).hexdigest(),
        "ecfr_as_of": ecfr_as_of,
        "ecfr_status_notice": (
            "The eCFR is continuously updated and is not an official legal edition of the CFR."
        ),
        "official_annual_cfr_url": "https://www.govinfo.gov/app/collection/cfr",
        "authority_notice": (
            "Source discovery only; no regulation is approved, applicable, or interpreted by this "
            "catalog."
        ),
        "source_count": len(sources),
        "sources": sources,
    }
    return json.dumps(catalog, indent=2, sort_keys=True) + "\n"


def validate_osha_catalog(catalog: dict[str, Any]) -> int:
    """Fail closed if a committed catalog widens authority or loses source identity."""
    sources = catalog.get("sources")
    if not isinstance(sources, list) or catalog.get("source_count") != len(sources):
        raise ValueError("OSHA catalog source_count mismatch")
    parts: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("OSHA catalog source must be an object")
        part = source.get("part")
        if not isinstance(part, str) or not part or part in parts:
            raise ValueError("OSHA catalog parts must be unique non-empty strings")
        parts.add(part)
        if source.get("review_state") != "unreviewed_source":
            raise ValueError("OSHA catalog sources must remain unreviewed_source")
        if source.get("osha_url") != f"{OSHA_INDEX_URL}/{part}":
            raise ValueError("OSHA catalog source URL is outside the official index")
        endpoint = source.get("content_endpoint")
        status = source.get("content_status")
        if status == "unavailable_in_ecfr_snapshot" and endpoint is None:
            continue
        if (
            status != "available"
            or not isinstance(endpoint, str)
            or not endpoint.startswith("https://www.ecfr.gov/api/versioner/v1/full/")
        ):
            raise ValueError("OSHA catalog content endpoint is not official eCFR")
    return len(parts)


def write_content_addressed_regulation(root: Path, content: bytes) -> RegulationArtifact:
    """Store immutable regulation bytes without granting them review or applicability state."""
    digest = hashlib.sha256(content).hexdigest()
    relative = Path("artifacts") / "sha256" / digest[:2] / f"{digest}.xml"
    destination = root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        destination.write_bytes(content)
    return RegulationArtifact(
        sha256="sha256:" + digest,
        relative_path=relative.as_posix(),
        byte_count=len(content),
    )
