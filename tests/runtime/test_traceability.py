"""Deterministic assurance traceability gate tests."""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / "scripts" / "verify_traceability.py"
CANONICAL_VERIFIER = ROOT / "scripts" / "verify.py"
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
REQUIRED_HAZARD_FAMILIES = (
    "human-zone-entry",
    "unexpected-start",
    "command-actual-mismatch",
    "excessive-motion",
    "stale-missing-contradictory-sensing",
    "timebase-failure",
    "output-path-failure",
    "configuration-corruption",
    "process-restart",
    "reset-rearm-misuse",
    "production-ai-compromise",
    "shared-power-network-sensor-common-cause",
)


def _load_verifier() -> ModuleType:
    assert VERIFIER.is_file(), "traceability verifier is missing"
    spec = importlib.util.spec_from_file_location("verify_traceability", VERIFIER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_missing_assurance_artifacts_are_reported(tmp_path: Path) -> None:
    verifier = _load_verifier()

    errors = verifier.validate_traceability(tmp_path)

    assert errors == tuple(f"missing assurance artifact: {path}" for path in REQUIRED_ARTIFACTS)


def _write_valid_fixture(root: Path) -> None:
    assurance = root / "assurance"
    assurance.mkdir()
    contents = {
        "CLAIMS.md": "# Claims\n\nSCOPE-ROBOT-CELL-001\n",
        "SYSTEM_BOUNDARY.md": "# Boundary\n\nSCOPE-ROBOT-CELL-001\n",
        "INTENDED_USE.md": "# Intended use\n\nSCOPE-ROBOT-CELL-001\n",
        "FORESEEABLE_MISUSE.md": "# Misuse\n\nHAZ-001\n",
        "HAZARD_LOG.md": "# Hazards\n\nHAZ-001\n",
        "SAFETY_PLAN.md": "# Plan\n\nROLE-SAFETY-OWNER\n",
        "SAFETY_CONCEPT.md": "# Concept\n\nCTRL-001\n",
        "SAFETY_REQUIREMENTS.md": (
            "# Requirements\n\nSR-001\n\n"
            "PLr: TBD — qualified target-system assessment\n"
            "SIL: TBD — qualified target-system assessment\n"
            "Total stopping time: TBD — qualified target-system assessment\n"
            "Diagnostic coverage: TBD — qualified target-system assessment\n"
            "Application validation: TBD — qualified target-system assessment\n"
            "Unresolved common-cause assumptions: TBD — qualified target-system assessment\n"
        ),
        "FUNCTION_ALLOCATION.md": (
            "# Allocation\n\nALLOC-OBS-001\nALLOC-LOGIC-001\nALLOC-OUTPUT-001\n"
            "ALLOC-EXTCTRL-001\nALLOC-FINAL-001\n"
        ),
        "CHANGE_CONTROL.md": "# Change control\n\nCI-001\n",
        "TOOL_POLICY.md": "# Tool policy\n\nTOOL-001\n",
        "VALIDATION_PLAN.md": "# Validation\n\nTEST-001\n",
    }
    for name, content in contents.items():
        (assurance / name).write_text(content, encoding="utf-8")
    with (assurance / "TRACEABILITY.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
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
            ),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerow(
            {
                "trace_id": "TRC-001",
                "hazard_id": "HAZ-001",
                "requirement_id": "SR-001",
                "rationale": "Exclude hazardous motion whenever occupancy cannot be excluded.",
                "control_id": "CTRL-001",
                "allocation_ids": (
                    "ALLOC-OBS-001;ALLOC-LOGIC-001;ALLOC-OUTPUT-001;"
                    "ALLOC-EXTCTRL-001;ALLOC-FINAL-001"
                ),
                "test_id": "TEST-001",
                "evidence_id": "EVID-001",
                "owner": "ROLE-SAFETY-OWNER",
                "status": "planned",
                "change_impact_id": "CI-001",
            }
        )
    evidence_index = {
        "schema_version": "1.0",
        "scope_id": "SCOPE-ROBOT-CELL-001",
        "records": [
            {
                "evidence_id": "EVID-001",
                "evidence_type": "planned_test_result",
                "path": "planned/EVID-001.json",
                "owner": "ROLE-SAFETY-OWNER",
                "status": "planned",
                "requirement_ids": ["SR-001"],
                "test_ids": ["TEST-001"],
                "change_impact_id": "CI-001",
            }
        ],
    }
    (assurance / "evidence-index.json").write_text(
        json.dumps(evidence_index, indent=2) + "\n", encoding="utf-8"
    )


def test_orphan_traceability_reference_is_rejected(tmp_path: Path) -> None:
    verifier = _load_verifier()
    _write_valid_fixture(tmp_path)
    traceability = tmp_path / "assurance" / "TRACEABILITY.csv"
    text = traceability.read_text(encoding="utf-8").replace("SR-001", "SR-999")
    traceability.write_text(text, encoding="utf-8")

    errors = verifier.validate_traceability(tmp_path)

    assert "orphan requirement_id in TRC-001: SR-999" in errors


def test_malformed_traceability_identifier_is_rejected(tmp_path: Path) -> None:
    verifier = _load_verifier()
    _write_valid_fixture(tmp_path)
    traceability = tmp_path / "assurance" / "TRACEABILITY.csv"
    text = traceability.read_text(encoding="utf-8").replace("SR-001", "requirement-one")
    traceability.write_text(text, encoding="utf-8")

    errors = verifier.validate_traceability(tmp_path)

    assert "malformed requirement_id in TRC-001: requirement-one" in errors


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("hazard_id", "HAZ-001"),
        ("requirement_id", "SR-001"),
        ("rationale", "Exclude hazardous motion whenever occupancy cannot be excluded."),
        ("control_id", "CTRL-001"),
        (
            "allocation_ids",
            "ALLOC-OBS-001;ALLOC-LOGIC-001;ALLOC-OUTPUT-001;ALLOC-EXTCTRL-001;ALLOC-FINAL-001",
        ),
        ("test_id", "TEST-001"),
        ("evidence_id", "EVID-001"),
        ("owner", "ROLE-SAFETY-OWNER"),
        ("status", "planned"),
        ("change_impact_id", "CI-001"),
    ),
)
def test_trace_path_fields_are_required(tmp_path: Path, field: str, value: str) -> None:
    verifier = _load_verifier()
    _write_valid_fixture(tmp_path)
    traceability = tmp_path / "assurance" / "TRACEABILITY.csv"
    text = traceability.read_text(encoding="utf-8").replace(value, "", 1)
    traceability.write_text(text, encoding="utf-8")

    errors = verifier.validate_traceability(tmp_path)

    assert f"missing required trace field {field} in TRC-001" in errors


