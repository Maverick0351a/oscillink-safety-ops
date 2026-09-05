from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADLINE = (
    "Oscillink Safety Ops is an independent safety and risk-mitigation supervisor for "
    "AI-controlled industrial equipment, connecting machine intent, observed behavior, and "
    "safety-manager oversight."
)
TRUST_FILES = (
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "SUPPORT.md",
    "TRADEMARKS.md",
    "CHANGELOG.md",
    "CITATION.cff",
    ".github/pull_request_template.md",
    "docs/releases/v0.1.0-alpha.1.md",
    "docs/releases/v0.1.0-alpha.2.md",
    "docs/release-process.md",
    "docs/publication-checklist.md",
)


def test_exact_community_files_and_issue_forms_exist() -> None:
    forms = ROOT / ".github" / "ISSUE_TEMPLATE"
    assert {path.name for path in forms.glob("*.yml")} == {
        "bug.yml",
        "config.yml",
        "external-reproduction.yml",
        "integration.yml",
    }
    for relative in (*TRUST_FILES, ".github/dependabot.yml"):
        assert (ROOT / relative).is_file(), relative


def test_issue_forms_require_safe_reproducible_submissions() -> None:
    for name in ("bug.yml", "integration.yml", "external-reproduction.yml"):
        text = (ROOT / ".github" / "ISSUE_TEMPLATE" / name).read_text(encoding="utf-8")
        assert text.startswith("name:")
        assert "body:" in text
        assert "validations:\n      required: true" in text
        assert "synthetic" in text.lower()
        assert "credential" in text.lower()
        assert "security.md" in text.lower()
    integration = (ROOT / ".github" / "ISSUE_TEMPLATE" / "integration.yml").read_text(
        encoding="utf-8"
    )
    assert "no machine, controller, PLC, robot, or network output" in integration


def test_trust_markdown_links_resolve_and_has_no_personal_or_private_paths() -> None:
    link = re.compile(r"\[[^]]+\]\(([^)]+)\)")
    for relative in TRUST_FILES:
        path = ROOT / relative
        text = path.read_text(encoding="utf-8")
        assert "C:\\Users\\" not in text and "C:/Users/" not in text
        assert "/home/" not in text
        assert "customer-data/" not in text and "private/" not in text
        for target in link.findall(text):
            clean = target.split("#", 1)[0]
            if not clean or clean.startswith(("http://", "https://", "mailto:")):
                continue
            assert (path.parent / clean).resolve().exists(), f"broken link in {relative}: {target}"


def test_current_runtime_claims_match_implemented_simulation_boundary() -> None:
    current_files = (
        "SECURITY.md",
        "docs/assurance-status.md",
        "docs/release-process.md",
        "docs/publication-checklist.md",
        "docs/releases/v0.1.0-alpha.2.md",
        "CHANGELOG.md",
    )
    for relative in current_files:
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "runtime supervisor is planned, not implemented" not in text.lower(), relative
        assert "runtime supervisor is not included" not in text.lower(), relative
    notes = (ROOT / "docs/releases/v0.1.0-alpha.2.md").read_text(encoding="utf-8")
    assert HEADLINE in notes
    assert "closed-file simulation and replay" in notes.lower()
    assert "local simulated one-way protective-stop and inhibit request records" in notes.lower()
    assert "TLA+" in notes and "synthetic benchmark" in notes and "hosted CI" in notes


def test_open_core_and_trademark_boundary_is_precise() -> None:
    contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    trademarks = (ROOT / "TRADEMARKS.md").read_text(encoding="utf-8")
    for text in (contributing, trademarks):
        lowered = text.lower()
        assert "open-core" in lowered
        assert "Apache-2.0" in text
        assert "commercial connectors" in lowered
        assert "deployment" in lowered
        assert "fleet" in lowered
        assert "certification-support" in lowered
        assert "separate" in lowered
    assert "proprietary layers are open source" not in (contributing + trademarks).lower()


def test_dependabot_tracks_actions_and_python_lock_weekly() -> None:
    text = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    assert text.startswith("version: 2\n")
    assert 'package-ecosystem: "github-actions"' in text
    assert 'package-ecosystem: "uv"' in text
    assert text.count('interval: "weekly"') == 2


def test_release_identity_and_unsupported_claim_boundaries() -> None:
    combined = "\n".join((ROOT / relative).read_text(encoding="utf-8") for relative in TRUST_FILES)
    assert "0.1.0a2" in combined
    assert "v0.1.0-alpha.2" in combined
    for unsupported in (
        "field-proven",
        "production-ready",
        "certified to sil",
        "certified to pl",
        "safe operation is guaranteed",
        "controls real equipment",
    ):
        assert unsupported not in combined.lower()
