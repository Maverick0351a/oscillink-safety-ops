"""Leakage-controlled hidden evaluation task-bank validation."""

from __future__ import annotations

import hashlib
from collections import Counter
from pathlib import Path

from pydantic import AwareDatetime, Field

from .domain import ContractModel, FindingState, NonEmptyStr, Sha256

MAX_HIDDEN_BANK_BYTES = 4 * 1024 * 1024


class HiddenEvaluationTask(ContractModel):
    schema_version: int = Field(default=1, ge=1, le=1)
    task_id: NonEmptyStr
    task_class: NonEmptyStr
    private_prompt: NonEmptyStr
    subject_success_definition: NonEmptyStr
    gold_state: FindingState
    fixture_sha256: Sha256
    verification_method: NonEmptyStr
    failure_categories: tuple[NonEmptyStr, ...]


class HiddenEvaluationValidation(ContractModel):
    schema_version: int = Field(default=1, ge=1, le=1)
    record_count: int = Field(ge=1)
    class_counts: dict[str, int]
    bank_sha256: Sha256
    validated_at: AwareDatetime | None = None
    disclosure_state: str = Field(default="counts_and_hash_only", pattern="^counts_and_hash_only$")


def validate_hidden_task_bank(
    path: Path,
    *,
    expected_class_counts: dict[str, int],
) -> HiddenEvaluationValidation:
    """Validate private tasks while returning no prompts, labels, or checks."""
    if not path.is_file():
        raise ValueError("hidden task bank is not a regular file")
    content = path.read_bytes()
    if not content or len(content) > MAX_HIDDEN_BANK_BYTES:
        raise ValueError("hidden task bank size is invalid")
    tasks: list[HiddenEvaluationTask] = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        if not line.strip():
            raise ValueError(f"blank hidden task record at line {line_number}")
        try:
            tasks.append(HiddenEvaluationTask.model_validate_json(line))
        except ValueError as exc:
            raise ValueError(f"invalid hidden task record at line {line_number}") from exc
    task_ids = [item.task_id for item in tasks]
    if len(task_ids) != len(set(task_ids)):
        raise ValueError("duplicate task_id in hidden task bank")
    class_counts = dict(sorted(Counter(item.task_class for item in tasks).items()))
    if class_counts != dict(sorted(expected_class_counts.items())):
        raise ValueError("hidden task bank class counts do not match frozen design")
    return HiddenEvaluationValidation(
        record_count=len(tasks),
        class_counts=class_counts,
        bank_sha256="sha256:" + hashlib.sha256(content).hexdigest(),
    )
