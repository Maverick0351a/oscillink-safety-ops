from __future__ import annotations

import importlib
import json
import re
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
APPROVED_HEADLINE = (
    "Oscillink Safety Ops is an independent safety and risk-mitigation supervisor for "
    "AI-controlled industrial equipment, connecting machine intent, observed behavior, and "
    "safety-manager oversight."
)


def test_repository_surface_reports_missing_required_file(tmp_path: Path) -> None:
    validate = importlib.import_module(
        "scripts.verify_repository_surface"
    ).validate_repository_surface

    errors = validate(tmp_path)

    assert "missing required repository file: CODE_OF_CONDUCT.md" in errors


def test_repository_surface_requires_publication_audit(tmp_path: Path) -> None:
    validate = importlib.import_module(
        "scripts.verify_repository_surface"
    ).validate_repository_surface

    assert (
        "missing required repository file: docs/audits/publication-readiness-2026-09-01.md"
        in validate(tmp_path)
    )


def test_repository_surface_requires_release_candidate_evidence(tmp_path: Path) -> None:
    validate = importlib.import_module(
        "scripts.verify_repository_surface"
    ).validate_repository_surface

    assert "missing required repository file: docs/audits/release-candidate-0.1.0a1.md" in validate(
        tmp_path
    )


def test_repository_surface_requires_prerelease_notes(tmp_path: Path) -> None:
    validate = importlib.import_module(
        "scripts.verify_repository_surface"
    ).validate_repository_surface

    assert "missing required repository file: docs/releases/v0.1.0-alpha.2.md" in validate(tmp_path)


def test_repository_surface_requires_private_pilot_gates(tmp_path: Path) -> None:
    validate = importlib.import_module(
        "scripts.verify_repository_surface"
    ).validate_repository_surface

    assert "missing required repository file: docs/milestones/private-pilot-gates.md" in validate(
        tmp_path
    )


def test_current_repository_has_complete_required_surface() -> None:
    validate = importlib.import_module(
        "scripts.verify_repository_surface"
    ).validate_repository_surface

    assert validate(ROOT) == ()


def test_repository_surface_rejects_required_file_without_boundary_text(tmp_path: Path) -> None:
    module = importlib.import_module("scripts.verify_repository_surface")
    for relative in module.REQUIRED_FILES:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("placeholder\n", encoding="utf-8")

    errors = module.validate_repository_surface(tmp_path)

    assert (
        "missing required text in SECURITY.md: Use GitHub private vulnerability reporting" in errors
    )
    assert (
        "missing required text in .github/ISSUE_TEMPLATE/config.yml: blank_issues_enabled: false"
    ) in errors


def test_canonical_verifier_checks_repository_surface(
    capsys: pytest.CaptureFixture[str],
) -> None:
    verifier = importlib.import_module("scripts.verify")

    verifier.check_repository_surface()

    assert "repository surface: ok" in capsys.readouterr().out


def test_publication_surfaces_are_launch_ready_and_license_reviewed() -> None:
    license_review = ROOT / "docs" / "audits" / "transitive-license-review-2026-09-03.md"
    assert license_review.is_file()
    review_text = license_review.read_text(encoding="utf-8")
    assert "23 locked third-party packages" in review_text
    assert "No license incompatibility identified" in review_text
    assert "mypy-extensions 1.1.0" in review_text

    checklist = (ROOT / "docs" / "publication-checklist.md").read_text(encoding="utf-8")
    assert "[x] Transitive dependency licenses receive independent review" in checklist
    pvr_gate = (
        "[x] GitHub private vulnerability reporting is enabled and read back immediately "
        "after public visibility"
    )
    assert pvr_gate in checklist.replace("\n      ", " ")
    assert "- [ ]" not in checklist

    launch_surfaces = (
        ROOT / "benchmark" / "robot_cell_v1" / "DATASET_CARD.md",
        ROOT / "spaces" / "oscillink-safety-ops-demo" / "README.md",
        ROOT / "docs" / "release-process.md",
        ROOT / "docs" / "releases" / "v0.1.0-alpha.2.md",
        ROOT / "docs" / "execution-plan.md",
    )
    stale_phrases = (
        "future Hugging Face Dataset",
        "has not been published",
        "neither artifact has been uploaded",
        "staging metadata for a future Hugging Face static Space",
        "Before any future publication",
        "There is no published Oscillink Safety Ops release",
        "license inventory is currently incomplete",
        "local release-candidate preparation; not published",
        "Published release: none",
        "Intended tag:",
        "not run because no push is authorized",
        "must be rerun after all changes",
    )
    for path in launch_surfaces:
        text = path.read_text(encoding="utf-8")
        for phrase in stale_phrases:
            assert phrase not in text, f"stale pre-publication copy in {path}: {phrase}"


def test_space_metadata_is_hugging_face_static_compatible() -> None:
    card = (ROOT / "spaces" / "oscillink-safety-ops-demo" / "README.md").read_text(encoding="utf-8")
    assert card.startswith("---\n")
    assert "sdk: static\n" in card
    assert "app_file: index.html\n" in card
    assert "colorFrom: indigo\n" in card
    assert "colorTo: blue\n" in card


def test_pytest_dev_dependency_excludes_vulnerable_versions() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert "pytest>=9.0.3,<10" in project["dependency-groups"]["dev"]


def test_public_positioning_uses_approved_headline_and_dedicated_assurance_status() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assurance_path = ROOT / "docs" / "assurance-status.md"

    first_prose_line = next(
        line for line in readme.splitlines() if line and not line.startswith("#")
    )
    assert first_prose_line == APPROVED_HEADLINE
    assert project["project"]["description"] == APPROVED_HEADLINE
    assert assurance_path.is_file()
    assurance = assurance_path.read_text(encoding="utf-8")
    assert "## Current implemented status" in assurance
    assert "No real machine control" in assurance
    assert "[Assurance status and limitations](docs/assurance-status.md)" in readme


