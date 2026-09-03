from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _version(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.split("."))


def test_cryptography_policy_excludes_known_vulnerable_46_series() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    cryptography = next(item for item in lock["package"] if item["name"] == "cryptography")

    assert "cryptography>=50.0.0,<51" in project["project"]["dependencies"]
    assert _version(cryptography["version"]) >= (50, 0, 0)


def test_security_workflow_runs_pinned_pip_audit_fail_closed() -> None:
    workflow = (ROOT / ".github" / "workflows" / "security.yml").read_text(encoding="utf-8")

    assert "pip-audit==2.10.1" in workflow
    assert "pip-audit --strict" in workflow
    assert (
        "--require-hashes" not in workflow
    )  # uv.lock is the resolved source, not exported hashes.
