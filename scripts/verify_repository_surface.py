"""Verify the local repository trust and community surface."""

from __future__ import annotations

from pathlib import Path

REQUIRED_FILES = (
    "CHANGELOG.md",
    "CITATION.cff",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "SUPPORT.md",
    "TRADEMARKS.md",
    ".github/ISSUE_TEMPLATE/alpha-evaluation.yml",
    ".github/ISSUE_TEMPLATE/bug-report.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/integration-request.yml",
    ".github/pull_request_template.md",
    "docs/audits/publication-readiness-2026-09-01.md",
    "docs/publication-checklist.md",
    "docs/releases/v0.1.0-alpha.1.md",
    "docs/release-process.md",
)

REQUIRED_TEXT = {
    "CHANGELOG.md": ("## [Unreleased]", "No public version or release tag has been published."),
    "CITATION.cff": ("cff-version: 1.2.0", "license: Apache-2.0", "version: 0.1.0a1"),
    "CODE_OF_CONDUCT.md": ("Contributor Covenant", "Report conduct concerns privately"),
    "SECURITY.md": ("must not become public", "No version is currently supported"),
    "SUPPORT.md": ("Do not report vulnerabilities in a public issue.",),
    "TRADEMARKS.md": ("does not grant permission", "does not imply sponsorship"),
    ".github/ISSUE_TEMPLATE/alpha-evaluation.yml": (
        "does not determine compliance or authorize physical work",
    ),
    ".github/ISSUE_TEMPLATE/bug-report.yml": ("Do not include credentials",),
    ".github/ISSUE_TEMPLATE/config.yml": ("blank_issues_enabled: false",),
    ".github/ISSUE_TEMPLATE/integration-request.yml": (
        "read-only and has no reverse command channel",
    ),
    ".github/pull_request_template.md": ("adds no equipment command",),
    "docs/audits/publication-readiness-2026-09-01.md": (
        "local pre-publication evidence; publication remains blocked",
        "0 findings",
        "known vulnerabilities: 0",
    ),
    "docs/publication-checklist.md": ("separate explicit authorization",),
    "docs/releases/v0.1.0-alpha.1.md": (
        "local deterministic engineering prerelease candidate; not published",
        "Package version: `0.1.0a1`",
        "Operational authority: none",
    ),
    "docs/release-process.md": ("requires explicit owner authorization",),
}


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
    return tuple(errors)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    errors = validate_repository_surface(root)
    if errors:
        raise SystemExit("\n".join(errors))
    print("repository surface: ok")


if __name__ == "__main__":
    main()
