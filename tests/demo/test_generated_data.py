"""Exact mechanical binding for the generated static demonstration."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = ROOT / "benchmark" / "robot_cell_v1"


def _sha256(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _run_generator(destination: Path) -> dict[str, bytes]:
    result = subprocess.run(  # noqa: S603 -- exact current Python executable and local script
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_demo.py"),
            "--benchmark-root",
            str(BENCHMARK),
            "--destination",
            str(destination),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return {
        path.relative_to(destination).as_posix(): path.read_bytes()
        for path in destination.rglob("*")
        if path.is_file()
    }


def test_demo_data_binds_all_exact_expected_results_and_metrics(tmp_path: Path) -> None:
    files = _run_generator(tmp_path / "demo")
    data = json.loads(files["assets/data.json"])
    expected_lines = (BENCHMARK / "expected-results.jsonl").read_bytes().splitlines(keepends=True)
    expected = [json.loads(line) for line in expected_lines]
    metrics_raw = (BENCHMARK / "metrics.json").read_bytes()
    manifest_raw = (BENCHMARK / "benchmark-manifest.json").read_bytes()
    manifest = json.loads(manifest_raw)
    manifest_files = {item["path"]: item["sha256"] for item in manifest["files"]}

    assert data["schema_version"] == 1
    assert data["demo_format"] == "oscillink-safety-monitor-demo-v1"
    assert data["metrics"] == json.loads(metrics_raw)
    assert len(data["cases"]) == 36
    assert [item["case_id"] for item in data["cases"]] == [item["case_id"] for item in expected]
    for actual, source, raw in zip(data["cases"], expected, expected_lines, strict=True):
        report_sha256 = actual["report_sha256"]
        assert {key: value for key, value in actual.items() if key != "report_sha256"} == source
        assert report_sha256 == _sha256(raw)
    assert data["source"]["benchmark_manifest_sha256"] == _sha256(manifest_raw)
    assert data["source"]["expected_results_sha256"] == manifest_files["expected-results.jsonl"]
    assert data["source"]["metrics_sha256"] == manifest_files["metrics.json"]
    payload_sha256 = data.pop("payload_sha256")
    canonical_payload = (
        json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    assert payload_sha256 == _sha256(canonical_payload)


def test_demo_generation_is_byte_repeatable_and_has_no_hand_entered_metrics(
    tmp_path: Path,
) -> None:
    first = _run_generator(tmp_path / "first")
    second = _run_generator(tmp_path / "second")

    assert first == second
    assert set(first) == {"assets/app.js", "assets/data.json", "assets/styles.css", "index.html"}
    html = first["index.html"].decode("utf-8")
    before_data, _, after_data = html.partition('<script id="demo-data" type="application/json">')
    _, separator, after_data = after_data.partition("</script>")
    assert separator
    authored_interface = before_data + after_data
    assert "36/36" not in authored_interface
    assert "108" not in authored_interface
    assert '"total_cases":36' not in first["assets/app.js"].decode("utf-8")


def test_committed_demo_matches_the_generator(tmp_path: Path) -> None:
    generated = _run_generator(tmp_path / "demo")
    committed = {
        path.relative_to(ROOT / "demo").as_posix(): path.read_bytes()
        for path in (ROOT / "demo").rglob("*")
        if path.is_file()
    }

    assert committed == generated
