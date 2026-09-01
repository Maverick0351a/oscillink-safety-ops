"""Deterministic review binding and stale-impact assessment for operational evidence."""

from __future__ import annotations

from .domain import (
    OperationalChangeImpact,
    OperationalEvidenceBatch,
    OperationalImpactReport,
    OperationalImpactState,
    OperationalInterpretationCandidate,
    OperationalReviewLedger,
)


def operational_candidate_sha256(candidate: OperationalInterpretationCandidate) -> str:
    """Return the canonical hash that an external review must bind."""
    return candidate.content_sha256()


def assess_operational_change_impact(
    ledger: OperationalReviewLedger,
    *,
    current_batch: OperationalEvidenceBatch,
) -> tuple[OperationalChangeImpact, ...]:
    """Compare reviewed candidates with current evidence without mutating review decisions."""
    current_records = {record.record_id: record for record in current_batch.records}
    reviews_by_candidate: dict[str, list[str]] = {}
    for review in ledger.reviews:
        reviews_by_candidate.setdefault(review.candidate_id, []).append(review.review_id)

    impacts: list[OperationalChangeImpact] = []
    for candidate in sorted(ledger.candidates, key=lambda item: item.candidate_id):
        current = current_records.get(candidate.record_id)
        current_record_sha256 = None if current is None else current.raw_record_sha256
        if current is None:
            state = OperationalImpactState.STALE_RECORD_MISSING
        elif current.raw_record_sha256 != candidate.raw_record_sha256:
            state = OperationalImpactState.STALE_RECORD_CHANGED
        elif current_batch.source_artifact_sha256 != candidate.source_artifact_sha256:
            state = OperationalImpactState.STALE_ARTIFACT_CHANGED
        elif current_batch.source_revision != candidate.source_revision:
            state = OperationalImpactState.STALE_SOURCE_REVISION_CHANGED
        elif current_batch.adapter_config_sha256 != candidate.adapter_config_sha256:
            state = OperationalImpactState.STALE_ADAPTER_CONFIG_CHANGED
        else:
            state = OperationalImpactState.CURRENT
        impacts.append(
            OperationalChangeImpact(
                candidate_id=candidate.candidate_id,
                state=state,
                prior_source_revision=candidate.source_revision,
                current_source_revision=current_batch.source_revision,
                prior_source_artifact_sha256=candidate.source_artifact_sha256,
                current_source_artifact_sha256=current_batch.source_artifact_sha256,
                prior_adapter_config_sha256=candidate.adapter_config_sha256,
                current_adapter_config_sha256=current_batch.adapter_config_sha256,
                prior_record_sha256=candidate.raw_record_sha256,
                current_record_sha256=current_record_sha256,
                affected_review_ids=tuple(
                    sorted(reviews_by_candidate.get(candidate.candidate_id, []))
                ),
            )
        )
    return tuple(impacts)


def build_operational_impact_report(
    ledger: OperationalReviewLedger,
    *,
    review_ledger_sha256: str,
    current_batch: OperationalEvidenceBatch,
) -> OperationalImpactReport:
    """Build a portable report bound to exact review-ledger and current-source bytes."""
    return OperationalImpactReport(
        review_ledger_sha256=review_ledger_sha256,
        current_batch_id=current_batch.batch_id,
        current_source_revision=current_batch.source_revision,
        current_source_artifact_sha256=current_batch.source_artifact_sha256,
        current_adapter_config_sha256=current_batch.adapter_config_sha256,
        impacts=assess_operational_change_impact(ledger, current_batch=current_batch),
    )