@pytest.mark.parametrize(
    ("document", "identifier", "field"),
    (
        ("HAZARD_LOG.md", "HAZ-002", "hazard_id"),
        ("SAFETY_REQUIREMENTS.md", "SR-002", "requirement_id"),
        ("SAFETY_CONCEPT.md", "CTRL-002", "control_id"),
        ("VALIDATION_PLAN.md", "TEST-002", "test_id"),
    ),
)
def test_declared_safety_ids_require_trace_rows(
    tmp_path: Path, document: str, identifier: str, field: str
) -> None:
    verifier = _load_verifier()
    _write_valid_fixture(tmp_path)
    path = tmp_path / "assurance" / document
    path.write_text(path.read_text(encoding="utf-8") + identifier + "\n", encoding="utf-8")

    errors = verifier.validate_traceability(tmp_path)

    assert f"untraced {field}: {identifier}" in errors


def test_complete_sensor_to_final_element_allocation_is_required(tmp_path: Path) -> None:
    verifier = _load_verifier()
    _write_valid_fixture(tmp_path)
    for name in ("FUNCTION_ALLOCATION.md", "TRACEABILITY.csv"):
        path = tmp_path / "assurance" / name
        text = path.read_text(encoding="utf-8").replace(";ALLOC-FINAL-001", "")
        text = text.replace("ALLOC-FINAL-001", "")
        path.write_text(text, encoding="utf-8")

    errors = verifier.validate_traceability(tmp_path)

    assert "missing required allocation: ALLOC-FINAL-001" in errors


@pytest.mark.parametrize(
    ("label", "invented_value"),
    (
        ("PLr", "e"),
        ("SIL", "2"),
        ("Total stopping time", "450 ms"),
        ("Diagnostic coverage", "99%"),
        ("Application validation", "complete"),
        ("Unresolved common-cause assumptions", "resolved"),
    ),
)
def test_target_system_assurance_values_remain_tbd(
    tmp_path: Path, label: str, invented_value: str
) -> None:
    verifier = _load_verifier()
    _write_valid_fixture(tmp_path)
    requirements = tmp_path / "assurance" / "SAFETY_REQUIREMENTS.md"
    text = requirements.read_text(encoding="utf-8").replace(
        f"{label}: TBD — qualified target-system assessment", f"{label}: {invented_value}"
    )
    requirements.write_text(text, encoding="utf-8")

    errors = verifier.validate_traceability(tmp_path)

    assert (
        f"target value must remain TBD pending qualified target-system assessment: {label}"
        in errors
    )


def test_evidence_index_references_are_validated(tmp_path: Path) -> None:
    verifier = _load_verifier()
    _write_valid_fixture(tmp_path)
    index_path = tmp_path / "assurance" / "evidence-index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    index["records"][0]["requirement_ids"] = ["SR-999"]
    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")

    errors = verifier.validate_traceability(tmp_path)

    assert "orphan requirement_id in EVID-001: SR-999" in errors


