from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from oscillink_safety_ops.domain import (
    ObservationQuality,
    OperationalEvidenceBatch,
    OperationalEvidenceRecord,
    OperationalInterpretationRule,
    OperationalRecordKind,
    OperationalSourceType,
)
from oscillink_safety_ops.interpretation import interpret_operational_batch
from oscillink_safety_ops.io import (
    load_operational_jsonl,
    store_operational_export,
    verify_manifest,
)
from scripts.export_schemas import SCHEMAS

NOW = datetime(2026, 8, 31, tzinfo=UTC)
SHA_A = "sha256:" + "a" * 64
SHA_B = "sha256:" + "b" * 64
ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "operational_evidence"


def record(**updates: object) -> OperationalEvidenceRecord:
    values: dict[str, object] = {
        "record_id": "record:synthetic-ammonia-001",
        "source_type": OperationalSourceType.AMMONIA_DETECTION,
        "record_kind": OperationalRecordKind.MEASUREMENT,
        "scope_id": "facility:synthetic-001",
        "system_id": "system:ammonia-detection",
        "component_id": "detector:nh3-01",
        "source_tag": "NH3_DETECTOR_01.PPM",
        "observed_at": NOW,
        "raw_value": 175.0,
        "units": "ppm",
        "quality": ObservationQuality.BAD,
        "calibration_revision": "calibration:synthetic-expired",
        "raw_record_sha256": SHA_B,
    }
    values.update(updates)
    return OperationalEvidenceRecord.model_validate(values)


def test_operational_record_preserves_bad_quality_without_safety_interpretation() -> None:
    result = record()

    assert result.raw_value == 175.0
    assert result.quality is ObservationQuality.BAD
    assert result.authority_state == "observational_evidence"
    assert result.access_mode == "read_only"
    assert "safe" not in result.model_dump_json().lower()


def test_missing_record_requires_explicit_missing_value_accounting() -> None:
    result = record(
        raw_value=None,
        units=None,
        quality=ObservationQuality.MISSING,
        missing_fields=("raw_value", "units"),
    )

    assert result.raw_value is None
    assert result.missing_fields == ("raw_value", "units")

    with pytest.raises(ValidationError, match="missing quality requires raw_value"):
        record(raw_value=0, quality=ObservationQuality.MISSING)


def test_operational_record_rejects_control_or_alarm_authority_fields() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        OperationalEvidenceRecord.model_validate(
            {**record().model_dump(), "alarm_acknowledge": True}
        )


def test_operational_batch_rejects_duplicate_record_identity() -> None:
    item = record()

    with pytest.raises(ValidationError, match="duplicate record_id"):
        OperationalEvidenceBatch(
            batch_id="batch:synthetic-001",
            source_revision="export:synthetic-001",
            source_artifact_sha256=SHA_B,
            adapter_config_sha256=SHA_A,
            records=(item, item),
        )


def test_autonomous_system_log_is_preserved_as_untrusted_observation() -> None:
    result = record(
        record_id="record:autonomy-001",
        source_type=OperationalSourceType.AUTONOMOUS_SYSTEM,
        record_kind=OperationalRecordKind.LOG,
        scope_id="cell:synthetic-robot-01",
        system_id="autonomy-stack:synthetic",
        component_id="planner:local",
        source_tag="planner.event",
        raw_value=None,
        units=None,
        quality=ObservationQuality.GOOD,
        calibration_revision=None,
        event_code="protective_stop_requested",
        message="Planner requested a protective stop.",
        missing_fields=("raw_value",),
    )

    assert result.message == "Planner requested a protective stop."
    assert result.source_type is OperationalSourceType.AUTONOMOUS_SYSTEM
    assert result.authority_state == "observational_evidence"


def test_jsonl_loader_preserves_export_order_quality_and_source_hash(tmp_path: Path) -> None:
    fire = record(
        record_id="record:synthetic-fire-001",
        source_type=OperationalSourceType.FIRE_SUPPRESSION,
        record_kind=OperationalRecordKind.EVENT,
        system_id="system:fire-suppression",
        component_id="panel:fire-01",
        source_tag="FIRE_PANEL_01.SUPERVISORY",
        raw_value="active",
        units=None,
        quality=ObservationQuality.GOOD,
        calibration_revision=None,
        event_code="supervisory",
    )
    ammonia = record()
    path = tmp_path / "operational.jsonl"
    path.write_text(
        "\n".join(
            json.dumps(item.model_dump(mode="json"), sort_keys=True) for item in (fire, ammonia)
        )
        + "\n",
        encoding="utf-8",
    )

    batch = load_operational_jsonl(
        path,
        batch_id="batch:synthetic-001",
        source_revision="export:synthetic-001",
        adapter_config_sha256=SHA_A,
    )

    assert [item.record_id for item in batch.records] == [fire.record_id, ammonia.record_id]
    assert batch.records[1].quality is ObservationQuality.BAD
    assert batch.source_artifact_sha256.startswith("sha256:")
    assert batch.access_mode == "read_only"


def test_jsonl_loader_rejects_embedded_control_surface(tmp_path: Path) -> None:
    exported = record().model_dump(mode="json")
    exported["alarm_acknowledge"] = True
    path = tmp_path / "operational.jsonl"
    path.write_text(json.dumps(exported) + "\n", encoding="utf-8")

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        load_operational_jsonl(
            path,
            batch_id="batch:synthetic-001",
            source_revision="export:synthetic-001",
            adapter_config_sha256=SHA_A,
        )


