from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
EXPECTED = {"verify.yml", "security.yml", "nightly.yml", "release.yml"}
PINNED_USES = re.compile(r"^\s*-?\s*uses:\s*[^#\s]+@([0-9a-f]{40})(?:\s+#.*)?$")


def _text(name: str) -> str:
    return (WORKFLOWS / name).read_text(encoding="utf-8")


def _run_blocks(text: str) -> tuple[str, ...]:
    lines = text.splitlines()
    blocks: list[str] = []
    index = 0
    while index < len(lines):
        match = re.match(r"^(\s*)-?\s*run:\s*(.*)$", lines[index])
        if not match:
            index += 1
            continue
        indent = len(match.group(1))
        block = [match.group(2)]
        index += 1
        while index < len(lines):
            line = lines[index]
            if line.strip() and len(line) - len(line.lstrip()) <= indent:
                break
            block.append(line)
            index += 1
        blocks.append("\n".join(block))
    return tuple(blocks)


def test_workflow_set_replaces_obsolete_ci() -> None:
    assert {path.name for path in WORKFLOWS.glob("*.yml")} == EXPECTED


def test_all_actions_are_full_sha_pinned_and_events_are_safe() -> None:
    for path in WORKFLOWS.glob("*.yml"):
        text = path.read_text(encoding="utf-8")
        assert "pull_request_target" not in text
        assert "workflow_run" not in text
        assert "repository_dispatch" not in text
        assert "issue_comment" not in text
        assert "permissions: write-all" not in text
        for line in text.splitlines():
            if "uses:" in line:
                assert PINNED_USES.match(line), f"mutable or malformed uses in {path.name}: {line}"
        for block in _run_blocks(text):
            assert "${{ github.event" not in block
            assert "${{ inputs." not in block


def test_workflows_have_concurrency_and_no_secret_or_deploy_surface() -> None:
    forbidden = (
        "secrets.",
        "id-token: write",
        "contents: write",
        "deploy",
        "gh release",
        "git push",
    )
    for name in EXPECTED:
        text = _text(name)
        assert "concurrency:" in text
        assert "cancel-in-progress:" in text
        assert "permissions:\n  contents: read" in text
        for marker in forbidden:
            assert marker not in text.lower()


def test_verify_has_locked_windows_and_ubuntu_lanes_and_both_test_gates() -> None:
    text = _text("verify.yml")
    assert "os: [ubuntu-latest, windows-latest]" in text
    assert "uv sync --locked --dev" in text
    assert "uv run python scripts/verify.py" in text
    assert "uv run python -m pytest -q" in text
    assert "uv run pytest -q" in text


def test_security_has_codeql_and_checksum_verified_gitleaks_history_scan() -> None:
    text = _text("security.yml")
    assert "github/codeql-action/init@cdf488f595d80d6e07e03d4674febd5ab45fa938" in text
    assert "github/codeql-action/analyze@cdf488f595d80d6e07e03d4674febd5ab45fa938" in text
    assert 'GITLEAKS_VERSION: "8.30.1"' in text
    assert "551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb" in text
    assert "fetch-depth: 0" in text
    assert "sha256sum -c" in text
    assert "gitleaks git" in text
    assert "--redact" in text


def test_nightly_replays_formal_property_fuzz_and_benchmark_gates() -> None:
    text = _text("nightly.yml")
    for marker in (
        "scripts/verify_tla.py",
        "tests/runtime/test_property_state_machine.py",
        "fuzz/runtime_observation_fuzz.py",
        "safety-ops benchmark verify",
    ):
        assert marker in text
    assert "936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88" in text


def test_release_is_manual_or_tag_gated_and_checks_artifacts_in_isolation() -> None:
    text = _text("release.yml")
    assert "workflow_dispatch:" in text
    assert 'tags:\n      - "v*"' in text
    assert "refs/tags/v0.1.0-alpha.1" in text
    assert "uv build --out-dir" in text
    assert "cyclonedx-sbom.json" in text
    assert "provenance.json" in text
    assert "benchmark-metrics.json" in text
    assert "formal-result.json" in text
    assert "SHA256SUMS.txt" in text
    assert "create_release_manifest.py verify" in text
    assert "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a" in text
    assert "if-no-files-found: error" in text
