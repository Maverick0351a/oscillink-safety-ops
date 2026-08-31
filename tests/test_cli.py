from __future__ import annotations

import json
from pathlib import Path

import pytest

from oscillink_safety_ops.cli import run
from oscillink_safety_ops.io import FixtureIntegrityError, load_plan, verify_manifest

FIXTURE = Path(__file__).parent / "fixtures" / "synthetic_press"


def test_cli_audits_pinned_fixture_as_deterministic_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = run(
        [
            "audit",
            "--packet",
            str(FIXTURE / "packet.json"),
            "--plan",
            str(FIXTURE / "plan.json"),
            "--manifest",
            str(FIXTURE / "manifest.json"),
        ]
    )

    report = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert [finding["state"] for finding in report["findings"]] == [
        "matched",
        "missing_evidence",
        "unreadable",
        "source_conflict",
        "revision_stale",
        "asset_mismatch",
        "unsupported_interpretation",
        "requires_authorized_review",
    ]
    assert all(
        finding["citation"]["quote_sha256"].startswith("sha256:") for finding in report["findings"]
    )


def test_fixture_verification_rejects_changed_source_bytes(tmp_path: Path) -> None:
    fixture_copy = tmp_path / "fixture"
    fixture_copy.mkdir()
    (fixture_copy / "sources").mkdir()
    (fixture_copy / "manifest.json").write_bytes((FIXTURE / "manifest.json").read_bytes())
    (fixture_copy / "sources" / "manual-rev2.txt").write_text("changed", encoding="utf-8")
    (fixture_copy / "sources" / "site-procedure-rev1.txt").write_bytes(
        (FIXTURE / "sources" / "site-procedure-rev1.txt").read_bytes()
    )

    with pytest.raises(FixtureIntegrityError, match="hash mismatch"):
        verify_manifest(fixture_copy / "manifest.json")


def test_cli_requires_manifest_for_every_audit() -> None:
    with pytest.raises(SystemExit):
        run(
            [
                "audit",
                "--packet",
                str(FIXTURE / "packet.json"),
                "--plan",
                str(FIXTURE / "plan.json"),
            ]
        )


def test_json_loader_rejects_oversized_input_before_validation(tmp_path: Path) -> None:
    oversized = tmp_path / "oversized-plan.json"
    oversized.write_text(
        '{"schema_version":1,"plan_id":"plan","asset_model":"model",'
        '"declared_evidence_keys":[],"padding":"' + "x" * (1024 * 1024) + '"}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="input exceeds"):
        load_plan(oversized)
