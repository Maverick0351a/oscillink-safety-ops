from __future__ import annotations

import importlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "2943db23ceb075e8955867903069cd5e043fee45"


def test_history_audit_derives_exact_reachable_baseline_without_values() -> None:
    module = importlib.import_module("scripts.audit_history")

    report = module.build_history_report(ROOT, BASELINE)
    serialized = module.canonical_json(report)

    assert report["scope"] == {
        "baseline_commit": BASELINE,
        "commit_count": 28,
        "object_count": 657,
        "blob_revision_count": 423,
        "definition": f"all Git objects reachable from {BASELINE}",
        "unreachable_objects_included": False,
    }
    assert report["scanner"] == {
        "archive_sha256": "d29144deff3a68aa93ced33dddf84b7fdc26070add4aa0f4513094c8332afc4e",
        "findings_count": 0,
        "name": "Gitleaks",
        "result_source": "maintainer-provided redacted full-history scan",
        "version": "8.30.1",
    }
    assert report["blob_inventory"]["over_10_mib_count"] == 0
    assert report["blob_inventory"]["largest"][0] == {
        "object_id": "056726e13d7ee4b959c83209fce1331316734377",
        "path": "demo/index.html",
        "size_bytes": 105826,
    }
    assert report["risky_historical_filenames"] == []
    assert report["personal_absolute_path_indicators"]["count"] == 2
    assert all(
        "indicator_value" not in item
        for item in report["personal_absolute_path_indicators"]["items"]
    )
    assert b"C:/Users/" not in serialized and b"C:\\Users\\" not in serialized


def test_history_audit_classifies_public_and_test_key_indicators_without_calling_them_secrets() -> (
    None
):
    module = importlib.import_module("scripts.audit_history")

    report = module.build_history_report(ROOT, BASELINE)
    classifications = {item["id"]: item for item in report["indicator_classifications"]}

    assert classifications["demo-public-verification-key"]["classification"] == (
        "project-authored public Ed25519 verification bytes; intentionally public; not a secret"
    )
    assert classifications["private-key-marker-rejection-fixture"]["classification"] == (
        "negative-test marker used to verify rejection; not a secret"
    )
    assert classifications["deterministic-test-signing-seed"]["classification"] == (
        "deterministic test-only signing seed; not an operational credential or secret"
    )
    assert "secret finding" not in json.dumps(report["personal_absolute_path_indicators"]).lower()


def test_history_audit_output_is_canonical_and_deterministic(tmp_path: Path) -> None:
    module = importlib.import_module("scripts.audit_history")
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"

    module.write_history_report(ROOT, BASELINE, first)
    module.write_history_report(ROOT, BASELINE, second)

    assert first.read_bytes() == second.read_bytes()
    assert first.read_bytes() == module.canonical_json(json.loads(first.read_bytes()))


def test_tracked_history_baseline_report_has_required_audit_and_limitations() -> None:
    path = ROOT / "docs" / "audits" / "history-baseline-2943db2.json"
    report = json.loads(path.read_bytes())

    assert report["scope"]["baseline_commit"] == BASELINE
    assert report["dependency_inventory"]["pip_audit"]["version"] == "2.10.1"
    assert report["dependency_inventory"]["pip_audit"]["vulnerability_count"] == 0
    assert report["dependency_inventory"]["license_inventory"]["status"] == "incomplete"
    assert report["limitations"]
    assert (
        "exact release-candidate commit must be scanned externally after commit"
        in report["limitations"]
    )
