"""Candidate-only deterministic interpretation of operational evidence records."""

from __future__ import annotations

import hashlib
from datetime import datetime

from .domain import (
    OperationalEvidenceBatch,
    OperationalInterpretationCandidate,
    OperationalInterpretationRule,
)


def interpret_operational_batch(
    batch: OperationalEvidenceBatch,
    *,
    rules: tuple[OperationalInterpretationRule, ...],
    interpreter_id: str,
    interpreter_version: str,
    interpreter_config_sha256: str,
    interpreted_at: datetime,
) -> tuple[OperationalInterpretationCandidate, ...]:
    """Apply exact source/event rules while preserving candidate-only authority."""
    candidates: list[OperationalInterpretationCandidate] = []
    for record in batch.records:
        for rule in sorted(rules, key=lambda item: item.rule_id):
            if rule.source_type is not record.source_type or rule.event_code != record.event_code:
                continue
            identity = (
                f"{batch.source_revision}\n{batch.source_artifact_sha256}\n"
                f"{batch.adapter_config_sha256}\n"
                f"{record.record_id}\n{record.raw_record_sha256}\n{rule.rule_id}"
            ).encode()
            candidate_id = "candidate:sha256:" + hashlib.sha256(identity).hexdigest()
            candidates.append(
                OperationalInterpretationCandidate(
                    candidate_id=candidate_id,
                    rule_id=rule.rule_id,
                    record_id=record.record_id,
                    raw_record_sha256=record.raw_record_sha256,
                    source_revision=batch.source_revision,
                    source_artifact_sha256=batch.source_artifact_sha256,
                    adapter_config_sha256=batch.adapter_config_sha256,
                    category=rule.category,
                    statement=rule.statement,
                    interpreter_id=interpreter_id,
                    interpreter_version=interpreter_version,
                    interpreter_config_sha256=interpreter_config_sha256,
                    interpreted_at=interpreted_at,
                )
            )
    return tuple(candidates)
