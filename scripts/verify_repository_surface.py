"""Verify the local repository trust and community surface."""

from __future__ import annotations

import re
from pathlib import Path

REQUIRED_FILES = (
    "CHANGELOG.md",
    "CITATION.cff",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "SUPPORT.md",
    "TRADEMARKS.md",
    ".github/ISSUE_TEMPLATE/bug.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/external-reproduction.yml",
    ".github/ISSUE_TEMPLATE/integration.yml",
    ".github/dependabot.yml",
    ".github/pull_request_template.md",
    ".github/workflows/nightly.yml",
    ".github/workflows/release.yml",
    ".github/workflows/security.yml",
    ".github/workflows/verify.yml",
    "docs/audits/history-baseline-2943db2.json",
    "docs/audits/publication-readiness-2026-09-01.md",
    "docs/audits/release-candidate-0.1.0a1.md",
    "docs/publication-checklist.md",
    "docs/releases/v0.1.0-alpha.1.md",
    "docs/release-process.md",
    "docs/milestones/private-pilot-gates.md",
)

REQUIRED_TEXT = {
    "CHANGELOG.md": ("## [Unreleased]", "No public version or release tag has been published."),
    "CITATION.cff": ("cff-version: 1.2.0", "license: Apache-2.0", "version: 0.1.0a1"),
    "CODE_OF_CONDUCT.md": ("Contributor Covenant", "Report conduct concerns privately"),
    "CONTRIBUTING.md": ("open-core", "Commercial connectors"),
    "SECURITY.md": ("Publication remains blocked", "No version is currently supported"),
    "SUPPORT.md": ("Vulnerabilities must follow",),
    "TRADEMARKS.md": ("does not grant permission", "open-core"),
    ".github/ISSUE_TEMPLATE/bug.yml": ("Do not include credentials",),
    ".github/ISSUE_TEMPLATE/config.yml": ("blank_issues_enabled: false",),
    ".github/ISSUE_TEMPLATE/external-reproduction.yml": ("synthetic software reproduction",),
    ".github/ISSUE_TEMPLATE/integration.yml": (
        "no machine, controller, PLC, robot, or network output",
    ),
    ".github/dependabot.yml": ('package-ecosystem: "github-actions"', 'package-ecosystem: "uv"'),
    ".github/pull_request_template.md": ("adds no real equipment",),
    ".github/workflows/nightly.yml": ("scripts/verify_tla.py", "fuzz/runtime_observation_fuzz.py"),
    ".github/workflows/release.yml": ("--require-complete", "SHA256SUMS.txt"),
    ".github/workflows/security.yml": ('GITLEAKS_VERSION: "8.30.1"', "pip-audit==2.10.1"),
    ".github/workflows/verify.yml": ("windows-latest", "scripts/verify.py"),
    "docs/audits/history-baseline-2943db2.json": (
        "oscillink-redacted-reachable-history-audit-v1",
        "2943db23ceb075e8955867903069cd5e043fee45",
    ),
    "docs/audits/publication-readiness-2026-09-01.md": (
        "local pre-publication evidence; publication remains blocked",
        "0 findings",
        "known vulnerabilities: 0",
    ),
    "docs/audits/release-candidate-0.1.0a1.md": (
        "private local release-candidate evidence; not published",
        "uncompressed member payload differences: 0",
        "Keep the candidate private and unpushed.",
    ),
    "docs/publication-checklist.md": ("separate explicit authorization",),
    "docs/releases/v0.1.0-alpha.1.md": (
        "published public prerelease",
        "Package version: `0.1.0a1`",
        "Release tag: [`v0.1.0-alpha.1`]",
        "Operational authority: none",
    ),
    "docs/release-process.md": ("exact candidate commit exists",),
}

PUBLIC_CLAIM_FILES = (
    "README.md",
    "SECURITY.md",
    "docs/assurance-status.md",
    "docs/product-boundary.md",
    "docs/technical-overview.md",
    "docs/execution-plan.md",
    "docs/publication-checklist.md",
    "docs/release-process.md",
    "docs/releases/v0.1.0-alpha.1.md",
)


def validate_public_claim_text(relative: str, text: str) -> tuple[str, ...]:
    """Reject public language that presents planned intervention as implemented."""
    errors: list[str] = []
    current_intervention = re.compile(
        r"\b(?:currently|now)\b[^.\n]{0,120}\b(?:emits?|issues?|requests?)\b"
        r"[^.\n]{0,80}\b(?:protective[- ]stop|inhibit|intervention)",
        re.IGNORECASE,
    )
    if current_intervention.search(text):
        errors.append(f"unimplemented runtime intervention presented as current in {relative}")
    unsupported_assurance = re.compile(
        r"(?<!\bNo )\bOscillink(?: Safety Ops)?\b[^.\n]{0,80}"
        r"(?:\bis certified\b|\bachieves?\s+(?:PL|SIL)\b)",
        re.IGNORECASE,
    )
    if unsupported_assurance.search(text):
        errors.append(f"unsupported certification or PL/SIL claim in {relative}")
    synthetic_field_result = re.compile(
        r"\b(?:synthetic|simulation)\b[^.\n]{0,100}\bfield results?\b"
        r"[^.\n]{0,100}\b(?:demonstrates?|proves?|shows?)\b",
        re.IGNORECASE,
    )
    if synthetic_field_result.search(text):
        errors.append(f"synthetic or simulation result presented as field evidence in {relative}")
    return tuple(errors)


def validate_repository_surface(root: Path) -> tuple[str, ...]:
    """Return deterministic repository-surface validation errors."""
    errors = [
        f"missing required repository file: {relative}"
        for relative in REQUIRED_FILES
        if not (root / relative).is_file()
    ]
    for relative, markers in REQUIRED_TEXT.items():
        path = root / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        errors.extend(
            f"missing required text in {relative}: {marker}"
            for marker in markers
            if marker not in text
        )
    for relative in PUBLIC_CLAIM_FILES:
        path = root / relative
        if path.is_file():
            errors.extend(validate_public_claim_text(relative, path.read_text(encoding="utf-8")))
    return tuple(errors)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    errors = validate_repository_surface(root)
    if errors:
        raise SystemExit("\n".join(errors))
    print("repository surface: ok")


if __name__ == "__main__":
    main()