def test_public_docs_distinguish_current_evidence_from_planned_supervision() -> None:
    required_markers = {
        "AGENTS.md": (
            "simulated, replay, and shadow supervision",
            "Real machinery control remains forbidden",
        ),
        "SECURITY.md": ("current package implements", "Assurance and deployment boundary"),
        "docs/product-boundary.md": (
            "## Current implementation",
            "## Implemented simulated supervisor",
        ),
        "docs/technical-overview.md": (
            "## Current evidence plane",
            "## Implemented simulated runtime plane",
        ),
        "docs/execution-plan.md": ("## Approved public direction", "Public alpha 0.1.0 alpha 2"),
        "docs/publication-checklist.md": ("Implemented runtime status",),
        "docs/release-process.md": ("current runtime is implemented",),
        "docs/releases/v0.1.0-alpha.1.md": ("## Included in this release",),
        "docs/releases/v0.1.0-alpha.2.md": ("## Included in this release",),
    }

    for relative, markers in required_markers.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for marker in markers:
            assert marker in text, f"missing public-boundary marker in {relative}: {marker}"


def test_public_claims_do_not_overstate_oscillink_assurance_or_results() -> None:
    public_claim_files = (
        "README.md",
        "SECURITY.md",
        "docs/assurance-status.md",
        "docs/product-boundary.md",
        "docs/technical-overview.md",
        "docs/execution-plan.md",
        "docs/publication-checklist.md",
        "docs/release-process.md",
        "docs/releases/v0.1.0-alpha.1.md",
        "docs/releases/v0.1.0-alpha.2.md",
    )
    forbidden_claims = (
        "Oscillink is certified",
        "Oscillink Safety Ops is safety-rated",
        "Oscillink achieves PL",
        "Oscillink achieves SIL",
        "field-proven",
        "production-ready",
        "controls real equipment",
        "commands real machinery",
    )

    for relative in public_claim_files:
        text = (ROOT / relative).read_text(encoding="utf-8")
        for claim in forbidden_claims:
            assert claim not in text, f"unsupported public claim in {relative}: {claim}"


def test_claim_validator_rejects_unimplemented_runtime_intervention_claim() -> None:
    module = importlib.import_module("scripts.verify_repository_surface")

    assert hasattr(module, "validate_public_claim_text")
    errors = module.validate_public_claim_text(
        "README.md",
        APPROVED_HEADLINE
        + "\n\nOscillink currently emits protective-stop requests for industrial equipment.\n",
    )

    assert errors == ("unimplemented runtime intervention presented as current in README.md",)


def test_claim_validator_rejects_unsupported_certification_claim() -> None:
    validate = importlib.import_module(
        "scripts.verify_repository_surface"
    ).validate_public_claim_text

    errors = validate(
        "README.md",
        APPROVED_HEADLINE + "\n\nOscillink Safety Ops is certified to SIL 3.\n",
    )

    assert errors == ("unsupported certification or PL/SIL claim in README.md",)


def test_claim_validator_rejects_synthetic_results_presented_as_field_results() -> None:
    validate = importlib.import_module(
        "scripts.verify_repository_surface"
    ).validate_public_claim_text

    errors = validate(
        "README.md",
        "The synthetic benchmark's field results demonstrate incident prevention.\n",
    )

    assert errors == ("synthetic or simulation result presented as field evidence in README.md",)


def test_repository_surface_runs_public_claim_validation(tmp_path: Path) -> None:
    validate = importlib.import_module(
        "scripts.verify_repository_surface"
    ).validate_repository_surface
    (tmp_path / "README.md").write_text(
        "Oscillink Safety Ops is certified to SIL 3.\n",
        encoding="utf-8",
    )

    errors = validate(tmp_path)

    assert "unsupported certification or PL/SIL claim in README.md" in errors


def test_runtime_supervisor_research_corpus_is_complete_and_ledger_bound() -> None:
    corpus = ROOT / "docs" / "research" / "runtime-supervisor"
    expected_reports = {
        "standards-path-2026-09-02.md": None,
        "hazards-incidents-2026-09-02.md": None,
        "community-voice-2026-09-02.md": "community-voice-ledger.json",
        "competitor-map-2026-09-02.md": "competitor-map-ledger.json",
        "public-demo-strategy-2026-09-02.md": "public-demo-strategy-ledger.json",
    }

    assert (corpus / "README.md").is_file()
    assert {path.name for path in corpus.glob("*.md") if path.name != "README.md"} == set(
        expected_reports
    )
    for report_name, ledger_name in expected_reports.items():
        report = (corpus / report_name).read_text(encoding="utf-8")
        assert "C:\\Users\\" not in report
        assert "C:/Users/" not in report
        assert "\r" not in report
        assert "## Sources" in report
        if ledger_name is None:
            continue
        ledger = json.loads((corpus / "citations" / ledger_name).read_text(encoding="utf-8"))
        sources = {source["id"]: source["url"] for source in ledger["sources"]}
        cited_ids = {int(value) for value in re.findall(r"\[(\d+)\]", report)}
        listed_sources = {
            int(source_id): url
            for source_id, url in re.findall(
                r"^\[(\d+)\]\s+(https?://\S+?)(?:\s+—|\s*$)", report, re.MULTILINE
            )
        }
        assert cited_ids == set(sources)
        assert listed_sources == sources
