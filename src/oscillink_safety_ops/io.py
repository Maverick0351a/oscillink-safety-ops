"""Strict JSON loading and content-addressed fixture verification."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .domain import (
    OperationalEvidenceBatch,
    OperationalEvidenceRecord,
    OperationalReviewLedger,
    OperationalSequenceFinding,
    PhysicalIntelligenceEvidenceEnvelope,
    ProposedPlan,
    RecordedEpisodeEvidence,
    RegulatorySectionSnapshot,
    RegulatorySourceEvidence,
    SafetyEvidencePacket,
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


@dataclass(frozen=True)
class _SequenceState:
    sequence_number: int
    record_id: str


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


def load_safety_evidence_packet(path: Path) -> SafetyEvidencePacket:
    return SafetyEvidencePacket.model_validate(_json_object(path))


def load_recorded_episode(path: Path) -> RecordedEpisodeEvidence:
    return RecordedEpisodeEvidence.model_validate(_json_object(path))


def load_envelope(path: Path) -> PhysicalIntelligenceEvidenceEnvelope:
    return PhysicalIntelligenceEvidenceEnvelope.model_validate(_json_object(path))


def load_regulatory_source_evidence(path: Path) -> RegulatorySourceEvidence:
    """Load one bounded strict official-source evidence declaration."""
    return RegulatorySourceEvidence.model_validate(_json_object(path))


def load_regulatory_section_snapshot(path: Path) -> RegulatorySectionSnapshot:
    """Load one bounded strict regulatory section extraction candidate."""
    return RegulatorySectionSnapshot.model_validate(_json_object(path))


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
    findings: list[OperationalSequenceFinding] = []
    stream_states: dict[str, _SequenceState] = {}
    latest_observed_at: dict[str, datetime] = {}
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            raise ValueError(f"blank JSONL record at line {line_number}")
        data: Any = json.loads(line)
        if not isinstance(data, dict):
            raise ValueError(f"expected JSON object at line {line_number}")
        if data.get("adapter_warnings"):
            raise ValueError("adapter_warnings is reserved for adapter-derived evidence")
        data.pop("adapter_warnings", None)
        data["raw_record_sha256"] = "sha256:" + hashlib.sha256(line.encode("utf-8")).hexdigest()
        if data.get("sequence_number") is None:
            data["adapter_warnings"] = ("sequence_number_missing",)
        record = OperationalEvidenceRecord.model_validate(data)
        stream_key = "|".join(
            (record.scope_id, record.system_id, record.component_id, record.source_tag)
        )
        prior = stream_states.get(stream_key)
        prior_observed_at = latest_observed_at.get(stream_key)
        warnings = list(record.adapter_warnings)
        if prior_observed_at is not None and record.observed_at < prior_observed_at:
            warnings.append("observed_at_out_of_order")
        if prior_observed_at is None or record.observed_at > prior_observed_at:
            latest_observed_at[stream_key] = record.observed_at
        if warnings != list(record.adapter_warnings):
            record = record.model_copy(update={"adapter_warnings": tuple(warnings)})
        if record.sequence_number is not None:
            if prior is not None:
                finding_data: dict[str, Any] | None = None
                if record.sequence_number == prior.sequence_number:
                    finding_data = {"state": "duplicate_sequence"}
                elif record.sequence_number < prior.sequence_number:
                    finding_data = {"state": "out_of_order"}
                elif record.sequence_number > prior.sequence_number + 1:
                    finding_data = {
                        "state": "sequence_gap",
                        "missing_sequence_start": prior.sequence_number + 1,
                        "missing_sequence_end": record.sequence_number - 1,
                    }
                if finding_data is not None:
                    findings.append(
                        OperationalSequenceFinding(
                            **finding_data,
                            stream_key=stream_key,
                            previous_record_id=prior.record_id,
                            current_record_id=record.record_id,
                            previous_sequence_number=prior.sequence_number,
                            current_sequence_number=record.sequence_number,
                        )
                    )
            if prior is None or record.sequence_number > prior.sequence_number:
                stream_states[stream_key] = _SequenceState(
                    sequence_number=record.sequence_number,
                    record_id=record.record_id,
                )
        records.append(record)
    return OperationalEvidenceBatch(
        batch_id=batch_id,
        source_revision=source_revision,
        source_artifact_sha256="sha256:" + hashlib.sha256(raw).hexdigest(),
        adapter_config_sha256=adapter_config_sha256,
        records=tuple(records),
        sequence_findings=tuple(findings),
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
