"""Deterministic closed-file runtime replay tests."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from oscillink_safety_ops.cli import run
from oscillink_safety_ops.runtime.configuration import configuration_signing_bytes
from oscillink_safety_ops.runtime.replay import (
    DEFAULT_MAX_REPLAY_BYTES,
    DEFAULT_MAX_REPLAY_LINE_BYTES,
    ReplayError,
    parse_observation_jsonl,
    replay_closed_files,
    runtime_format_identity,
)

NOW = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _write_fixture(root: Path) -> tuple[Path, Path, Path]:
    root.mkdir(parents=True, exist_ok=True)
    private = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    configuration: dict[str, Any] = {
        "schema_version": 1,
        "configuration_id": "configuration:robot-cell:demo-v1",
        "revision": 1,
        "scope_id": "SCOPE-ROBOT-CELL-001",
        "valid_from": "2026-09-03T00:00:00Z",
        "valid_until": "2026-09-04T00:00:00Z",
        "required_source_ids": [
            "independent-health-monitor:a",
            "independent-zone-sensor:a",
            "production-ai:planner",
        ],
        "max_observation_age_seconds": 0.5,
        "max_receive_delay_seconds": 0.2,
        "max_future_skew_seconds": 0.0,
        "max_correlation_delay_seconds": 0.25,
        "max_speed_mps": 1.0,
        "max_acceleration_mps2": 2.0,
        "signer_id": "demo-safety-config-signer-v1",
        "signature_algorithm": "ed25519",
        "signature": "ed25519:" + "00" * 64,
        "authority_state": "externally_signed_configuration",
        "operational_authority": "simulated_evaluation_only",
    }
    configuration["signature"] = (
        "ed25519:" + private.sign(configuration_signing_bytes(configuration)).hex()
    )
    configuration_raw = _canonical(configuration)
    config_path = root / "configuration.json"
    config_path.write_bytes(configuration_raw)
    authority = {
        "schema_version": 1,
        "scope_id": "SCOPE-ROBOT-CELL-001",
        "signer_id": "demo-safety-config-signer-v1",
        "ed25519_public_key": "ed25519-public:" + private.public_key().public_bytes_raw().hex(),
        "configuration_id": "configuration:robot-cell:demo-v1",
        "revision": 1,
        "approved_configuration_sha256": "sha256:" + hashlib.sha256(configuration_raw).hexdigest(),
        "constraints": {
            "max_observation_age_seconds": 0.5,
            "max_receive_delay_seconds": 0.2,
            "max_future_skew_seconds": 0.0,
            "max_correlation_delay_seconds": 0.25,
            "max_speed_mps": 1.0,
            "max_acceleration_mps2": 2.0,
            "mandatory_source_ids": [
                "independent-health-monitor:a",
                "independent-zone-sensor:a",
                "production-ai:planner",
            ],
        },
    }
    authority_path = root / "authority.json"
    authority_path.write_bytes(_canonical(authority))
    common = {
        "schema_version": 1,
        "run_id": "run:robot-cell:clean-v1",
        "sequence_number": 0,
        "observed_at": "2026-09-03T12:00:00Z",
        "received_at": "2026-09-03T12:00:00Z",
    }
    records = [
        {
            **common,
            "observation_id": "command:0",
            "source_id": "production-ai:planner",
            "source_domain": "production_ai",
            "command_id": "command-id:0",
            "command_kind": "idle",
            "motion_requested": False,
        },
        {
            **common,
            "observation_id": "physical:0",
            "source_id": "independent-zone-sensor:a",
            "source_domain": "independent_physical_observation",
            "zone_id": "zone:synthetic-protected",
            "occupancy": "clear",
            "motion_state": "stopped",
            "speed_mps": 0.0,
            "acceleration_mps2": 0.0,
            "quality": "good",
            "calibration_sha256": "sha256:" + "d" * 64,
        },
        {
            **common,
            "observation_id": "health:0",
            "source_id": "independent-health-monitor:a",
            "source_domain": "independent_source_health",
            "monitored_source_id": "independent-zone-sensor:a",
            "source_state": "healthy",
            "clock_state": "healthy",
            "last_source_sequence": 0,
        },
    ]
    input_path = root / "clean.jsonl"
    input_path.write_bytes(b"".join(_canonical(record) for record in records))
    return config_path, input_path, authority_path


def test_clean_replay_is_byte_deterministic_and_binds_all_identities(tmp_path: Path) -> None:
    configuration, input_path, authority = _write_fixture(tmp_path)

    first = replay_closed_files(
        root=tmp_path,
        configuration=configuration.relative_to(tmp_path),
        input_path=input_path.relative_to(tmp_path),
        authority_path=authority.relative_to(tmp_path),
    )
    second = replay_closed_files(
        root=tmp_path,
        configuration=configuration.relative_to(tmp_path),
        input_path=input_path.relative_to(tmp_path),
        authority_path=authority.relative_to(tmp_path),
    )

    assert first.canonical_bytes == second.canonical_bytes
    assert first.report["configuration_sha256"].startswith("sha256:")
    assert first.report["input_sha256"].startswith("sha256:")
    assert first.report["scenario_id"] == "scenario:clean"
    assert first.report["scenario_sha256"].startswith("sha256:")
    assert "runtime_code_sha256" not in first.report
    assert first.report["runtime_format_sha256"].startswith("sha256:")
    assert first.report["runtime_format_sources"]
    assert all(item["byte_count"] > 0 for item in first.report["runtime_format_sources"])
    assert first.report["report_format"] == "oscillink-runtime-replay-report-v1"
    assert first.report["final_state"]["supervisor_state"] == "monitoring_normal"
    assert first.canonical_bytes.endswith(b"\n")


def test_documented_cli_replay_publishes_exact_report_locally(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    configuration, input_path, _ = _write_fixture(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = run(
        [
            "runtime",
            "replay",
            "--configuration",
            configuration.name,
            "--input",
            input_path.name,
            "--output",
            "runtime-report.json",
        ]
    )

    expected = replay_closed_files(
        root=tmp_path,
        configuration=Path(configuration.name),
        input_path=Path(input_path.name),
        authority_path=Path("authority.json"),
    )
    assert result == 0
    assert (tmp_path / "runtime-report.json").read_bytes() == expected.canonical_bytes


def test_frozen_robot_cell_corpus_matches_byte_exact_expected_outputs() -> None:
    root = Path(__file__).resolve().parents[2]
    scenario_root = root / "scenarios" / "robot_cell_v1"
    for name in ("clean", "zone-entry", "stale-source", "contradictory-source"):
        result = replay_closed_files(
            root=root,
            configuration=Path("scenarios/robot_cell_v1/configuration.json"),
            input_path=Path(f"scenarios/robot_cell_v1/{name}.jsonl"),
            authority_path=Path("scenarios/robot_cell_v1/authority.json"),
        )
        expected = scenario_root / "expected" / f"{name}.report.json"
        assert result.canonical_bytes == expected.read_bytes()


def test_grouped_replay_rejects_duplicate_and_missing_source_arrangement(tmp_path: Path) -> None:
    configuration, input_path, authority = _write_fixture(tmp_path)
    records = [json.loads(line) for line in input_path.read_text(encoding="utf-8").splitlines()]
    duplicate = dict(records[0])
    duplicate["observation_id"] = "command:duplicate"
    duplicate["command_id"] = "command-id:duplicate"
    input_path.write_bytes(b"".join(_canonical(item) for item in (*records[:2], duplicate)))

    with pytest.raises(ReplayError) as captured:
        replay_closed_files(
            root=tmp_path,
            configuration=configuration.relative_to(tmp_path),
            input_path=input_path.relative_to(tmp_path),
            authority_path=authority.relative_to(tmp_path),
        )

    assert captured.value.code == "duplicate_source"


def test_runtime_format_identity_is_bound_to_exact_runtime_source_bytes(tmp_path: Path) -> None:
    runtime_root = Path(__file__).resolve().parents[2] / "src" / "oscillink_safety_ops" / "runtime"
    copied = tmp_path / "runtime"
    shutil.copytree(runtime_root, copied)

    original = runtime_format_identity(copied)
    replay_source = copied / "replay.py"
    replay_source.write_bytes(replay_source.read_bytes() + b"\n")
    changed = runtime_format_identity(copied)

    assert original.sha256 != changed.sha256
    assert original.sources != changed.sources
    assert all(source.byte_count > 0 for source in original.sources)


def test_grouped_replay_rejects_source_role_substitution(tmp_path: Path) -> None:
    configuration, input_path, authority = _write_fixture(tmp_path)
    records = [json.loads(line) for line in input_path.read_text(encoding="utf-8").splitlines()]
    records[0]["source_id"], records[1]["source_id"] = (
        records[1]["source_id"],
        records[0]["source_id"],
    )
    input_path.write_bytes(b"".join(_canonical(item) for item in records))

    with pytest.raises(ReplayError) as captured:
        replay_closed_files(
            root=tmp_path,
            configuration=configuration.relative_to(tmp_path),
            input_path=input_path.relative_to(tmp_path),
            authority_path=authority.relative_to(tmp_path),
        )

    assert captured.value.code == "source_role_mismatch"


@pytest.mark.parametrize(
    ("raw", "code"),
    (
        (b"{]\n", "malformed_json"),
        (b"\xff\n", "invalid_utf8"),
        (b'{"x":1,"x":2}\n', "duplicate_key"),
        (b"{}\r\n", "noncanonical_jsonl"),
        (b"\n", "blank_line"),
        (b"{}", "noncanonical_jsonl"),
        (b"x" * (DEFAULT_MAX_REPLAY_LINE_BYTES + 1) + b"\n", "oversized_line"),
        (b"x" * (DEFAULT_MAX_REPLAY_BYTES + 1), "oversized"),
    ),
    ids=(
        "malformed-json",
        "invalid-utf8",
        "duplicate-key",
        "crlf",
        "blank-line",
        "missing-lf",
        "oversized-line",
        "oversized-file",
    ),
)
def test_parser_rejects_malformed_encoding_line_and_size_cases_with_stable_codes(
    raw: bytes, code: str
) -> None:
    with pytest.raises(ReplayError) as captured:
        parse_observation_jsonl(raw)
    assert captured.value.code == code


def test_parser_rejects_duplicate_exact_lines_and_duplicate_ids(tmp_path: Path) -> None:
    _, input_path, _ = _write_fixture(tmp_path)
    lines = input_path.read_bytes().splitlines(keepends=True)

    with pytest.raises(ReplayError) as captured:
        parse_observation_jsonl(lines[0] + lines[0])
    assert captured.value.code == "duplicate_input"

    changed = json.loads(lines[0])
    changed["command_id"] = "command-id:changed"
    with pytest.raises(ReplayError) as captured:
        parse_observation_jsonl(lines[0] + _canonical(changed))
    assert captured.value.code == "duplicate_observation_id"


def test_parser_non_bytes_input_is_a_typed_replay_error() -> None:
    with pytest.raises(ReplayError) as captured:
        parse_observation_jsonl(bytearray(b"{}\n"))  # type: ignore[arg-type]
    assert captured.value.code == "invalid_bytes"


@pytest.mark.parametrize(
    ("field", "relative", "code"),
    (
        ("input_path", Path("../outside.jsonl"), "path_escape"),
        ("input_path", Path("C:/absolute.jsonl"), "path_escape"),
        ("authority_path", Path("../authority.json"), "path_escape"),
        ("configuration", Path("../configuration.json"), "invalid_configuration"),
    ),
)
def test_replay_rejects_traversal_and_absolute_paths(
    tmp_path: Path, field: str, relative: Path, code: str
) -> None:
    configuration, input_path, authority = _write_fixture(tmp_path)
    arguments = {
        "root": tmp_path,
        "configuration": configuration.relative_to(tmp_path),
        "input_path": input_path.relative_to(tmp_path),
        "authority_path": authority.relative_to(tmp_path),
    }
    arguments[field] = relative

    with pytest.raises(ReplayError) as captured:
        replay_closed_files(**cast(Any, arguments))
    assert captured.value.code == code


def test_replay_rejects_symlink_and_non_regular_inputs(tmp_path: Path) -> None:
    configuration, input_path, authority = _write_fixture(tmp_path)
    with pytest.raises(ReplayError) as captured:
        replay_closed_files(
            root=tmp_path,
            configuration=configuration.relative_to(tmp_path),
            input_path=Path("."),
            authority_path=authority.relative_to(tmp_path),
        )
    assert captured.value.code == "non_regular"

    link = tmp_path / "linked.jsonl"
    try:
        os.symlink(input_path, link)
    except OSError as error:
        pytest.skip(f"symlink creation unavailable: {error}")
    with pytest.raises(ReplayError) as captured:
        replay_closed_files(
            root=tmp_path,
            configuration=configuration.relative_to(tmp_path),
            input_path=link.relative_to(tmp_path),
            authority_path=authority.relative_to(tmp_path),
        )
    assert captured.value.code == "path_symlink"


def _batch(
    records: list[dict[str, Any]], sequence: int, timestamp: str, tag: str
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for record in records:
        item = dict(record)
        item["sequence_number"] = sequence
        item["observed_at"] = timestamp
        item["received_at"] = timestamp
        item["observation_id"] = f"{record['source_domain']}:{tag}"
        if item["source_domain"] == "production_ai":
            item["command_id"] = f"command-id:{tag}"
        if item["source_domain"] == "independent_source_health":
            item["last_source_sequence"] = sequence
        result.append(item)
    return result


def _replay_records(tmp_path: Path, records: list[dict[str, Any]]) -> Any:
    configuration, input_path, authority = _write_fixture(tmp_path)
    input_path.write_bytes(b"".join(_canonical(record) for record in records))
    return replay_closed_files(
        root=tmp_path,
        configuration=configuration.relative_to(tmp_path),
        input_path=input_path.relative_to(tmp_path),
        authority_path=authority.relative_to(tmp_path),
    )


def test_replay_rejects_mixed_run_ids_incomplete_and_missing_sources(tmp_path: Path) -> None:
    _, input_path, _ = _write_fixture(tmp_path)
    records = [json.loads(line) for line in input_path.read_text(encoding="utf-8").splitlines()]

    mixed = [dict(item) for item in records]
    mixed[-1]["run_id"] = "run:other"
    with pytest.raises(ReplayError) as captured:
        _replay_records(tmp_path / "mixed", mixed)
    assert captured.value.code == "run_mismatch"

    with pytest.raises(ReplayError) as captured:
        _replay_records(tmp_path / "incomplete", records[:-1])
    assert captured.value.code == "incomplete_batch"

    missing = [dict(item) for item in records]
    missing[-1]["source_id"] = "independent-health-monitor:unexpected"
    with pytest.raises(ReplayError) as captured:
        _replay_records(tmp_path / "missing", missing)
    assert captured.value.code == "missing_source"


@pytest.mark.parametrize(
    ("case", "expected_reason"),
    (
        ("missing_sequence", "missing_sequence"),
        ("rollback", "sequence_rollback"),
        ("future", "configuration_invalid_at_evaluation"),
        ("stale", "stale_observation"),
        ("frozen", "frozen_source"),
        ("contradictory", "contradictory_state"),
    ),
)
def test_replay_source_batch_faults_fail_closed_deterministically(
    tmp_path: Path, case: str, expected_reason: str
) -> None:
    _, input_path, _ = _write_fixture(tmp_path)
    base = [json.loads(line) for line in input_path.read_text(encoding="utf-8").splitlines()]
    first = _batch(base, 0, "2026-09-03T12:00:00Z", "first")
    if case == "missing_sequence":
        records = first + _batch(base, 2, "2026-09-03T12:00:00.200000Z", "gap")
    elif case == "rollback":
        records = (
            first
            + _batch(base, 1, "2026-09-03T12:00:00.100000Z", "second")
            + _batch(base, 0, "2026-09-03T12:00:00.200000Z", "rollback")
        )
    elif case == "future":
        records = first + _batch(base, 1, "2026-09-04T00:00:00Z", "future")
    elif case == "stale":
        records = _batch(base, 0, "2026-09-03T11:59:58Z", "stale")
        for item in records:
            item["received_at"] = "2026-09-03T12:00:00Z"
    elif case == "frozen":
        second = _batch(base, 1, "2026-09-03T12:00:00Z", "frozen")
        for item in second:
            item["received_at"] = "2026-09-03T12:00:00.100000Z"
        records = first + second
    else:
        records = first
        records[1].update(
            occupancy="contradictory",
            motion_state="contradictory",
            quality="contradictory",
            speed_mps=None,
            acceleration_mps2=None,
        )

    first_result = _replay_records(tmp_path / "run-a", records)
    second_result = _replay_records(tmp_path / "run-b", records)

    assert first_result.canonical_bytes == second_result.canonical_bytes
    assert first_result.report["final_state"]["latched"] is True
    assert expected_reason in first_result.report["decisions"][-1]["reason_codes"]


@pytest.mark.parametrize(
    ("case", "code"),
    (
        ("changed_configuration", "invalid_configuration"),
        ("forged_configuration", "invalid_configuration"),
        ("expired_configuration", "invalid_configuration"),
        ("changed_authority", "invalid_authority"),
        ("forged_authority", "invalid_configuration"),
        ("wrong_scope_authority", "invalid_configuration"),
    ),
)
def test_replay_rejects_changed_forged_expired_and_wrong_scope_trust_inputs(
    tmp_path: Path, case: str, code: str
) -> None:
    configuration, input_path, authority = _write_fixture(tmp_path)
    if case == "changed_configuration":
        configuration.write_bytes(configuration.read_bytes() + b" ")
    elif case == "forged_configuration":
        document = json.loads(configuration.read_bytes())
        document["signature"] = "ed25519:" + "11" * 64
        raw = _canonical(document)
        configuration.write_bytes(raw)
        policy = json.loads(authority.read_bytes())
        policy["approved_configuration_sha256"] = "sha256:" + hashlib.sha256(raw).hexdigest()
        authority.write_bytes(_canonical(policy))
    elif case == "expired_configuration":
        records = [json.loads(line) for line in input_path.read_text(encoding="utf-8").splitlines()]
        input_path.write_bytes(
            b"".join(
                _canonical(item) for item in _batch(records, 0, "2026-09-04T00:00:00Z", "expired")
            )
        )
    elif case == "changed_authority":
        policy = json.loads(authority.read_bytes())
        policy["unexpected"] = True
        authority.write_bytes(_canonical(policy))
    elif case == "forged_authority":
        policy = json.loads(authority.read_bytes())
        policy["ed25519_public_key"] = "ed25519-public:" + "00" * 32
        authority.write_bytes(_canonical(policy))
    else:
        policy = json.loads(authority.read_bytes())
        policy["scope_id"] = "SCOPE-OTHER-001"
        authority.write_bytes(_canonical(policy))

    with pytest.raises(ReplayError) as captured:
        replay_closed_files(
            root=tmp_path,
            configuration=configuration.relative_to(tmp_path),
            input_path=input_path.relative_to(tmp_path),
            authority_path=authority.relative_to(tmp_path),
        )
    assert captured.value.code == code
