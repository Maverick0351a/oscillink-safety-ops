"""Validate the assurance lifecycle and traceability artifacts."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

REQUIRED_ARTIFACTS = (
    "assurance/CLAIMS.md",
    "assurance/SYSTEM_BOUNDARY.md",
    "assurance/INTENDED_USE.md",
    "assurance/FORESEEABLE_MISUSE.md",
    "assurance/HAZARD_LOG.md",
    "assurance/SAFETY_PLAN.md",
    "assurance/SAFETY_CONCEPT.md",
    "assurance/SAFETY_REQUIREMENTS.md",
    "assurance/FUNCTION_ALLOCATION.md",
    "assurance/TRACEABILITY.csv",
    "assurance/CHANGE_CONTROL.md",
    "assurance/TOOL_POLICY.md",
    "assurance/VALIDATION_PLAN.md",
    "assurance/evidence-index.json",
)
ID_PATTERNS = {
    "trace_id": re.compile(r"TRC-\d{3}"),
    "hazard_id": re.compile(r"HAZ-\d{3}"),
    "requirement_id": re.compile(r"SR-\d{3}"),
    "control_id": re.compile(r"CTRL-\d{3}"),
    "allocation_ids": re.compile(r"ALLOC-(?:OBS|LOGIC|OUTPUT|EXTCTRL|FINAL)-\d{3}"),
    "test_id": re.compile(r"TEST-\d{3}"),
    "evidence_id": re.compile(r"EVID-\d{3}"),
    "owner": re.compile(r"ROLE-[A-Z][A-Z0-9-]*"),
    "change_impact_id": re.compile(r"CI-\d{3}"),
}
TRACE_FIELDS = (
    "trace_id",
    "hazard_id",
    "requirement_id",
    "rationale",
    "control_id",
    "allocation_ids",
    "test_id",
    "evidence_id",
    "owner",
    "status",
    "change_impact_id",
)
ALLOWED_STATUSES = {"planned", "implemented", "verified", "blocked", "retired"}
REQUIRED_ALLOCATIONS = {
    "ALLOC-OBS-001",
    "ALLOC-LOGIC-001",
    "ALLOC-OUTPUT-001",
    "ALLOC-EXTCTRL-001",
    "ALLOC-FINAL-001",
}
TARGET_SYSTEM_TBDS = (
    "PLr",
    "SIL",
    "Total stopping time",
    "Diagnostic coverage",
    "Application validation",
    "Unresolved common-cause assumptions",
)
EVIDENCE_FIELDS = (
    "evidence_id",
    "evidence_type",
    "path",
    "owner",
    "status",
    "requirement_ids",
    "test_ids",
    "change_impact_id",
)


def _document_ids(path: Path, prefix: str) -> set[str]:
    return set(re.findall(rf"\b{re.escape(prefix)}-[A-Z0-9-]+\b", path.read_text(encoding="utf-8")))


def validate_traceability(root: Path) -> tuple[str, ...]:
    """Return deterministic traceability validation errors."""
    errors = [
        f"missing assurance artifact: {relative}"
        for relative in REQUIRED_ARTIFACTS
        if not (root / relative).is_file()
    ]
    if errors:
        return tuple(errors)

    assurance = root / "assurance"
    try:
        evidence_index = json.loads((assurance / "evidence-index.json").read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        return ("malformed evidence-index.json: invalid UTF-8",)
    except json.JSONDecodeError:
        return ("malformed evidence-index.json: invalid JSON",)
    if not isinstance(evidence_index, dict):
        return ("malformed evidence-index.json: expected object",)
    evidence_records = evidence_index.get("records")
    if not isinstance(evidence_records, list):
        return ("malformed evidence-index.json: records must be an array",)
    if not evidence_records:
        errors.append("empty evidence index")

    requirements_text = (assurance / "SAFETY_REQUIREMENTS.md").read_text(encoding="utf-8")
    for label in TARGET_SYSTEM_TBDS:
        marker = f"{label}: TBD — qualified target-system assessment"
        if marker not in requirements_text:
            errors.append(
                "target value must remain TBD pending qualified target-system assessment: " + label
            )
    known_ids = {
        "hazard_id": _document_ids(assurance / "HAZARD_LOG.md", "HAZ"),
        "requirement_id": _document_ids(assurance / "SAFETY_REQUIREMENTS.md", "SR"),
        "control_id": _document_ids(assurance / "SAFETY_CONCEPT.md", "CTRL"),
        "allocation_ids": _document_ids(assurance / "FUNCTION_ALLOCATION.md", "ALLOC"),
        "test_id": _document_ids(assurance / "VALIDATION_PLAN.md", "TEST"),
        "owner": _document_ids(assurance / "SAFETY_PLAN.md", "ROLE"),
        "change_impact_id": _document_ids(assurance / "CHANGE_CONTROL.md", "CI"),
    }
    known_ids["evidence_id"] = set()
    seen_evidence_ids: set[str] = set()
    for record_number, record in enumerate(evidence_records, start=1):
        if not isinstance(record, dict):
            errors.append(f"malformed evidence record {record_number}: expected object")
            continue
        evidence_id_value = record.get("evidence_id")
        evidence_label = (
            evidence_id_value
            if isinstance(evidence_id_value, str) and evidence_id_value
            else f"evidence record {record_number}"
        )
        for field in EVIDENCE_FIELDS:
            value = record.get(field)
            if value is None or value == "" or value == []:
                errors.append(
                    f"missing required evidence field {field} in evidence record {record_number}"
                )
        if isinstance(evidence_id_value, str) and evidence_id_value:
            if ID_PATTERNS["evidence_id"].fullmatch(evidence_id_value) is None:
                errors.append(
                    f"malformed evidence_id in evidence record {record_number}: {evidence_id_value}"
                )
            if evidence_id_value in seen_evidence_ids:
                errors.append(f"duplicate evidence_id: {evidence_id_value}")
            seen_evidence_ids.add(evidence_id_value)
            known_ids["evidence_id"].add(evidence_id_value)
        for field in ("evidence_type", "path", "owner", "status", "change_impact_id"):
            value = record.get(field)
            if value is not None and not isinstance(value, str):
                errors.append(f"malformed evidence field {field} in {evidence_label}")
        owner = record.get("owner")
        if isinstance(owner, str) and owner:
            if ID_PATTERNS["owner"].fullmatch(owner) is None:
                errors.append(f"malformed owner in {evidence_label}: {owner}")
            elif owner not in known_ids["owner"]:
                errors.append(f"orphan owner in {evidence_label}: {owner}")
        status = record.get("status")
        if isinstance(status, str) and status and status not in ALLOWED_STATUSES:
            errors.append(f"malformed status in {evidence_label}: {status}")
        change_impact_id = record.get("change_impact_id")
        if isinstance(change_impact_id, str) and change_impact_id:
            if ID_PATTERNS["change_impact_id"].fullmatch(change_impact_id) is None:
                errors.append(f"malformed change_impact_id in {evidence_label}: {change_impact_id}")
            elif change_impact_id not in known_ids["change_impact_id"]:
                errors.append(f"orphan change_impact_id in {evidence_label}: {change_impact_id}")
        for field, known_field in (
            ("requirement_ids", "requirement_id"),
            ("test_ids", "test_id"),
        ):
            values = record.get(field)
            if values is None:
                continue
            if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
                errors.append(f"malformed evidence field {field} in {evidence_label}")
                continue
            for value in values:
                if ID_PATTERNS[known_field].fullmatch(value) is None:
                    errors.append(f"malformed {known_field} in {evidence_label}: {value}")
                elif value not in known_ids[known_field]:
                    errors.append(f"orphan {known_field} in {evidence_label}: {value}")
    for allocation_id in sorted(REQUIRED_ALLOCATIONS - known_ids["allocation_ids"]):
        errors.append(f"missing required allocation: {allocation_id}")
    try:
        with (assurance / "TRACEABILITY.csv").open(encoding="utf-8", newline="") as handle:
            table = list(csv.reader(handle, strict=True))
    except UnicodeDecodeError:
        return tuple((*errors, "malformed TRACEABILITY.csv: invalid UTF-8"))
    except csv.Error as exc:
        return tuple((*errors, f"malformed TRACEABILITY.csv: {exc}"))
    if not table:
        return tuple((*errors, "malformed TRACEABILITY.csv: empty file"))
    if tuple(table[0]) != TRACE_FIELDS:
        return tuple((*errors, "malformed TRACEABILITY.csv header"))
    rows: list[dict[str, str]] = []
    for row_number, values in enumerate(table[1:], start=2):
        if len(values) != len(TRACE_FIELDS):
            errors.append(
                f"malformed TRACEABILITY.csv row {row_number}: "
                f"expected {len(TRACE_FIELDS)} fields, got {len(values)}"
            )
        rows.append(dict(zip(TRACE_FIELDS, values, strict=False)))
    for unique_field in ("trace_id", "requirement_id"):
        values = [row.get(unique_field) for row in rows if row.get(unique_field)]
        seen: set[str] = set()
        for value in values:
            if value in seen:
                errors.append(f"duplicate {unique_field}: {value}")
            seen.add(value)
    coverage_fields = ("hazard_id", "requirement_id", "control_id", "test_id", "evidence_id")
    traced_ids = {field: set() for field in coverage_fields}
    for row_number, row in enumerate(rows, start=2):
        trace_id = row.get("trace_id") or f"row {row_number}"
        for field in coverage_fields:
            traced_ids[field].update(value for value in (row.get(field) or "").split(";") if value)
        for field in TRACE_FIELDS:
            if not (row.get(field) or "").strip():
                errors.append(f"missing required trace field {field} in {trace_id}")
        if row.get("status") and row["status"] not in ALLOWED_STATUSES:
            errors.append(f"malformed status in {trace_id}: {row['status']}")
        for field, pattern in ID_PATTERNS.items():
            values = (row.get(field) or "").split(";")
            for value in values:
                if value and pattern.fullmatch(value) is None:
                    errors.append(f"malformed {field} in {trace_id}: {value}")
        for field, allowed in known_ids.items():
            values = (row.get(field) or "").split(";")
            for value in values:
                if value and value not in allowed:
                    errors.append(f"orphan {field} in {trace_id}: {value}")
    for field in coverage_fields:
        for identifier in sorted(known_ids[field] - traced_ids[field]):
            errors.append(f"untraced {field}: {identifier}")
    return tuple(errors)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    errors = validate_traceability(root)
    if errors:
        raise SystemExit("\n".join(errors))
    print("traceability: ok")


if __name__ == "__main__":
    main()
