"""Deterministic bounded closed-file replay for the simulated supervisor."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from types import MappingProxyType
from typing import Any, Final

from pydantic import ValidationError

from .configuration import (
    ConfigurationAuthority,
    ConfigurationConstraints,
    ConfigurationError,
    load_supervisor_configuration,
)
from .contracts import CommandObservation, PhysicalObservation, SourceHealthObservation
from .freshness import Observation
from .supervisor import canonical_record_bytes, evaluate_supervisor, start_supervisor

DEFAULT_MAX_AUTHORITY_BYTES: Final = 65_536
DEFAULT_MAX_REPLAY_BYTES: Final = 4 * 1024 * 1024
DEFAULT_MAX_REPLAY_LINE_BYTES: Final = 1024 * 1024
REPORT_FORMAT: Final = "oscillink-runtime-replay-report-v1"
SCENARIO_FORMAT: Final = "oscillink-runtime-observation-jsonl-v1"
_RUNTIME_FORMAT_DESCRIPTOR: Final = (
    "oscillink-safety-ops/runtime-replay-v1;"
    "configuration=exact-ed25519-v1;observation=exact-jsonl-v1;"
    "canonical-json=utf8-lf-sort-keys-compact-v1"
)
RUNTIME_FORMAT_SOURCE_FILES: Final = (
    "configuration.py",
    "contracts.py",
    "correlator.py",
    "freshness.py",
    "policy.py",
    "replay.py",
    "state_machine.py",
    "supervisor.py",
)


class ReplayError(ValueError):
    """Typed fail-closed closed-file replay error."""

    def __init__(self, code: str, message: str | None = None) -> None:
        self.code = code
        super().__init__(message or code)


@dataclass(frozen=True, slots=True)
class ReplayResult:
    """Canonical report bytes and an immutable parsed view."""

    canonical_bytes: bytes
    report: MappingProxyType[str, Any]


@dataclass(frozen=True, slots=True)
class _CapturedFile:
    raw: bytes
    sha256: str


@dataclass(frozen=True, slots=True)
class RuntimeSourceIdentity:
    """Exact source-file identity contributing to the runtime replay format."""

    path: str
    sha256: str
    byte_count: int


@dataclass(frozen=True, slots=True)
class RuntimeFormatIdentity:
    """Aggregate identity derived from exact runtime source bytes."""

    sha256: str
    sources: tuple[RuntimeSourceIdentity, ...]


def runtime_format_identity(runtime_root: Path | None = None) -> RuntimeFormatIdentity:
    """Hash the exact implementation sources that define replay report semantics."""

    root = Path(__file__).resolve().parent if runtime_root is None else runtime_root
    if not isinstance(root, Path):
        raise ReplayError("runtime_format_unavailable", "runtime source root must be a Path")
    try:
        root_metadata = root.lstat()
    except OSError as error:
        raise ReplayError(
            "runtime_format_unavailable", "runtime source root is unavailable"
        ) from error
    if stat.S_ISLNK(root_metadata.st_mode) or not stat.S_ISDIR(root_metadata.st_mode):
        raise ReplayError(
            "runtime_format_unavailable", "runtime source root must be a real directory"
        )
    sources: list[RuntimeSourceIdentity] = []
    for name in RUNTIME_FORMAT_SOURCE_FILES:
        path = root / name
        try:
            metadata = path.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
                raise ReplayError(
                    "runtime_format_unavailable", f"runtime source is not a regular file: {name}"
                )
            raw = path.read_bytes()
        except ReplayError:
            raise
        except OSError as error:
            raise ReplayError(
                "runtime_format_unavailable", f"runtime source cannot be read: {name}"
            ) from error
        if not raw:
            raise ReplayError("runtime_format_unavailable", f"runtime source is empty: {name}")
        sources.append(
            RuntimeSourceIdentity(
                path=f"runtime/{name}",
                sha256="sha256:" + hashlib.sha256(raw).hexdigest(),
                byte_count=len(raw),
            )
        )
    payload = {
        "descriptor": _RUNTIME_FORMAT_DESCRIPTOR,
        "sources": [
            {"path": item.path, "sha256": item.sha256, "byte_count": item.byte_count}
            for item in sources
        ],
    }
    digest = "sha256:" + hashlib.sha256(_canonical_json(payload)).hexdigest()
    return RuntimeFormatIdentity(digest, tuple(sources))


def _validate_relative(path: Path) -> None:
    if not isinstance(path, Path):
        raise ReplayError("invalid_path", "replay path must be a Path")
    if path.is_absolute() or path.anchor or PureWindowsPath(str(path)).drive or ".." in path.parts:
        raise ReplayError("path_escape", "replay path must be relative and root-confined")


def _resolved_root(root: Path) -> Path:
    if not isinstance(root, Path):
        raise ReplayError("invalid_root", "replay root must be a Path")
    try:
        metadata = root.lstat()
    except OSError as error:
        raise ReplayError("invalid_root", "replay root is unavailable") from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise ReplayError("invalid_root", "replay root must be a real directory")
    return root.resolve()


def _capture_regular_file(root: Path, relative: Path, *, maximum: int) -> _CapturedFile:
    """Open a root-confined regular file once and retain its sole byte snapshot."""

    _validate_relative(relative)
    cursor = root
    metadata: os.stat_result | None = None
    try:
        for part in relative.parts:
            if part in {"", "."}:
                continue
            cursor /= part
            metadata = cursor.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                raise ReplayError("path_symlink", "replay input path contains a symlink")
    except FileNotFoundError as error:
        raise ReplayError("missing_file", "replay input file does not exist") from error
    except ReplayError:
        raise
    except OSError as error:
        raise ReplayError("metadata_unavailable") from error
    if metadata is None or not stat.S_ISREG(metadata.st_mode):
        raise ReplayError("non_regular", "replay input is not a regular file")
    if metadata.st_size > maximum:
        raise ReplayError("oversized", f"replay input exceeds {maximum} bytes")
    path = root / relative
    try:
        with path.open("rb") as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode):
                raise ReplayError("non_regular", "opened replay input is not regular")
            if (metadata.st_dev, metadata.st_ino) != (opened.st_dev, opened.st_ino):
                raise ReplayError("substitution", "replay input changed while opening")
            raw = stream.read(maximum + 1)
    except ReplayError:
        raise
    except OSError as error:
        raise ReplayError("read_failed", "replay input bytes cannot be read") from error
    if len(raw) > maximum:
        raise ReplayError("oversized", f"replay input exceeds {maximum} bytes")
    return _CapturedFile(raw, "sha256:" + hashlib.sha256(raw).hexdigest())


def _duplicate_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise ReplayError("duplicate_key", f"duplicate JSON object name: {name}")
        result[name] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise ReplayError("nonfinite_json", f"non-finite JSON number is forbidden: {value}")


def _parse_json_object(raw: bytes, *, kind: str) -> dict[str, Any]:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ReplayError("invalid_utf8", f"{kind} is not valid UTF-8") from error
    try:
        parsed = json.loads(
            text,
            object_pairs_hook=_duplicate_object,
            parse_constant=_reject_nonfinite,
        )
    except ReplayError:
        raise
    except (json.JSONDecodeError, RecursionError) as error:
        raise ReplayError("malformed_json", f"{kind} is malformed JSON") from error
    if type(parsed) is not dict:
        raise ReplayError("invalid_shape", f"{kind} must be a JSON object")
    return parsed


def _plain_string(value: object, name: str) -> str:
    if type(value) is not str or not value:
        raise ReplayError("invalid_authority", f"authority {name} must be a nonempty string")
    return value


def _load_authority(captured: _CapturedFile, *, root: Path) -> ConfigurationAuthority:
    data = _parse_json_object(captured.raw, kind="authority")
    expected_names = {
        "schema_version",
        "scope_id",
        "signer_id",
        "ed25519_public_key",
        "configuration_id",
        "revision",
        "approved_configuration_sha256",
        "constraints",
    }
    if set(data) != expected_names or data.get("schema_version") != 1:
        raise ReplayError("invalid_authority", "authority has unknown, missing, or invalid fields")
    if type(data["revision"]) is not int or data["revision"] < 1:
        raise ReplayError("invalid_authority", "authority revision must be a positive integer")
    public_wire = _plain_string(data["ed25519_public_key"], "ed25519_public_key")
    if not public_wire.startswith("ed25519-public:"):
        raise ReplayError("invalid_authority", "authority public key has the wrong format")
    try:
        public_key = bytes.fromhex(public_wire.removeprefix("ed25519-public:"))
    except ValueError as error:
        raise ReplayError("invalid_authority", "authority public key is not hexadecimal") from error
    constraints = data["constraints"]
    if type(constraints) is not dict or set(constraints) != {
        "max_observation_age_seconds",
        "max_receive_delay_seconds",
        "max_future_skew_seconds",
        "max_speed_mps",
        "max_acceleration_mps2",
        "mandatory_source_ids",
    }:
        raise ReplayError("invalid_authority", "authority constraints have invalid fields")
    sources = constraints["mandatory_source_ids"]
    if type(sources) is not list or not all(type(item) is str for item in sources):
        raise ReplayError("invalid_authority", "authority mandatory sources are invalid")
    if sources != sorted(set(sources)):
        raise ReplayError(
            "invalid_authority", "authority mandatory sources must be unique and sorted"
        )
    try:
        policy = ConfigurationAuthority(
            root=root,
            scope_id=_plain_string(data["scope_id"], "scope_id"),
            signer_public_keys={_plain_string(data["signer_id"], "signer_id"): public_key},
            approved_configuration_sha256={
                (
                    _plain_string(data["configuration_id"], "configuration_id"),
                    data["revision"],
                ): _plain_string(
                    data["approved_configuration_sha256"], "approved_configuration_sha256"
                )
            },
            constraints=ConfigurationConstraints(
                max_observation_age_seconds=constraints["max_observation_age_seconds"],
                max_receive_delay_seconds=constraints["max_receive_delay_seconds"],
                max_future_skew_seconds=constraints["max_future_skew_seconds"],
                max_speed_mps=constraints["max_speed_mps"],
                max_acceleration_mps2=constraints["max_acceleration_mps2"],
                mandatory_source_ids=frozenset(sources),
            ),
            minimum_revision=data["revision"],
        )
    except (TypeError, ValueError) as error:
        raise ReplayError("invalid_authority", "authority violates its strict contract") from error
    return policy


def _observation_from_line(raw_line: bytes) -> Observation:
    if len(raw_line) > DEFAULT_MAX_REPLAY_LINE_BYTES:
        raise ReplayError("oversized_line", "replay JSONL record exceeds its byte bound")
    data = _parse_json_object(raw_line, kind="replay JSONL record")
    if "input_sha256" in data:
        raise ReplayError("reserved_identity", "input_sha256 is reserved for exact-byte replay")
    source_domain = data.get("source_domain")
    model: type[CommandObservation] | type[PhysicalObservation] | type[SourceHealthObservation]
    if source_domain == "production_ai":
        model = CommandObservation
    elif source_domain == "independent_physical_observation":
        model = PhysicalObservation
    elif source_domain == "independent_source_health":
        model = SourceHealthObservation
    else:
        raise ReplayError("unknown_record", "replay record has an unknown source domain")
    data["input_sha256"] = "sha256:" + hashlib.sha256(raw_line).hexdigest()
    try:
        validation_wire = json.dumps(
            data,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return model.model_validate_json(validation_wire)
    except (TypeError, ValueError, ValidationError) as error:
        raise ReplayError(
            "invalid_observation", "replay observation violates its contract"
        ) from error


def parse_observation_jsonl(raw: bytes) -> tuple[Observation, ...]:
    """Parse one already-captured bounded JSONL snapshot into exact-line-bound observations."""

    if type(raw) is not bytes:
        raise ReplayError("invalid_bytes", "replay input must be exact bytes")
    if not raw:
        raise ReplayError("empty_input", "replay JSONL is empty")
    if len(raw) > DEFAULT_MAX_REPLAY_BYTES:
        raise ReplayError("oversized", f"replay input exceeds {DEFAULT_MAX_REPLAY_BYTES} bytes")
    if not raw.endswith(b"\n"):
        raise ReplayError("noncanonical_jsonl", "replay JSONL must end with LF")
    raw_lines = raw.splitlines(keepends=True)
    if any(line in {b"\n", b"\r\n"} for line in raw_lines):
        raise ReplayError("blank_line", "replay JSONL cannot contain blank lines")
    if any(line.endswith(b"\r\n") for line in raw_lines):
        raise ReplayError("noncanonical_jsonl", "replay JSONL must use LF line endings")
    observations = tuple(_observation_from_line(line) for line in raw_lines)
    digests = tuple(item.input_sha256 for item in observations)
    if len(digests) != len(set(digests)):
        raise ReplayError("duplicate_input", "replay JSONL contains duplicate exact records")
    ids = tuple(item.observation_id for item in observations)
    if len(ids) != len(set(ids)):
        raise ReplayError(
            "duplicate_observation_id", "replay JSONL contains duplicate observation IDs"
        )
    return observations


def _canonical_json(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _source_domain_for_id(source_id: str) -> str | None:
    for prefix, domain in (
        ("production-ai:", "production_ai"),
        ("independent-zone-sensor:", "independent_physical_observation"),
        ("independent-health-monitor:", "independent_source_health"),
    ):
        if source_id.startswith(prefix):
            return domain
    return None


def _validate_source_batches(
    observations: tuple[Observation, ...], *, required_source_ids: tuple[str, ...]
) -> None:
    required = set(required_source_ids)
    batch_size = len(required_source_ids)
    if len(observations) % batch_size:
        raise ReplayError("incomplete_batch", "replay ends with an incomplete source batch")
    for offset in range(0, len(observations), batch_size):
        batch = observations[offset : offset + batch_size]
        source_ids = tuple(item.source_id for item in batch)
        if len(source_ids) != len(set(source_ids)):
            raise ReplayError("duplicate_source", "replay batch contains a duplicate source")
        observed = set(source_ids)
        if required - observed:
            raise ReplayError("missing_source", "replay batch is missing a required source")
        if observed - required:
            raise ReplayError("unexpected_source", "replay batch contains an unexpected source")
        for item in batch:
            expected_domain = _source_domain_for_id(item.source_id)
            if expected_domain is None or item.source_domain != expected_domain:
                raise ReplayError(
                    "source_role_mismatch", "replay source identity has the wrong observation role"
                )


def replay_closed_files(
    *,
    root: Path,
    configuration: Path,
    input_path: Path,
    authority_path: Path,
) -> ReplayResult:
    """Capture, authenticate, replay, and report closed local files without side effects."""

    resolved_root = _resolved_root(root)
    authority_capture = _capture_regular_file(
        resolved_root, authority_path, maximum=DEFAULT_MAX_AUTHORITY_BYTES
    )
    policy = _load_authority(authority_capture, root=resolved_root)
    input_capture = _capture_regular_file(
        resolved_root, input_path, maximum=DEFAULT_MAX_REPLAY_BYTES
    )
    observations = parse_observation_jsonl(input_capture.raw)
    run_ids = {item.run_id for item in observations}
    if len(run_ids) != 1:
        raise ReplayError("run_mismatch", "replay observations must have one run identity")
    required_count = len(policy.constraints.mandatory_source_ids)
    first_time = max(item.received_at for item in observations[:required_count])
    try:
        bound = load_supervisor_configuration(
            configuration,
            authority=policy,
            evaluation_time=first_time,
        )
    except ConfigurationError as error:
        raise ReplayError("invalid_configuration", str(error)) from error
    if set(bound.configuration.required_source_ids) != set(policy.constraints.mandatory_source_ids):
        raise ReplayError(
            "invalid_configuration", "replay configuration sources must equal authority sources"
        )
    required_source_ids = bound.configuration.required_source_ids
    _validate_source_batches(observations, required_source_ids=required_source_ids)
    required_count = len(required_source_ids)
    run_id = next(iter(run_ids))
    runtime = start_supervisor(
        run_id=run_id,
        configuration=bound,
        evaluation_time=first_time,
        startup_input_sha256=(bound.configuration_sha256,),
    )
    decisions: list[dict[str, Any]] = []
    states: list[dict[str, Any]] = []
    requests: list[dict[str, Any]] = []
    decision_hashes: list[str] = []
    request_hashes: list[str] = []
    for offset in range(0, len(observations), required_count):
        batch = observations[offset : offset + required_count]
        evaluation_time = max(item.received_at for item in batch)
        evaluation = evaluate_supervisor(
            batch,
            evaluation_time=evaluation_time,
            runtime=runtime,
        )
        decision_raw = canonical_record_bytes(evaluation.decision)
        decisions.append(evaluation.decision.model_dump(mode="json"))
        states.append(evaluation.state.state.model_dump(mode="json"))
        decision_hashes.append("sha256:" + hashlib.sha256(decision_raw).hexdigest())
        if evaluation.action_request is not None:
            request_raw = canonical_record_bytes(evaluation.action_request)
            requests.append(evaluation.action_request.model_dump(mode="json"))
            request_hashes.append("sha256:" + hashlib.sha256(request_raw).hexdigest())
        runtime = evaluation.state
    scenario_id = "scenario:" + input_path.stem
    scenario_binding = _canonical_json(
        {
            "format": SCENARIO_FORMAT,
            "scenario_id": scenario_id,
            "input_sha256": input_capture.sha256,
        }
    )
    runtime_format = runtime_format_identity()
    report: dict[str, Any] = {
        "schema_version": 1,
        "report_format": REPORT_FORMAT,
        "scenario_format": SCENARIO_FORMAT,
        "scenario_id": scenario_id,
        "scenario_sha256": "sha256:" + hashlib.sha256(scenario_binding).hexdigest(),
        "runtime_format_sha256": runtime_format.sha256,
        "runtime_format_sources": [
            {"path": item.path, "sha256": item.sha256, "byte_count": item.byte_count}
            for item in runtime_format.sources
        ],
        "configuration_sha256": bound.configuration_sha256,
        "configuration_authority_sha256": authority_capture.sha256,
        "input_sha256": input_capture.sha256,
        "input_byte_count": len(input_capture.raw),
        "input_record_sha256": sorted(item.input_sha256 for item in observations),
        "run_id": run_id,
        "decisions": decisions,
        "decision_sha256": sorted(decision_hashes),
        "requests": requests,
        "request_sha256": sorted(request_hashes),
        "states": states,
        "final_state": runtime.state.model_dump(mode="json"),
        "delivery_mode": "local_closed_file_simulation",
        "operational_authority": "none",
        "stopping_claim": "not_established",
    }
    canonical = _canonical_json(report)
    parsed_view = MappingProxyType(json.loads(canonical))
    return ReplayResult(canonical, parsed_view)
