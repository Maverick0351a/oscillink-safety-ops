from __future__ import annotations

import importlib
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


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

    assert "missing required repository file: docs/releases/v0.1.0-alpha.1.md" in validate(tmp_path)


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

    assert "missing required text in SECURITY.md: must not become public" in errors
    assert (
        "missing required text in .github/ISSUE_TEMPLATE/config.yml: blank_issues_enabled: false"
    ) in errors


def test_canonical_verifier_checks_repository_surface(
    capsys: pytest.CaptureFixture[str],
) -> None:
    verifier = importlib.import_module("scripts.verify")

    verifier.check_repository_surface()

    assert "repository surface: ok" in capsys.readouterr().out


def test_pytest_dev_dependency_excludes_vulnerable_versions() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert "pytest>=9.0.3,<10" in project["dependency-groups"]["dev"]
