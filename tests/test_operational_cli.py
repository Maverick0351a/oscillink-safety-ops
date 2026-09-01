from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from oscillink_safety_ops.cli import run
from oscillink_safety_ops.domain import (
    ObservationQuality,
    OperationalInterpretationReview,
    OperationalInterpretationRule,
    OperationalRecordKind,
    OperationalReviewDecision,
    OperationalReviewLedger,
    OperationalSourceType,
)
from oscillink_safety_ops.governance import operational_candidate_sha256
from oscillink_safety_ops.interpretation import interpret_operational_batch
from oscillink_safety_ops.io import (
    load_operational_jsonl,
    load_operational_review_ledger,
)

NOW = datetime(2026, 8, 31, tzinfo=UTC)
SHA_A = "sha256:" + "a" * 64


def exported_record(*, message: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "record_id": "record:autonomy-001",
        "source_type": OperationalSourceType.AUTONOMOUS_SYSTEM,
        "record_kind": OperationalRecordKind.LOG,
        "scope_id": "cell:synthetic-robot-01",
        "system_id": "autonomy-stack:synthetic",
        "component_id": "planner:local",
        "source_tag": "planner.event",
        "observed_at": NOW.isoformat().replace("+00:00", "Z"),
        "raw_value": None,
        "units": None,
        "quality": ObservationQuality.GOOD,
        "calibration_revision": None,
        "event_code": "protective_stop_requested",
        "message": message,
        "missing_fields": ["raw_value"],
        "unsupported_fields": [],
        "authority_state": "observational_evidence",
        "access_mode": "read_only",
        "content_treatment": "untrusted_data",
    }


def write_export(path: Path, *, message: str) -> None:
    path.write_text(json.dumps(exported_record(message=message), sort_keys=True) + "\n")


def write_ledger(tmp_path: Path) -> Path:
    source = tmp_path / "prior.jsonl"
    write_export(source, message="Planner requested a protective stop.")
    batch = load_operational_jsonl(
        source,
        batch_id="batch:autonomy-prior",
        source_revision="export:autonomy-001",
        adapter_config_sha256=SHA_A,
    )
    candidate = interpret_operational_batch(
        batch,
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
    review = OperationalInterpretationReview(
        review_id="review:synthetic-001",
        candidate_id=candidate.candidate_id,
        candidate_sha256=operational_candidate_sha256(candidate),
        decision=OperationalReviewDecision.ACCEPTED_INTERPRETATION,
        reviewer_id="reviewer:synthetic-external",
        reviewer_role="role:authorized-safety-reviewer",
        reviewer_authority_ref="authority:synthetic-site-matrix-v1",
        reviewed_at=NOW,
        rationale="Synthetic acceptance of the interpretation only.",
    )
    path = tmp_path / "ledger.json"
    path.write_text(
        OperationalReviewLedger(candidates=(candidate,), reviews=(review,)).model_dump_json(
            indent=2
        )
        + "\n"
    )
    return path


def test_review_ledger_loader_is_bounded_strict_and_hash_bound(tmp_path: Path) -> None:
    path = write_ledger(tmp_path)

    ledger = load_operational_review_ledger(path)

    assert ledger.reviews[0].candidate_sha256 == operational_candidate_sha256(ledger.candidates[0])

    tampered = json.loads(path.read_text())
    tampered["command"] = "acknowledge_alarm"
    path.write_text(json.dumps(tampered))
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        load_operational_review_ledger(path)


def test_cli_validates_review_ledger_deterministically(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ledger = write_ledger(tmp_path)
    argv = ["operational", "review-validate", "--ledger", str(ledger)]

    assert run(argv) == 0
    first = capsys.readouterr().out
    assert run(argv) == 0
    second = capsys.readouterr().out

    assert first == second
    result = json.loads(first)
    assert result["operational_authority"] == "none"
    assert result["reviews"][0]["decision"] == "accepted_interpretation"


def test_cli_emits_stale_impact_when_current_record_bytes_change(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ledger = write_ledger(tmp_path)
    current = tmp_path / "current.jsonl"
    write_export(current, message="Planner requested a protective stop after a source change.")

    assert (
        run(
            [
                "operational",
                "impact",
                "--ledger",
                str(ledger),
                "--current-input",
                str(current),
                "--batch-id",
                "batch:autonomy-current",
                "--source-revision",
                "export:autonomy-002",
                "--adapter-config-sha256",
                SHA_A,
            ]
        )
        == 0
    )

    result = json.loads(capsys.readouterr().out)
    assert result["review_ledger_sha256"].startswith("sha256:")
    assert result["current_source_artifact_sha256"].startswith("sha256:")
    assert result["impacts"][0]["state"] == "stale_record_changed"
    assert result["impacts"][0]["affected_review_ids"] == ["review:synthetic-001"]
    assert result["impacts"][0]["operational_authority"] == "none"
