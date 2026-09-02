from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from oscillink_safety_ops.cli import run
from oscillink_safety_ops.domain import PhysicalIntelligenceEvidenceEnvelope
from oscillink_safety_ops.io import (
    FixtureIntegrityError,
    load_envelope,
    load_plan,
    verify_envelope_payload,
    verify_manifest,
)
from scripts.verify import verify_envelope_fixture

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
            "--envelope",
            str(FIXTURE / "envelope.json"),
            "--root",
            str(FIXTURE),
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


def test_cli_rejects_plan_path_different_from_verified_envelope_payload(tmp_path: Path) -> None:
    tampered = tmp_path / "plan.json"
    plan = json.loads((FIXTURE / "plan.json").read_text(encoding="utf-8"))
    plan["declared_evidence_keys"].append("verification.zero_energy")
    tampered.write_text(json.dumps(plan), encoding="utf-8")

    with pytest.raises(FixtureIntegrityError, match="plan path does not match envelope payload"):
        run(
            [
                "audit",
                "--packet",
                str(FIXTURE / "packet.json"),
                "--plan",
                str(tampered),
                "--manifest",
                str(FIXTURE / "manifest.json"),
                "--envelope",
                str(FIXTURE / "envelope.json"),
                "--root",
                str(FIXTURE),
            ]
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


def test_envelope_loader_uses_the_same_bounded_strict_json_boundary(tmp_path: Path) -> None:
    path = tmp_path / "evidence-envelope.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "platform_id": "example-platform",
                "platform_version": "2026.08",
                "adapter_id": "example-json-export-reader",
                "adapter_version": "1.0.0",
                "adapter_config_sha256": "sha256:" + "a" * 64,
                "artifact_type": "recorded_episode_manifest",
                "source_ref": "exports/run-0042/manifest.json",
                "source_revision": "revision-17",
                "content_sha256": "sha256:" + "b" * 64,
                "observed_at": "2026-08-31T00:00:00Z",
                "payload_ref": "payloads/episode-0003.json",
            }
        ),
        encoding="utf-8",
    )

    envelope = load_envelope(path)

    assert envelope.platform_id == "example-platform"
    assert envelope.access_mode == "read_only"


def test_envelope_payload_verification_binds_the_declared_content_hash(tmp_path: Path) -> None:
    payload = tmp_path / "episode.json"
    payload.write_bytes(b'{"episode_id":"synthetic-003"}\n')
    envelope_path = tmp_path / "evidence-envelope.json"
    envelope_path.write_text(
        json.dumps(
            {
                "platform_id": "example-platform",
                "platform_version": "2026.08",
                "adapter_id": "example-json-export-reader",
                "adapter_version": "1.0.0",
                "adapter_config_sha256": "sha256:" + "a" * 64,
                "artifact_type": "recorded_episode",
                "source_ref": "episode.json",
                "source_revision": "revision-17",
                "content_sha256": "sha256:" + hashlib.sha256(payload.read_bytes()).hexdigest(),
                "observed_at": "2026-08-31T00:00:00Z",
                "payload_ref": "episode.json",
            }
        ),
        encoding="utf-8",
    )

    envelope = load_envelope(envelope_path)

    assert verify_envelope_payload(envelope, root=tmp_path) == envelope.content_sha256

    payload.write_bytes(b'{"episode_id":"changed"}\n')
    with pytest.raises(FixtureIntegrityError, match="payload hash mismatch"):
        verify_envelope_payload(envelope, root=tmp_path)


def test_cli_validates_an_envelope_and_emits_deterministic_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = tmp_path / "episode.json"
    payload.write_bytes(b'{"episode_id":"synthetic-003"}\n')
    envelope_path = tmp_path / "evidence-envelope.json"
    envelope_path.write_text(
        json.dumps(
            {
                "platform_id": "example-platform",
                "platform_version": "2026.08",
                "adapter_id": "example-json-export-reader",
                "adapter_version": "1.0.0",
                "adapter_config_sha256": "sha256:" + "a" * 64,
                "artifact_type": "recorded_episode",
                "source_ref": "episode.json",
                "source_revision": "revision-17",
                "content_sha256": "sha256:" + hashlib.sha256(payload.read_bytes()).hexdigest(),
                "observed_at": "2026-08-31T00:00:00Z",
                "payload_ref": "episode.json",
            }
        ),
        encoding="utf-8",
    )

    first_exit = run(
        [
            "envelope",
            "validate",
            "--envelope",
            str(envelope_path),
            "--root",
            str(tmp_path),
        ]
    )
    first = capsys.readouterr().out
    second_exit = run(
        [
            "envelope",
            "validate",
            "--envelope",
            str(envelope_path),
            "--root",
            str(tmp_path),
        ]
    )
    second = capsys.readouterr().out

    result = json.loads(first)
    assert first_exit == second_exit == 0
    assert first == second
    assert result["access_mode"] == "read_only"
    assert result["content_treatment"] == "untrusted_data"


