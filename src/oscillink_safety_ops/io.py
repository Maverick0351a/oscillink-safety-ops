"""Strict JSON loading and content-addressed fixture verification."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .domain import (
    OperationalEvidenceBatch,
    OperationalEvidenceRecord,
    OperationalReviewLedger,
    PhysicalIntelligenceEvidenceEnvelope,
    ProposedPlan,
    SafetyMemoryPacket,
)

MAX_JSON_BYTES = 1024 * 1024


class FixtureIntegrityError(ValueError):
    """Raised when fixture bytes do not match the pinned manifest."""


@dataclass(frozen=True)
class StoredOperationalArtifact:
    sha256: str
    relative_path: str
    byte_count: int


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_file(path: Path) -> str:
    """Return a prefixed SHA-256 for exact local file bytes."""
    return "sha256:" + _sha256(path)


def _json_object(path: Path) -> dict[str, Any]:
    if path.stat().st_size > MAX_JSON_BYTES:
        raise ValueError(f"input exceeds {MAX_JSON_BYTES} bytes")
    data: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def load_packet(path: Path) -> SafetyMemoryPacket:
    return SafetyMemoryPacket.model_validate(_json_object(path))


def load_plan(path: Path) -> ProposedPlan:
    return ProposedPlan.model_validate(_json_object(path))


def load_envelope(path: Path) -> PhysicalIntelligenceEvidenceEnvelope:
    return PhysicalIntelligenceEvidenceEnvelope.model_validate(_json_object(path))


def load_operational_review_ledger(path: Path) -> OperationalReviewLedger:
    """Load a bounded strict review ledger with exact candidate-hash validation."""
    return OperationalReviewLedger.model_validate(_json_object(path))


def load_operational_jsonl(
    path: Path,
    *,
    batch_id: str,
    source_revision: str,
    adapter_config_sha256: str,
) -> OperationalEvidenceBatch:
    """Normalize one bounded JSONL export without adding interpretation or control authority."""
    if path.stat().st_size > MAX_JSON_BYTES:
        raise ValueError(f"input exceeds {MAX_JSON_BYTES} bytes")
    raw = path.read_bytes()
    lines = raw.decode("utf-8").splitlines()
    if not lines:
        raise ValueError("operational JSONL export is empty")
    records: list[OperationalEvidenceRecord] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            raise ValueError(f"blank JSONL record at line {line_number}")
        data: Any = json.loads(line)
        if not isinstance(data, dict):
            raise ValueError(f"expected JSON object at line {line_number}")
        data["raw_record_sha256"] = "sha256:" + hashlib.sha256(line.encode("utf-8")).hexdigest()
        records.append(OperationalEvidenceRecord.model_validate(data))
    return OperationalEvidenceBatch(
        batch_id=batch_id,
        source_revision=source_revision,
        source_artifact_sha256="sha256:" + hashlib.sha256(raw).hexdigest(),
        adapter_config_sha256=adapter_config_sha256,
        records=tuple(records),
    )


def store_operational_export(source: Path, *, root: Path) -> StoredOperationalArtifact:
    """Store exact export bytes by hash under a caller-controlled local evidence root."""
    if source.stat().st_size > MAX_JSON_BYTES:
        raise ValueError(f"input exceeds {MAX_JSON_BYTES} bytes")
    content = source.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    relative = Path("artifacts") / "sha256" / digest[:2] / f"{digest}.jsonl"
    destination = root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        destination.write_bytes(content)
    return StoredOperationalArtifact(
        sha256="sha256:" + digest,
        relative_path=relative.as_posix(),
        byte_count=len(content),
    )


def verify_envelope_payload(
    envelope: PhysicalIntelligenceEvidenceEnvelope,
    *,
    root: Path,
) -> str:
    resolved_root = root.resolve()
    payload = (resolved_root / envelope.payload_ref).resolve()
    if not payload.is_relative_to(resolved_root) or not payload.is_file():
        raise FixtureIntegrityError(f"invalid envelope payload_ref: {envelope.payload_ref}")
    actual = "sha256:" + _sha256(payload)
    if actual != envelope.content_sha256:
        raise FixtureIntegrityError("envelope payload hash mismatch")
    return actual


def verify_manifest(path: Path) -> frozenset[str]:
    manifest = _json_object(path)
    entries = manifest.get("files")
    if not isinstance(entries, list):
        raise FixtureIntegrityError("manifest files must be a list")
    root = path.parent.resolve()
    verified: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise FixtureIntegrityError("manifest file entry must be an object")
        relative = entry.get("path")
        expected = entry.get("sha256")
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise FixtureIntegrityError("manifest path and sha256 must be strings")
        candidate = (root / relative).resolve()
        if not candidate.is_relative_to(root) or not candidate.is_file():
            raise FixtureIntegrityError(f"invalid fixture path: {relative}")
        actual = _sha256(candidate)
        if actual != expected:
            raise FixtureIntegrityError(f"hash mismatch for {relative}")
        verified.add("sha256:" + actual)
    return frozenset(verified)
