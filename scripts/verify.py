"""Canonical local verification gate."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
TEXT_SUFFIXES = {".md", ".py", ".json", ".toml", ".yaml", ".yml", ".txt"}


def executable(name: str) -> str:
    resolved = shutil.which(name)
    if resolved is None:
        raise SystemExit(f"required executable not found: {name}")
    return resolved


def run(*command: str, pythonpath: str | None = None) -> None:
    prefix = "PYTHONPATH= " if pythonpath == "" else ""
    print("+", prefix + " ".join(command), flush=True)
    resolved = (executable(command[0]), *command[1:])
    environment = None
    if pythonpath is not None:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = pythonpath
    subprocess.run(resolved, cwd=ROOT, check=True, env=environment)  # noqa: S603


def repository_files() -> list[Path]:
    result = subprocess.run(  # noqa: S603 -- resolved trusted git executable
        [executable("git"), "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [ROOT / line for line in result.stdout.splitlines() if line]


def check_text_hygiene() -> None:
    home_marker = "C:" + "\\Users\\"
    secret_pattern = re.compile(
        r"(?i)(api[_-]?key|password|secret|access[_-]?token)\s*[:=]\s*['\"][^'\"]+"
    )
    errors: list[str] = []
    for path in repository_files():
        if path.suffix.lower() not in TEXT_SUFFIXES or not path.is_file():
            continue
        raw = path.read_bytes()
        relative = path.relative_to(ROOT).as_posix()
        if b"\r\n" in raw or b"\r" in raw:
            errors.append(f"non-LF line endings: {relative}")
        text = raw.decode("utf-8")
        if home_marker in text:
            errors.append(f"absolute Windows user path: {relative}")
        if path.name != "verify.py" and secret_pattern.search(text):
            errors.append(f"possible embedded secret: {relative}")
    if errors:
        raise SystemExit("\n".join(errors))
    print("text hygiene: ok")


def check_schemas() -> None:
    sys.path.insert(0, str(ROOT))
    from scripts.export_schemas import SCHEMAS, render

    for name, schema in SCHEMAS.items():
        expected = render(schema)
        actual = (ROOT / "schemas" / name).read_text(encoding="utf-8")
        if actual != expected:
            raise SystemExit(f"schema is stale: schemas/{name}")
    print("schemas: ok")


def check_runtime_schemas() -> None:
    from scripts.export_runtime_schemas import RUNTIME_SCHEMAS, render

    schema_root = ROOT / "schemas" / "runtime"
    actual_names = (
        {path.name for path in schema_root.glob("*.schema.json")} if schema_root.is_dir() else set()
    )
    expected_names = set(RUNTIME_SCHEMAS)
    if actual_names != expected_names:
        missing = sorted(expected_names - actual_names)
        extra = sorted(actual_names - expected_names)
        raise SystemExit(f"runtime schema set drift: missing={missing}; extra={extra}")
    for name, schema in RUNTIME_SCHEMAS.items():
        expected = render(schema)
        actual = (schema_root / name).read_bytes()
        if actual != expected:
            raise SystemExit(f"schema is stale: schemas/runtime/{name}")
    print("runtime schemas: ok")


def check_scenario_manifest() -> None:
    from scripts.verify_scenario_manifest import verify_scenario_manifest

    errors = verify_scenario_manifest(ROOT / "scenarios" / "robot_cell_v1")
    if errors:
        raise SystemExit("\n".join(errors))
    print("runtime scenario manifest: ok")


def check_benchmark() -> None:
    from oscillink_safety_ops.benchmark import verify_benchmark

    result = verify_benchmark(ROOT / "benchmark" / "robot_cell_v1", repository_root=ROOT)
    if (
        result.total_cases != 36
        or result.exact_matches != 36
        or result.fault_families != 12
        or result.repeat_runs != 3
        or result.network_accessed is not False
    ):
        raise SystemExit("frozen benchmark verification totals are invalid")
    print("benchmark: 36/36 exact; 12 fault families; 3 repeat runs")


def check_demo() -> None:
    from scripts.verify_demo import verify_demo

    result = verify_demo(
        ROOT / "demo",
        benchmark_root=ROOT / "benchmark" / "robot_cell_v1",
        repository_root=ROOT,
    )
    if (
        result.total_cases != 36
        or result.exact_matches != 36
        or result.control_surfaces != 0
        or result.network_accessed is not False
    ):
        raise SystemExit("static demo verification totals are invalid")
    print("demo: 36 scenarios; exact generated assets; no network/control surfaces")


def check_tla_result() -> None:
    from scripts.verify_tla import verify_formal_result_binding

    errors = verify_formal_result_binding(ROOT)
    if errors:
        raise SystemExit("\n".join(errors))
    print("formal result binding: ok")


def check_repository_surface() -> None:
    from scripts.verify_repository_surface import validate_repository_surface

    errors = validate_repository_surface(ROOT)
    if errors:
        raise SystemExit("\n".join(errors))
    print("repository surface: ok")


def verify_envelope_fixture(fixture: Path) -> str:
    from oscillink_safety_ops.io import load_envelope, verify_envelope_payload

    envelope = load_envelope(fixture / "envelope.json")
    return verify_envelope_payload(envelope, root=fixture)


def check_osha_catalog() -> None:
    from oscillink_safety_ops.regulations import validate_osha_catalog

    path = ROOT / "knowledge" / "osha" / "catalog.json"
    catalog = json.loads(path.read_text(encoding="utf-8"))
    if validate_osha_catalog(catalog) != 67:
        raise SystemExit("OSHA catalog does not match the reviewed 67-part source snapshot")
    print("OSHA catalog: ok")


def check_fixture() -> None:
    from oscillink_safety_ops.domain import OperationalSourceType
    from oscillink_safety_ops.io import (
        load_operational_jsonl,
        load_packet,
        load_plan,
        verify_manifest,
    )

    fixture = ROOT / "tests" / "fixtures" / "synthetic_press"
    verified = verify_manifest(fixture / "manifest.json")
    packet = load_packet(fixture / "packet.json")
    load_plan(fixture / "plan.json")
    missing = {source.sha256 for source in packet.sources} - verified
    if missing:
        raise SystemExit("fixture packet contains an unpinned source hash")
    verify_envelope_fixture(fixture)
    print("fixture: ok")

    operational = ROOT / "tests" / "fixtures" / "operational_evidence"
    operational_hashes = verify_manifest(operational / "manifest.json")
    batch = load_operational_jsonl(
        operational / "synthetic-operational.jsonl",
        batch_id="batch:synthetic-operational-001",
        source_revision="export:synthetic-operational-001",
        adapter_config_sha256=("sha256:" + "a" * 64),
    )
    expected_sources = {
        OperationalSourceType.FIRE_SUPPRESSION,
        OperationalSourceType.AMMONIA_DETECTION,
        OperationalSourceType.AUTONOMOUS_SYSTEM,
    }
    if {record.source_type for record in batch.records} != expected_sources:
        raise SystemExit("operational fixture does not cover all declared synthetic sources")
    if batch.source_artifact_sha256 not in operational_hashes:
        raise SystemExit("operational fixture source hash is not pinned by its manifest")
    print("operational fixture: ok")


def main() -> None:
    check_text_hygiene()
    check_repository_surface()
    check_schemas()
    check_runtime_schemas()
    check_scenario_manifest()
    check_benchmark()
    check_demo()
    check_tla_result()
    check_osha_catalog()
    check_fixture()
    run("uv", "run", "python", "scripts/verify_production_ai_compromise.py", pythonpath="")
    run("uv", "run", "python", "scripts/verify_process_restart.py", pythonpath="")
    run("uv", "run", "python", "scripts/verify_traceability.py", pythonpath="")
    run("uv", "run", "ruff", "check", ".")
    run("uv", "run", "ruff", "format", "--check", ".")
    run("uv", "run", "mypy")
    run("uv", "build")
    run("uv", "run", "python", "-m", "pytest", "-q")
    print("verification: ok")


if __name__ == "__main__":
    main()
