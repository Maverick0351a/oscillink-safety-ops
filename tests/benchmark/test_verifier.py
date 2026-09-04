"""Canonical benchmark verifier and adversarial integrity tests."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from oscillink_safety_ops.benchmark import BenchmarkVerificationError
from scripts import generate_benchmark as benchmark_generator
from scripts.generate_benchmark import generate_benchmark
from scripts.verify_benchmark import verify_benchmark as verify_benchmark

SOURCE_COMMIT = "dc27cf6ce25be97b0cb70b698679445103409e7b"
MAX_BENCHMARK_FILE_BYTES = 4 * 1024 * 1024


def _rewrite_canonical(path: Path, document: object) -> None:
    path.write_bytes(
        (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    )


def _resign_file(benchmark: Path, relative: str) -> None:
    raw = (benchmark / relative).read_bytes()
    manifest_path = benchmark / "benchmark-manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    entry = next(item for item in manifest["files"] if item["path"] == relative)
    entry["byte_count"] = len(raw)
    entry["sha256"] = "sha256:" + hashlib.sha256(raw).hexdigest()
    _rewrite_canonical(manifest_path, manifest)


def _generated(tmp_path: Path) -> tuple[Path, Path]:
    repository = Path(__file__).resolve().parents[2]
    benchmark = tmp_path / "robot_cell_v1"
    generate_benchmark(
        benchmark, source_repository=repository, runtime_baseline_commit=SOURCE_COMMIT
    )
    return benchmark, repository


def test_verifier_recomputes_exact_outputs_metrics_and_repeatability(tmp_path: Path) -> None:
    benchmark, repository = _generated(tmp_path)

    summary = verify_benchmark(benchmark, repository_root=repository)

    assert summary.total_cases == 36
    assert summary.exact_matches == 36
    assert summary.fault_families == 12
    assert summary.repeat_runs == 3
    assert summary.network_accessed is False


def test_verifier_rejects_an_internally_consistent_35_case_corpus(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    documents = benchmark_generator.build_case_documents()[:-1]
    monkeypatch.setattr(benchmark_generator, "build_case_documents", lambda: documents)
    benchmark, repository = _generated(tmp_path)

    with pytest.raises(BenchmarkVerificationError, match="exactly 36 cases") as captured:
        verify_benchmark(benchmark, repository_root=repository)

    assert captured.value.code == "case_count"


def test_verifier_rejects_boolean_manifest_schema_version(tmp_path: Path) -> None:
    benchmark, repository = _generated(tmp_path)
    manifest_path = benchmark / "benchmark-manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["schema_version"] = True
    _rewrite_canonical(manifest_path, manifest)

    with pytest.raises(BenchmarkVerificationError, match="manifest identity") as captured:
        verify_benchmark(benchmark, repository_root=repository)

    assert captured.value.code == "manifest_identity"


def test_verifier_rejects_resigned_expected_output_tampering(tmp_path: Path) -> None:
    benchmark, repository = _generated(tmp_path)
    expected_path = benchmark / "expected-results.jsonl"
    lines = expected_path.read_bytes().splitlines()
    first = json.loads(lines[0])
    first["title"] = "Tampered but schema-valid title"
    lines[0] = _canonical_line(first).rstrip(b"\n")
    expected_path.write_bytes(b"\n".join(lines) + b"\n")
    _resign_file(benchmark, "expected-results.jsonl")

    with pytest.raises(BenchmarkVerificationError) as captured:
        verify_benchmark(benchmark, repository_root=repository)

    assert captured.value.code == "exact_output_mismatch"


def test_verifier_rejects_resigned_derived_metrics_tampering(tmp_path: Path) -> None:
    benchmark, repository = _generated(tmp_path)
    metrics_path = benchmark / "metrics.json"
    metrics = json.loads(metrics_path.read_bytes())
    metrics["exact_matches"] = 0
    _rewrite_canonical(metrics_path, metrics)
    _resign_file(benchmark, "metrics.json")

    with pytest.raises(BenchmarkVerificationError) as captured:
        verify_benchmark(benchmark, repository_root=repository)

    assert captured.value.code == "wrong_totals"


def test_verifier_rejects_resigned_private_key_marker(tmp_path: Path) -> None:
    benchmark, repository = _generated(tmp_path)
    readme = benchmark / "README.md"
    readme.write_bytes(readme.read_bytes() + b"\n-----BEGIN PRIVATE KEY-----\n")
    _resign_file(benchmark, "README.md")

    with pytest.raises(BenchmarkVerificationError) as captured:
        verify_benchmark(benchmark, repository_root=repository)

    assert captured.value.code == "private_key"


def test_verifier_rejects_resigned_noncanonical_jsonl(tmp_path: Path) -> None:
    benchmark, repository = _generated(tmp_path)
    cases_path = benchmark / "cases.jsonl"
    cases_path.write_bytes(cases_path.read_bytes().replace(b"\n", b"\r\n", 1))
    _resign_file(benchmark, "cases.jsonl")

    with pytest.raises(BenchmarkVerificationError) as captured:
        verify_benchmark(benchmark, repository_root=repository)

    assert captured.value.code == "malformed_jsonl"


def test_verifier_rejects_unmanifested_files(tmp_path: Path) -> None:
    benchmark, repository = _generated(tmp_path)
    (benchmark / "unexpected.txt").write_text("untrusted", encoding="utf-8")

    with pytest.raises(BenchmarkVerificationError) as captured:
        verify_benchmark(benchmark, repository_root=repository)

    assert captured.value.code == "unmanifested_file"


def test_manifest_uses_non_self_referential_baseline_and_source_hashes(tmp_path: Path) -> None:
    benchmark, _repository = _generated(tmp_path)
    manifest_path = benchmark / "benchmark-manifest.json"
    manifest = json.loads(manifest_path.read_bytes())

    assert "source_commit" not in manifest
    assert manifest["runtime_baseline_commit"] == SOURCE_COMMIT
    assert manifest["benchmark_source_sha256"].startswith("sha256:")
    assert manifest["generator_source_sha256"].startswith("sha256:")


def test_verifier_accepts_exact_sources_when_repository_head_differs(tmp_path: Path) -> None:
    benchmark, repository = _generated(tmp_path)
    future_repository = tmp_path / "future-repository"
    (future_repository / ".git").mkdir(parents=True)
    (future_repository / ".git" / "HEAD").write_text("f" * 40 + "\n", encoding="ascii")
    for relative in (
        Path("scripts/generate_benchmark.py"),
        Path("src/oscillink_safety_ops/benchmark.py"),
    ):
        target = future_repository / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repository / relative, target)

    summary = verify_benchmark(benchmark, repository_root=future_repository)

    assert summary.total_cases == 36


def test_verifier_rejects_runtime_baseline_identity_drift(tmp_path: Path) -> None:
    benchmark, repository = _generated(tmp_path)
    manifest_path = benchmark / "benchmark-manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["runtime_baseline_commit"] = "0" * 40
    _rewrite_canonical(manifest_path, manifest)

    with pytest.raises(BenchmarkVerificationError) as captured:
        verify_benchmark(benchmark, repository_root=repository)

    assert captured.value.code == "source_drift"


def test_verifier_rejects_exact_benchmark_source_drift(tmp_path: Path) -> None:
    benchmark, repository = _generated(tmp_path)
    drifted_repository = tmp_path / "drifted-repository"
    for relative in (
        Path("scripts/generate_benchmark.py"),
        Path("src/oscillink_safety_ops/benchmark.py"),
    ):
        target = drifted_repository / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repository / relative, target)
    with (drifted_repository / "src/oscillink_safety_ops/benchmark.py").open("ab") as stream:
        stream.write(b"\n# drift\n")

    with pytest.raises(BenchmarkVerificationError, match="benchmark source") as captured:
        verify_benchmark(benchmark, repository_root=drifted_repository)

    assert captured.value.code == "source_drift"


def test_verifier_rejects_oversized_resigned_files_before_loading_them(tmp_path: Path) -> None:
    benchmark, repository = _generated(tmp_path)
    readme = benchmark / "README.md"
    readme.write_bytes(b"x" * (MAX_BENCHMARK_FILE_BYTES + 1))
    _resign_file(benchmark, "README.md")

    with pytest.raises(BenchmarkVerificationError, match="maximum byte count") as captured:
        verify_benchmark(benchmark, repository_root=repository)

    assert captured.value.code == "file_too_large"


def _canonical_line(document: object) -> bytes:
    return (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