def test_duplicate_trace_and_requirement_ids_are_rejected(tmp_path: Path) -> None:
    verifier = _load_verifier()
    _write_valid_fixture(tmp_path)
    traceability = tmp_path / "assurance" / "TRACEABILITY.csv"
    lines = traceability.read_text(encoding="utf-8").splitlines()
    traceability.write_text("\n".join((*lines, lines[1])) + "\n", encoding="utf-8")

    errors = verifier.validate_traceability(tmp_path)

    assert "duplicate trace_id: TRC-001" in errors
    assert "duplicate requirement_id: SR-001" in errors


def test_malformed_evidence_json_is_reported_without_crashing(tmp_path: Path) -> None:
    verifier = _load_verifier()
    _write_valid_fixture(tmp_path)
    (tmp_path / "assurance" / "evidence-index.json").write_text("{", encoding="utf-8")

    errors = verifier.validate_traceability(tmp_path)

    assert errors == ("malformed evidence-index.json: invalid JSON",)


def test_evidence_index_must_be_a_nonempty_object(tmp_path: Path) -> None:
    verifier = _load_verifier()
    _write_valid_fixture(tmp_path)
    index_path = tmp_path / "assurance" / "evidence-index.json"

    index_path.write_text("[]\n", encoding="utf-8")
    assert verifier.validate_traceability(tmp_path) == (
        "malformed evidence-index.json: expected object",
    )

    index_path.write_text('{"schema_version":"1.0","records":[]}\n', encoding="utf-8")
    assert "empty evidence index" in verifier.validate_traceability(tmp_path)


@pytest.mark.parametrize(
    "field",
    (
        "evidence_id",
        "evidence_type",
        "path",
        "owner",
        "status",
        "requirement_ids",
        "test_ids",
        "change_impact_id",
    ),
)
def test_required_evidence_fields_are_reported_without_crashing(tmp_path: Path, field: str) -> None:
    verifier = _load_verifier()
    _write_valid_fixture(tmp_path)
    index_path = tmp_path / "assurance" / "evidence-index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    del index["records"][0][field]
    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")

    errors = verifier.validate_traceability(tmp_path)

    assert f"missing required evidence field {field} in evidence record 1" in errors


def test_duplicate_evidence_ids_are_rejected(tmp_path: Path) -> None:
    verifier = _load_verifier()
    _write_valid_fixture(tmp_path)
    index_path = tmp_path / "assurance" / "evidence-index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    index["records"].append(index["records"][0].copy())
    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")

    errors = verifier.validate_traceability(tmp_path)

    assert "duplicate evidence_id: EVID-001" in errors


def test_malformed_traceability_csv_is_reported_without_crashing(tmp_path: Path) -> None:
    verifier = _load_verifier()
    _write_valid_fixture(tmp_path)
    traceability = tmp_path / "assurance" / "TRACEABILITY.csv"
    traceability.write_text('"unterminated', encoding="utf-8")

    errors = verifier.validate_traceability(tmp_path)

    assert errors == ("malformed TRACEABILITY.csv: unexpected end of data",)


def test_traceability_csv_rejects_wrong_row_width(tmp_path: Path) -> None:
    verifier = _load_verifier()
    _write_valid_fixture(tmp_path)
    traceability = tmp_path / "assurance" / "TRACEABILITY.csv"
    lines = traceability.read_text(encoding="utf-8").splitlines()
    traceability.write_text("\n".join((lines[0], lines[1] + ",extra")) + "\n", encoding="utf-8")

    errors = verifier.validate_traceability(tmp_path)

    assert "malformed TRACEABILITY.csv row 2: expected 11 fields, got 12" in errors


def test_production_assurance_artifacts_are_complete() -> None:
    verifier = _load_verifier()

    assert verifier.validate_traceability(ROOT) == ()


def test_production_hazard_log_covers_every_mandatory_family() -> None:
    hazard_log = (ROOT / "assurance" / "HAZARD_LOG.md").read_text(encoding="utf-8")

    for family in REQUIRED_HAZARD_FAMILIES:
        assert f"Hazard family: `{family}`" in hazard_log


def test_canonical_verifier_runs_traceability_with_empty_pythonpath(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    verifier = _load_module(CANONICAL_VERIFIER, "canonical_verifier")
    for name in (
        "check_text_hygiene",
        "check_repository_surface",
        "check_schemas",
        "check_osha_catalog",
        "check_fixture",
    ):
        monkeypatch.setattr(verifier, name, lambda: None)
    calls: list[tuple[tuple[str, ...], dict[str, str]]] = []
    monkeypatch.setattr(verifier, "run", lambda *args, **kwargs: calls.append((args, kwargs)))

    verifier.main()

    assert (
        ("uv", "run", "python", "scripts/verify_traceability.py"),
        {"pythonpath": ""},
    ) in calls
