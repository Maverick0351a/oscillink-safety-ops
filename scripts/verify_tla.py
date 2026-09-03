"""Execute pinned TLC deterministically and verify its canonical result binding."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH: Final = Path("assurance/tla/Supervisor.tla")
CONFIG_PATH: Final = Path("assurance/tla/Supervisor.cfg")
RESULT_PATH: Final = Path("assurance/tla/formal-result.json")
RESULT_FORMAT: Final = "oscillink-tlc-formal-result-v1"
EXPECTED_JAR_SHA256: Final = "936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88"
EXPECTED_TLC_VERSION: Final = "TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)"
INVARIANTS: Final = (
    "TypeOK",
    "ProductionAuthoritySeparation",
    "LatchClearRequiresFullRecovery",
    "AckIsNotReset",
    "ResetIsNotFreshStart",
    "RebootPreservesLatch",
    "NoMotionCommandDuringRecovery",
    "FaultsFailClosed",
)
MAX_SET_SIZE: Final = 100_000
HEAP_MAX_MIB: Final = 512
TIMEOUT_SECONDS: Final = 120


class FormalVerificationError(ValueError):
    """Typed deterministic formal-runner or result-binding failure."""

    def __init__(self, code: str, message: str | None = None) -> None:
        self.code = code
        super().__init__(message or code)


@dataclass(frozen=True, slots=True)
class TlcCounts:
    """Exact finite-state summary parsed from a successful TLC run."""

    generated_states: int
    distinct_states: int
    states_left_on_queue: int
    search_depth: int
    invariant_success: bool


def _sha256(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _canonical(value: object) -> bytes:
    return (
        json.dumps(
            value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
        )
        + "\n"
    ).encode("utf-8")


def _regular_bytes(path: Path, *, kind: str, maximum: int = 1024 * 1024) -> bytes:
    try:
        metadata = path.lstat()
    except FileNotFoundError as error:
        raise FormalVerificationError(f"missing_{kind}", f"{kind} is missing: {path}") from error
    except OSError as error:
        raise FormalVerificationError(
            f"unavailable_{kind}", f"{kind} is unavailable: {path}"
        ) from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise FormalVerificationError(f"invalid_{kind}", f"{kind} must be a regular file: {path}")
    if metadata.st_size < 1 or metadata.st_size > maximum:
        raise FormalVerificationError(f"invalid_{kind}", f"{kind} size is invalid: {path}")
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise FormalVerificationError(
            f"unavailable_{kind}", f"{kind} cannot be read: {path}"
        ) from error
    if len(raw) != metadata.st_size:
        raise FormalVerificationError(f"changed_{kind}", f"{kind} changed while reading: {path}")
    return raw


def parse_tlc_output(output: str) -> TlcCounts:
    """Parse one complete TLC transcript and reject failed or partial state exploration."""

    if type(output) is not str:
        raise FormalVerificationError("invalid_output", "TLC output must be text")
    if re.search(r"Invariant\s+\S+\s+is violated", output, flags=re.IGNORECASE):
        raise FormalVerificationError("invariant_violation", "TLC reported an invariant violation")
    if "Model checking completed. No error has been found." not in output:
        raise FormalVerificationError("tlc_failure", "TLC did not report exact invariant success")
    matches = re.findall(
        r"([0-9][0-9,]*) states generated, ([0-9][0-9,]*) distinct states found, "
        r"([0-9][0-9,]*) states left on queue\.",
        output,
    )
    if not matches:
        raise FormalVerificationError("missing_state_counts", "TLC final state counts are missing")
    generated, distinct, queued = (int(value.replace(",", "")) for value in matches[-1])
    if generated < 1 or distinct < 1 or distinct > generated:
        raise FormalVerificationError("invalid_state_counts", "TLC state counts are invalid")
    if queued != 0:
        raise FormalVerificationError("incomplete_state_space", "TLC left states on its queue")
    depth_matches = re.findall(
        r"The depth of the complete state graph search is ([0-9][0-9,]*)\.", output
    )
    if not depth_matches:
        raise FormalVerificationError(
            "missing_search_depth", "TLC complete search depth is missing"
        )
    depth = int(depth_matches[-1].replace(",", ""))
    if depth < 0:
        raise FormalVerificationError("invalid_search_depth")
    return TlcCounts(generated, distinct, queued, depth, True)


def verify_jar(jar_path: Path, *, expected_sha256: str = EXPECTED_JAR_SHA256) -> str:
    """Verify the exact regular JAR bytes before any Java process is started."""

    raw = _regular_bytes(jar_path, kind="jar", maximum=128 * 1024 * 1024)
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected_sha256:
        raise FormalVerificationError(
            "jar_hash_mismatch",
            f"TLC JAR SHA-256 mismatch: expected {expected_sha256}, got {actual}",
        )
    return "sha256:" + actual


def _verify_java(java_path: Path) -> None:
    _regular_bytes(java_path, kind="java", maximum=256 * 1024 * 1024)


def _tlc_version(java_path: Path, jar_path: Path) -> str:
    result = subprocess.run(  # noqa: S603 -- explicit maintainer-provided executable
        [str(java_path), "-cp", str(jar_path), "tlc2.TLC", "-version"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = result.stdout + result.stderr
    match = re.search(r"TLC2 Version [^\r\n]+", output)
    if match is None:
        raise FormalVerificationError("tlc_version_missing", "TLC version could not be parsed")
    version = match.group(0).strip()
    if version != EXPECTED_TLC_VERSION:
        raise FormalVerificationError(
            "tlc_version_mismatch",
            f"TLC version mismatch: expected {EXPECTED_TLC_VERSION}, got {version}",
        )
    return version


def _artifact(root: Path, relative: Path, *, kind: str) -> dict[str, object]:
    raw = _regular_bytes(root / relative, kind=kind)
    return {"path": relative.as_posix(), "sha256": _sha256(raw), "byte_count": len(raw)}


def run_tlc(*, root: Path, java_path: Path, jar_path: Path) -> tuple[dict[str, Any], str]:
    """Run exhaustive TLC with one worker and bounded deterministic settings."""

    _verify_java(java_path)
    jar_sha256 = verify_jar(jar_path)
    version = _tlc_version(java_path, jar_path)
    model = _artifact(root, MODEL_PATH, kind="model")
    configuration = _artifact(root, CONFIG_PATH, kind="config")
    tla_root = root / MODEL_PATH.parent
    with tempfile.TemporaryDirectory(prefix="oscillink-tlc-") as metadata_directory:
        command = [
            str(java_path),
            "-Xms64m",
            f"-Xmx{HEAP_MAX_MIB}m",
            "-cp",
            str(jar_path),
            "tlc2.TLC",
            "-workers",
            "1",
            "-fp",
            "0",
            "-maxSetSize",
            str(MAX_SET_SIZE),
            "-deadlock",
            "-cleanup",
            "-metadir",
            metadata_directory,
            "-config",
            CONFIG_PATH.name,
            MODEL_PATH.name,
        ]
        try:
            completed = subprocess.run(  # noqa: S603 -- explicit verified Java and pinned JAR
                command,
                cwd=tla_root,
                check=False,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as error:
            raise FormalVerificationError(
                "tlc_timeout", "TLC exceeded its bounded timeout"
            ) from error
    transcript = completed.stdout + completed.stderr
    if completed.returncode != 0:
        if "Invariant" in transcript and "violated" in transcript:
            raise FormalVerificationError("invariant_violation", transcript.strip())
        raise FormalVerificationError("tlc_failed", transcript.strip())
    counts = parse_tlc_output(transcript)
    result: dict[str, Any] = {
        "schema_version": 1,
        "result_format": RESULT_FORMAT,
        "scope_id": "SCOPE-ROBOT-CELL-001",
        "evidence_class": "maintainer_run_synthetic_software_evidence",
        "model": model,
        "configuration": configuration,
        "tool": {"jar_sha256": jar_sha256, "tlc_version": version},
        "execution": {
            "workers": 1,
            "fingerprint_index": 0,
            "max_set_size": MAX_SET_SIZE,
            "heap_max_mib": HEAP_MAX_MIB,
            "timeout_seconds": TIMEOUT_SECONDS,
            "deadlock_check": False,
            "generated_states": counts.generated_states,
            "distinct_states": counts.distinct_states,
            "states_left_on_queue": counts.states_left_on_queue,
            "search_depth": counts.search_depth,
            "invariant_success": counts.invariant_success,
            "invariants": list(INVARIANTS),
        },
        "limitations": [
            "abstract_finite_model_only",
            "no_python_refinement_proof",
            "no_target_timing_or_stopping_validation",
            "no_plr_sil_or_diagnostic_coverage_claim",
            "no_application_validation_or_certification_claim",
        ],
    }
    return result, transcript


def verify_formal_result_binding(root: Path) -> tuple[str, ...]:
    """Check only canonical local bytes and bindings; never execute Java or access a network."""

    result_path = root / RESULT_PATH
    try:
        raw = _regular_bytes(result_path, kind="formal_result")
        text = raw.decode("utf-8", errors="strict")
        result = json.loads(text)
    except FormalVerificationError as error:
        return (str(error),)
    except UnicodeDecodeError:
        return ("formal result is not valid UTF-8",)
    except (json.JSONDecodeError, RecursionError):
        return ("formal result is malformed JSON",)
    if type(result) is not dict:
        return ("formal result must be a JSON object",)
    try:
        if raw != _canonical(result):
            return ("formal result must be canonical UTF-8 JSON plus LF",)
    except (TypeError, ValueError):
        return ("formal result is malformed JSON",)
    errors: list[str] = []
    if result.get("schema_version") != 1 or result.get("result_format") != RESULT_FORMAT:
        errors.append("formal result identity is invalid")
    for key, relative, label in (
        ("model", MODEL_PATH, "model"),
        ("configuration", CONFIG_PATH, "configuration"),
    ):
        entry = result.get(key)
        if type(entry) is not dict or entry.get("path") != relative.as_posix():
            errors.append(f"formal {label} binding is invalid")
            continue
        try:
            artifact_raw = _regular_bytes(root / relative, kind=label)
        except FormalVerificationError as error:
            errors.append(str(error))
            continue
        if entry.get("byte_count") != len(artifact_raw):
            errors.append(f"formal {label} byte count mismatch: {relative.as_posix()}")
        if entry.get("sha256") != _sha256(artifact_raw):
            errors.append(f"formal {label} SHA-256 mismatch: {relative.as_posix()}")
    tool = result.get("tool")
    if type(tool) is not dict or tool != {
        "jar_sha256": "sha256:" + EXPECTED_JAR_SHA256,
        "tlc_version": EXPECTED_TLC_VERSION,
    }:
        errors.append("formal TLC tool binding is invalid")
    execution = result.get("execution")
    if type(execution) is not dict:
        errors.append("formal execution summary is invalid")
    else:
        expected_settings = {
            "workers": 1,
            "fingerprint_index": 0,
            "max_set_size": MAX_SET_SIZE,
            "heap_max_mib": HEAP_MAX_MIB,
            "timeout_seconds": TIMEOUT_SECONDS,
            "deadlock_check": False,
            "states_left_on_queue": 0,
            "invariant_success": True,
            "invariants": list(INVARIANTS),
        }
        if any(execution.get(key) != value for key, value in expected_settings.items()):
            errors.append("formal execution settings or invariant result is invalid")
        generated = execution.get("generated_states")
        distinct = execution.get("distinct_states")
        depth = execution.get("search_depth")
        if (
            type(generated) is not int
            or type(distinct) is not int
            or type(depth) is not int
            or generated < 1
            or distinct < 1
            or distinct > generated
            or depth < 0
        ):
            errors.append("formal state counts are invalid")
    if result.get("evidence_class") != "maintainer_run_synthetic_software_evidence":
        errors.append("formal evidence class is invalid")
    return tuple(errors)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--java", type=Path, default=os.environ.get("SAFETY_OPS_JAVA"))
    parser.add_argument("--jar", type=Path, default=os.environ.get("SAFETY_OPS_TLA2TOOLS_JAR"))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="execute TLC and write canonical result")
    mode.add_argument(
        "--check", action="store_true", help="execute TLC and compare canonical result"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    if args.java is None or args.jar is None:
        raise SystemExit(
            "explicit --java/--jar paths or SAFETY_OPS_JAVA/SAFETY_OPS_TLA2TOOLS_JAR are required"
        )
    result, _ = run_tlc(root=ROOT, java_path=args.java, jar_path=args.jar)
    canonical = _canonical(result)
    destination = ROOT / RESULT_PATH
    if args.write:
        destination.write_bytes(canonical)
        print(
            "formal result written: "
            f"generated={result['execution']['generated_states']} "
            f"distinct={result['execution']['distinct_states']}"
        )
        return
    try:
        existing = _regular_bytes(destination, kind="formal_result")
    except FormalVerificationError as error:
        raise SystemExit(str(error)) from error
    if existing != canonical:
        raise SystemExit("formal result does not match this deterministic TLC execution")
    errors = verify_formal_result_binding(ROOT)
    if errors:
        raise SystemExit("\n".join(errors))
    print(
        "formal result verified: "
        f"generated={result['execution']['generated_states']} "
        f"distinct={result['execution']['distinct_states']}"
    )


if __name__ == "__main__":
    main()