def test_jsonl_loader_reports_sequence_gaps_and_out_of_order_records(tmp_path: Path) -> None:
    first = record(record_id="record:seq-10").model_dump(mode="json")
    gap = record(record_id="record:seq-12").model_dump(mode="json")
    late = record(record_id="record:seq-11").model_dump(mode="json")
    first["sequence_number"] = 10
    gap["sequence_number"] = 12
    late["sequence_number"] = 11
    late["observed_at"] = "2026-08-30T23:59:00Z"
    path = tmp_path / "sequenced.jsonl"
    path.write_text(
        "".join(json.dumps(item, sort_keys=True) + "\n" for item in (first, gap, late)),
        encoding="utf-8",
    )

    batch = load_operational_jsonl(
        path,
        batch_id="batch:sequenced",
        source_revision="export:sequenced",
        adapter_config_sha256=SHA_A,
    )

    assert [item.state for item in batch.sequence_findings] == ["sequence_gap", "out_of_order"]
    assert batch.sequence_findings[0].missing_sequence_start == 11
    assert batch.sequence_findings[0].missing_sequence_end == 11
    assert batch.records[2].adapter_warnings == ("observed_at_out_of_order",)


def test_jsonl_loader_marks_missing_sequence_and_rejects_source_adapter_warnings(
    tmp_path: Path,
) -> None:
    exported = record().model_dump(mode="json")
    path = tmp_path / "missing-sequence.jsonl"
    path.write_text(json.dumps(exported) + "\n", encoding="utf-8")

    batch = load_operational_jsonl(
        path,
        batch_id="batch:missing-sequence",
        source_revision="export:missing-sequence",
        adapter_config_sha256=SHA_A,
    )
    assert batch.records[0].adapter_warnings == ("sequence_number_missing",)

    exported["adapter_warnings"] = ["source_attempted_to_hide_parse_error"]
    path.write_text(json.dumps(exported) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="adapter_warnings is reserved"):
        load_operational_jsonl(
            path,
            batch_id="batch:forbidden-warning",
            source_revision="export:forbidden-warning",
            adapter_config_sha256=SHA_A,
        )


def test_jsonl_loader_rejects_oversized_export(tmp_path: Path) -> None:
    path = tmp_path / "operational.jsonl"
    path.write_bytes(b" " * (1024 * 1024 + 1))

    with pytest.raises(ValueError, match="input exceeds"):
        load_operational_jsonl(
            path,
            batch_id="batch:synthetic-001",
            source_revision="export:synthetic-001",
            adapter_config_sha256=SHA_A,
        )


def test_autonomous_log_interpretation_remains_a_deterministic_candidate() -> None:
    log = record(
        record_id="record:autonomy-001",
        source_type=OperationalSourceType.AUTONOMOUS_SYSTEM,
        record_kind=OperationalRecordKind.LOG,
        scope_id="cell:synthetic-robot-01",
        system_id="autonomy-stack:synthetic",
        component_id="planner:local",
        source_tag="planner.event",
        raw_value=None,
        units=None,
        quality=ObservationQuality.GOOD,
        calibration_revision=None,
        event_code="protective_stop_requested",
        message="Planner requested a protective stop.",
        missing_fields=("raw_value",),
    )
    rule = OperationalInterpretationRule(
        rule_id="rule:protective-stop-requested",
        source_type=OperationalSourceType.AUTONOMOUS_SYSTEM,
        event_code="protective_stop_requested",
        category="protective_stop_event",
        statement="Source log reports that a protective stop was requested.",
    )

    candidates = interpret_operational_batch(
        OperationalEvidenceBatch(
            batch_id="batch:autonomy-001",
            source_revision="export:autonomy-001",
            source_artifact_sha256=SHA_B,
            adapter_config_sha256=SHA_A,
            records=(log,),
        ),
        rules=(rule,),
        interpreter_id="interpreter:exact-event-map",
        interpreter_version="1.0.0",
        interpreter_config_sha256=SHA_A,
        interpreted_at=NOW,
    )

    assert len(candidates) == 1
    assert candidates[0].record_id == log.record_id
    assert candidates[0].raw_record_sha256 == log.raw_record_sha256
    assert candidates[0].review_state == "candidate"
    assert candidates[0].authority_state == "no_operational_authority"
    assert "command" not in candidates[0].model_dump_json().lower()


def test_operational_export_is_stored_by_exact_content_hash(tmp_path: Path) -> None:
    source = tmp_path / "autonomy.jsonl"
    source.write_text('{"event":"synthetic"}\n', encoding="utf-8")

    artifact = store_operational_export(source, root=tmp_path / "store")

    stored = tmp_path / "store" / artifact.relative_path
    assert stored.read_bytes() == source.read_bytes()
    assert artifact.sha256.startswith("sha256:")
    assert artifact.relative_path.endswith(".jsonl")


def test_pinned_operational_fixture_covers_fire_ammonia_and_autonomy() -> None:
    verified = verify_manifest(FIXTURE / "manifest.json")
    batch = load_operational_jsonl(
        FIXTURE / "synthetic-operational.jsonl",
        batch_id="batch:synthetic-operational-001",
        source_revision="export:synthetic-operational-001",
        adapter_config_sha256=SHA_A,
    )

    assert [record.source_type for record in batch.records] == [
        OperationalSourceType.FIRE_SUPPRESSION,
        OperationalSourceType.AMMONIA_DETECTION,
        OperationalSourceType.AUTONOMOUS_SYSTEM,
    ]
    assert batch.source_artifact_sha256 in verified


def test_operational_contract_schemas_preserve_candidate_only_authority() -> None:
    batch_schema = SCHEMAS["operational-evidence-batch.schema.json"]
    candidate_schema = SCHEMAS["operational-interpretation-candidate.schema.json"]

    assert "records" in batch_schema["properties"]
    assert candidate_schema["properties"]["review_state"]["const"] == "candidate"
    assert candidate_schema["properties"]["authority_state"]["const"] == (
        "no_operational_authority"
    )
