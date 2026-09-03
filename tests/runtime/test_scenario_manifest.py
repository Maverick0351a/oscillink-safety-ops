"""Exact-byte production runtime-corpus manifest tests."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from scripts.verify import check_scenario_manifest
from scripts.verify_scenario_manifest import verify_scenario_manifest


def _copy_corpus(tmp_path: Path) -> Path:
    root = Path(__file__).resolve().parents[2]
    destination = tmp_path / "robot_cell_v1"
    shutil.copytree(root / "scenarios" / "robot_cell_v1", destination)
    return destination


def test_canonical_verifier_checks_production_manifest() -> None:
    check_scenario_manifest()


def test_production_manifest_binds_every_scenario_configuration_authority_and_report() -> None:
    root = Path(__file__).resolve().parents[2]
    corpus = root / "scenarios" / "robot_cell_v1"

    assert verify_scenario_manifest(corpus) == ()
    document = json.loads((corpus / "MANIFEST.json").read_bytes())
    entries = document["files"]
    assert [entry["path"] for entry in entries] == [
        "authority.json",
        "clean.jsonl",
        "configuration.json",
        "contradictory-source.jsonl",
        "expected/clean.report.json",
        "expected/contradictory-source.report.json",
        "expected/stale-source.report.json",
        "expected/zone-entry.report.json",
        "stale-source.jsonl",
        "zone-entry.jsonl",
    ]
    assert all(type(entry["byte_count"]) is int and entry["byte_count"] > 0 for entry in entries)
    assert all(entry["sha256"].startswith("sha256:") for entry in entries)


def test_manifest_detects_changed_bytes_and_byte_count(tmp_path: Path) -> None:
    corpus = _copy_corpus(tmp_path)
    path = corpus / "clean.jsonl"
    path.write_bytes(path.read_bytes() + b"\n")

    errors = verify_scenario_manifest(corpus)

    assert errors == (
        "byte count mismatch: clean.jsonl",
        "SHA-256 mismatch: clean.jsonl",
    )


def test_manifest_rejects_missing_extra_duplicate_and_nonpositive_entries(tmp_path: Path) -> None:
    corpus = _copy_corpus(tmp_path)
    manifest_path = corpus / "MANIFEST.json"
    document = json.loads(manifest_path.read_bytes())
    document["files"] = document["files"][1:]
    document["files"].append(dict(document["files"][0]))
    document["files"][0]["byte_count"] = 0
    (corpus / "unexpected.jsonl").write_bytes(b"{}\n")
    manifest_path.write_bytes(
        (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    )

    errors = verify_scenario_manifest(corpus)

    assert "missing manifest entry: authority.json" in errors
    assert "duplicate manifest path: clean.jsonl" in errors
    assert "invalid byte_count: clean.jsonl" in errors
    assert "unmanifested corpus file: unexpected.jsonl" in errors


def test_manifest_rejects_any_unmanifested_private_or_hidden_file(tmp_path: Path) -> None:
    corpus = _copy_corpus(tmp_path)
    (corpus / "demo-private-key.pem").write_text("not-a-real-key", encoding="utf-8")

    errors = verify_scenario_manifest(corpus)

    assert "unmanifested corpus file: demo-private-key.pem" in errors


def test_manifest_rejects_noncanonical_malformed_and_escaping_paths(tmp_path: Path) -> None:
    corpus = _copy_corpus(tmp_path)
    manifest_path = corpus / "MANIFEST.json"
    original = manifest_path.read_bytes()

    manifest_path.write_bytes(original.replace(b"\n", b"\r\n"))
    assert verify_scenario_manifest(corpus) == ("manifest must be canonical UTF-8 JSON plus LF",)

    manifest_path.write_bytes(b'{"schema_version":1,"schema_version":1}\n')
    assert verify_scenario_manifest(corpus) == (
        "manifest contains duplicate JSON key: schema_version",
    )

    manifest_path.write_bytes(
        b'{"corpus_format":"oscillink-runtime-scenario-manifest-v1",'
        b'"files":[{"byte_count":1,"path":"../outside",'
        b'"role":"scenario_input","sha256":"sha256:' + b"0" * 64 + b'"}],'
        b'"schema_version":1,"scope_id":"SCOPE-ROBOT-CELL-001"}\n'
    )
    assert verify_scenario_manifest(corpus) == ("manifest path escapes corpus: ../outside",)
