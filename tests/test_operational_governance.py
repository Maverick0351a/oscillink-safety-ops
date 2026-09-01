from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from oscillink_safety_ops.domain import (
    ObservationQuality,
    OperationalEvidenceBatch,
    OperationalEvidenceRecord,
    OperationalImpactState,
    OperationalInterpretationCandidate,
    OperationalInterpretationReview,
    OperationalRecordKind,
    OperationalReviewDecision,
    OperationalReviewLedger,
    OperationalSourceType,
)
from oscillink_safety_ops.governance import (
    assess_operational_change_impact,
    operational_candidate_sha256,
)
from oscillink_safety_ops.interpretation import interpret_operational_batch
from scripts.export_schemas import SCHEMAS

NOW = datetime(2026, 8, 31, tzinfo=UTC)
SHA_A = "sha256:" + "a" * 64
SHA_B = "sha256:" + "b" * 64
SHA_C = "sha256:" + "c" * 64
SHA_D = "sha256:" + "d" * 64


def autonomy_record(*, raw_record_sha256: str = SHA_B) -> OperationalEvidenceRecord:
    return OperationalEvidenceRecord(
        record_id="record:autonomy-001",
        source_type=OperationalSourceType.AUTONOMOUS_SYSTEM,
        record_kind=OperationalRecordKind.LOG,
        scope_id="cell:synthetic-robot-01",
        system_id="autonomy-stack:synthetic",
        component_id="planner:local",
        source_tag="planner.event",
        observed_at=NOW,
        raw_record_sha256=raw_record_sha256,
        raw_value=None,
        units=None,
        quality=ObservationQuality.GOOD,
        event_code="protective_stop_requested",
        message="Planner requested a protective stop.",
        missing_fields=("raw_value",),
    )


def batch(
    *,
    source_artifact_sha256: str = SHA_C,
    adapter_config_sha256: str = SHA_A,
    records: tuple[OperationalEvidenceRecord, ...] | None = None,
) -> OperationalEvidenceBatch:
    return OperationalEvidenceBatch(
        batch_id="batch:autonomy-001",
        source_revision="export:autonomy-001",
        source_artifact_sha256=source_artifact_sha256,
        adapter_config_sha256=adapter_config_sha256,
        records=records if records is not None else (autonomy_record(),),
    )


def candidate() -> OperationalInterpretationCandidate:
    from oscillink_safety_ops.domain import OperationalInterpretationRule

    return interpret_operational_batch(
        batch(),
        rules=(
            OperationalInterpretationRule(
                rule_id="rule:protective-stop-requested",
                source_type=OperationalSourceType.AUTONOMOUS_SYSTEM,
                event_code="protective_stop_requested",
                category="protective_stop_event",
                statement="Source log reports that a protective stop was requested.",
            ),
        ),
        interpreter_id="interpreter:exact-event-map",
        interpreter_version="1.0.0",
        interpreter_config_sha256=SHA_A,
        interpreted_at=NOW,
    )[0]


def review(*, candidate_sha256: str | None = None) -> OperationalInterpretationReview:
    item = candidate()
    return OperationalInterpretationReview(
        review_id="review:synthetic-001",
        candidate_id=item.candidate_id,
        candidate_sha256=candidate_sha256 or operational_candidate_sha256(item),
        decision=OperationalReviewDecision.ACCEPTED_INTERPRETATION,
        reviewer_id="reviewer:synthetic-external",
        reviewer_role="role:authorized-safety-reviewer",
        reviewer_authority_ref="authority:synthetic-site-matrix-v1",
        reviewed_at=NOW,
        rationale="Synthetic acceptance of the interpretation only.",
    )


def ledger() -> OperationalReviewLedger:
    item = candidate()
    return OperationalReviewLedger(candidates=(item,), reviews=(review(),))


def test_external_review_accepts_only_the_interpretation_without_operational_authority() -> None:
    result = ledger()

    assert result.reviews[0].decision is OperationalReviewDecision.ACCEPTED_INTERPRETATION
    assert result.reviews[0].authority_state == "review_record_only"
    assert result.reviews[0].operational_authority == "none"
    assert "approved_to_operate" not in result.model_dump_json().lower()