def test_cli_validates_the_pinned_synthetic_envelope(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = run(
        [
            "envelope",
            "validate",
            "--envelope",
            str(FIXTURE / "envelope.json"),
            "--root",
            str(FIXTURE),
        ]
    )

    result = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert result["task_id"] == "plan-synthetic-maintenance-001"
    assert result["content_sha256"] == (
        "sha256:551b03d141e51dfb73b193282509b7a94d9c7d39ce89dc1bb882bde7dc5852fe"
    )


def test_canonical_fixture_gate_verifies_the_envelope_payload() -> None:
    assert verify_envelope_fixture(FIXTURE) == (
        "sha256:551b03d141e51dfb73b193282509b7a94d9c7d39ce89dc1bb882bde7dc5852fe"
    )


def test_envelope_payload_cannot_escape_the_declared_read_only_root(tmp_path: Path) -> None:
    root = tmp_path / "allowed"
    root.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_bytes(b'{"episode_id":"outside"}\n')
    envelope = PhysicalIntelligenceEvidenceEnvelope(
        platform_id="example-platform",
        platform_version="2026.08",
        adapter_id="example-json-export-reader",
        adapter_version="1.0.0",
        adapter_config_sha256="sha256:" + "a" * 64,
        artifact_type="recorded_episode",
        source_ref="../outside.json",
        source_revision="revision-17",
        content_sha256="sha256:" + hashlib.sha256(outside.read_bytes()).hexdigest(),
        observed_at=datetime(2026, 8, 31, tzinfo=UTC),
        payload_ref="../outside.json",
    )

    with pytest.raises(FixtureIntegrityError, match="invalid envelope payload_ref"):
        verify_envelope_payload(envelope, root=root)


def test_cli_normalizes_and_stores_operational_jsonl_deterministically(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exported = {
        "schema_version": 1,
        "record_id": "record:autonomy-001",
        "source_type": "autonomous_system",
        "record_kind": "log",
        "scope_id": "cell:synthetic-robot-01",
        "system_id": "autonomy-stack:synthetic",
        "component_id": "planner:local",
        "source_tag": "planner.event",
        "observed_at": "2026-08-31T00:00:00Z",
        "raw_record_sha256": "sha256:" + "0" * 64,
        "raw_value": None,
        "units": None,
        "quality": "good",
        "calibration_revision": None,
        "event_code": "protective_stop_requested",
        "message": "Planner requested a protective stop.",
        "missing_fields": ["raw_value"],
        "unsupported_fields": [],
        "authority_state": "observational_evidence",
        "access_mode": "read_only",
        "content_treatment": "untrusted_data",
    }
    source = tmp_path / "autonomy.jsonl"
    source.write_text(json.dumps(exported, sort_keys=True) + "\n", encoding="utf-8")
    argv = [
        "operational",
        "normalize",
        "--input",
        str(source),
        "--batch-id",
        "batch:autonomy-001",
        "--source-revision",
        "export:autonomy-001",
        "--adapter-config-sha256",
        "sha256:" + "a" * 64,
        "--store-root",
        str(tmp_path / "store"),
    ]

    assert run(argv) == 0
    first = capsys.readouterr().out
    assert run(argv) == 0
    second = capsys.readouterr().out

    assert first == second
    result = json.loads(first)
    assert result["batch"]["records"][0]["source_type"] == "autonomous_system"
    assert result["batch"]["records"][0]["raw_record_sha256"] != exported["raw_record_sha256"]
    assert result["stored_artifact"]["sha256"] == result["batch"]["source_artifact_sha256"]
