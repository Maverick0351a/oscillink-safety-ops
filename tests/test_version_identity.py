from __future__ import annotations

import importlib
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "0.1.0a2"
HUMAN_VERSION = "0.1.0-alpha.2"


def test_runtime_version_is_canonical_project_prerelease() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    package = importlib.import_module("oscillink_safety_ops")

    assert "version" not in project["project"]
    assert project["project"]["dynamic"] == ["version"]
    assert project["tool"]["hatch"]["version"]["path"] == ("src/oscillink_safety_ops/__init__.py")
    assert package.__version__ == EXPECTED_VERSION


def test_release_candidate_documents_match_package_version() -> None:
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    package = next(item for item in lock["package"] if item["name"] == "oscillink-safety-ops")
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    release_notes = ROOT / "docs" / "releases" / f"v{HUMAN_VERSION}.md"

    assert "version" not in package
    assert package["source"] == {"editable": "."}
    assert f"version: {EXPECTED_VERSION}" in citation
    assert f"## [{HUMAN_VERSION}] — 2026-09-04" in changelog
    assert release_notes.is_file()
    notes = release_notes.read_text(encoding="utf-8")
    assert f"Package version: `{EXPECTED_VERSION}`" in notes
    assert "published public prerelease" in notes
    assert "Tagged commit: `58cb8e494018481ac81810c56cdfffd20bb6c993`" in notes