def test_review_ledger_rejects_a_review_bound_to_different_candidate_bytes() -> None:
    item = candidate()

    with pytest.raises(ValidationError, match="candidate_sha256 does not match"):
        OperationalReviewLedger(candidates=(item,), reviews=(review(candidate_sha256=SHA_D),))


def test_retracted_review_requires_and_preserves_same_candidate_lineage() -> None:
    item = candidate()
    accepted = review()
    retracted = OperationalInterpretationReview(
        review_id="review:synthetic-retraction-001",
        candidate_id=item.candidate_id,
        candidate_sha256=operational_candidate_sha256(item),
        decision=OperationalReviewDecision.RETRACTED_INTERPRETATION,
        reviewer_id="reviewer:synthetic-external",
        reviewer_role="role:authorized-safety-reviewer",
        reviewer_authority_ref="authority:synthetic-site-matrix-v1",
        reviewed_at=NOW,
        rationale="Synthetic retraction of the prior interpretation review.",
        supersedes_review_id=accepted.review_id,
    )

    result = OperationalReviewLedger(candidates=(item,), reviews=(accepted, retracted))

    assert result.reviews[1].supersedes_review_id == accepted.review_id
    assert result.reviews[1].operational_authority == "none"


def test_changed_record_stales_the_candidate_and_every_dependent_review() -> None:
    changed = batch(records=(autonomy_record(raw_record_sha256=SHA_D),))

    impact = assess_operational_change_impact(ledger(), current_batch=changed)

    assert len(impact) == 1
    assert impact[0].state is OperationalImpactState.STALE_RECORD_CHANGED
    assert impact[0].affected_review_ids == ("review:synthetic-001",)
    assert impact[0].prior_record_sha256 == SHA_B
    assert impact[0].current_record_sha256 == SHA_D
    assert impact[0].authority_state == "change_evidence_only"


def test_changed_artifact_stales_candidate_even_when_record_bytes_are_unchanged() -> None:
    changed = batch(source_artifact_sha256=SHA_D)

    impact = assess_operational_change_impact(ledger(), current_batch=changed)

    assert impact[0].state is OperationalImpactState.STALE_ARTIFACT_CHANGED
    assert impact[0].prior_source_artifact_sha256 == SHA_C
    assert impact[0].current_source_artifact_sha256 == SHA_D


def test_changed_adapter_configuration_stales_candidate_on_unchanged_source_bytes() -> None:
    changed = batch(adapter_config_sha256=SHA_D)

    impact = assess_operational_change_impact(ledger(), current_batch=changed)

    assert impact[0].state is OperationalImpactState.STALE_ADAPTER_CONFIG_CHANGED
    assert impact[0].prior_adapter_config_sha256 == SHA_A
    assert impact[0].current_adapter_config_sha256 == SHA_D


def test_missing_record_remains_explicit_and_does_not_auto_resolve_review() -> None:
    impact = assess_operational_change_impact(ledger(), current_batch=batch(records=()))

    assert impact[0].state is OperationalImpactState.STALE_RECORD_MISSING
    assert impact[0].current_record_sha256 is None
    assert impact[0].affected_review_ids == ("review:synthetic-001",)


def test_unchanged_candidate_and_source_remain_current() -> None:
    impact = assess_operational_change_impact(ledger(), current_batch=batch())

    assert impact[0].state is OperationalImpactState.CURRENT
    assert impact[0].current_record_sha256 == impact[0].prior_record_sha256


def test_review_and_change_impact_schemas_preserve_no_authority_boundary() -> None:
    ledger_schema = SCHEMAS["operational-review-ledger.schema.json"]
    impact_schema = SCHEMAS["operational-change-impact.schema.json"]
    report_schema = SCHEMAS["operational-impact-report.schema.json"]

    assert ledger_schema["properties"]["operational_authority"]["const"] == "none"
    assert impact_schema["properties"]["authority_state"]["const"] == ("change_evidence_only")
    assert report_schema["properties"]["operational_authority"]["const"] == "none"
