from __future__ import annotations

import json
from pathlib import Path

import pytest

from oscillink_safety_ops.evaluation import validate_hidden_task_bank
from scripts.export_schemas import SCHEMAS


def _task(task_id: str, task_class: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "task_id": task_id,
        "task_class": task_class,
        "private_prompt": "Evaluator-only synthetic prompt.",
        "subject_success_definition": "Return one cited evidence state and rationale.",
        "gold_state": "missing_evidence",
        "fixture_sha256": "sha256:" + "a" * 64,
        "verification_method": "Compare exact state and required citation identity.",
        "failure_categories": ["wrong_state", "missing_citation"],
    }


def _write_bank(path: Path, tasks: list[dict[str, object]]) -> None:
    path.write_text("".join(json.dumps(item) + "\n" for item in tasks), encoding="utf-8")


def test_hidden_bank_validator_reports_only_counts_and_hash(tmp_path: Path) -> None:
    bank = tmp_path / "tasks.jsonl"
    _write_bank(bank, [_task("task-001", "staleness"), _task("task-002", "authority")])

    result = validate_hidden_task_bank(bank, expected_class_counts={"authority": 1, "staleness": 1})

    assert result.record_count == 2
    assert result.class_counts == {"authority": 1, "staleness": 1}
    assert result.bank_sha256.startswith("sha256:")
    assert "prompt" not in result.model_dump_json().lower()
    assert "gold" not in result.model_dump_json().lower()


def test_hidden_bank_validator_rejects_duplicate_ids(tmp_path: Path) -> None:
    bank = tmp_path / "tasks.jsonl"
    _write_bank(bank, [_task("task-001", "staleness"), _task("task-001", "authority")])

    with pytest.raises(ValueError, match="duplicate task_id"):
        validate_hidden_task_bank(bank, expected_class_counts={"authority": 1, "staleness": 1})


def test_hidden_bank_validator_rejects_unbalanced_frozen_design(tmp_path: Path) -> None:
    bank = tmp_path / "tasks.jsonl"
    _write_bank(bank, [_task("task-001", "staleness")])

    with pytest.raises(ValueError, match="class counts"):
        validate_hidden_task_bank(bank, expected_class_counts={"authority": 1, "staleness": 1})


def test_public_hidden_evaluation_artifacts_disclose_no_private_labels() -> None:
    root = Path(__file__).parents[1]
    manifest_text = (root / "evaluations" / "hidden-evaluation-v1-manifest.json").read_text(
        encoding="utf-8"
    )
    manifest = json.loads(manifest_text)

    assert manifest["record_count"] == 12
    assert manifest["execution_state"] == "not_executed"
    assert "private_prompt" not in manifest_text
    assert "gold_state" not in manifest_text
    schema = SCHEMAS["hidden-evaluation-validation.schema.json"]
    assert schema["additionalProperties"] is False
    assert schema["properties"]["disclosure_state"]["default"] == "counts_and_hash_only"
