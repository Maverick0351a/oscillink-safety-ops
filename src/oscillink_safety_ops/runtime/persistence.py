"""Bounded exact-byte content-addressed persistence for supervisor state."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Any, Literal

from pydantic import ValidationError

from .contracts import SupervisorStateRecord
from .supervisor import canonical_record_bytes

DEFAULT_MAX_STATE_BYTES = 262_144


class PersistenceError(ValueError):
    """Typed fail-closed persistence integrity failure."""

    def __init__(self, code: str, message: str | None = None) -> None:
        self.code = code
        super().__init__(message or code)


@dataclass(frozen=True, slots=True)
class StateArtifact:
    """Trusted locator, exact-byte digest, and length for one state artifact."""

    relative_path: Path
    sha256: str
    byte_count: int

    def __post_init__(self) -> None:
        if not isinstance(self.relative_path, Path):
            raise TypeError("relative_path must be a Path")
        if (
            type(self.sha256) is not str
            or len(self.sha256) != 71
            or not self.sha256.startswith("sha256:")
            or any(character not in "0123456789abcdef" for character in self.sha256[7:])
        ):
            raise ValueError("sha256 must be a prefixed lowercase SHA-256")
        if type(self.byte_count) is not int or self.byte_count < 1:
            raise ValueError("byte_count must be a positive integer")


@dataclass(frozen=True, slots=True)
class StateLoadResult:
    """Loaded state or caller-supplied conservative state after an integrity failure."""

    state: SupervisorStateRecord
    integrity_state: Literal["verified", "failed_closed"]
    reason_code: str


def _relative_path(path: Path) -> None:
    if not isinstance(path, Path):
        raise PersistenceError("invalid_path", "state path must be a Path")
    if path.is_absolute() or path.anchor or PureWindowsPath(str(path)).drive or ".." in path.parts:
        raise PersistenceError(
            "path_escape", "state path must be relative and cannot escape its root"
        )


def _root(root: Path) -> Path:
    if not isinstance(root, Path):
        raise PersistenceError("invalid_root", "state root must be a Path")
    try:
        metadata = root.lstat()
    except OSError as error:
        raise PersistenceError("invalid_root", "state root is unavailable") from error
    if stat.S_ISLNK(metadata.st_mode):
        raise PersistenceError("root_symlink", "state root cannot be a symlink")
    if not stat.S_ISDIR(metadata.st_mode):
        raise PersistenceError("invalid_root", "state root must be a directory")
    return root.resolve()


def _reject_linked_parents(root: Path, relative: Path) -> None:
    cursor = root
    for part in relative.parts[:-1]:
        if part in {"", "."}:
            continue
        cursor /= part
        try:
            metadata = cursor.lstat()
        except FileNotFoundError:
            return
        except OSError as error:
            raise PersistenceError("metadata_unavailable") from error
        if stat.S_ISLNK(metadata.st_mode):
            raise PersistenceError("path_symlink", "state path contains a symlink")
        if not stat.S_ISDIR(metadata.st_mode):
            raise PersistenceError("non_directory_parent", "state parent is not a directory")


def _ensure_directory(root: Path, relative: Path) -> Path:
    _relative_path(relative)
    cursor = root
    for part in relative.parts:
        if part in {"", "."}:
            continue
        cursor /= part
        try:
            metadata = cursor.lstat()
        except FileNotFoundError:
            try:
                cursor.mkdir()
            except FileExistsError:
                metadata = cursor.lstat()
            else:
                metadata = cursor.lstat()
        except OSError as error:
            raise PersistenceError("directory_creation_failed") from error
        if stat.S_ISLNK(metadata.st_mode):
            raise PersistenceError("path_symlink", "state directory contains a symlink")
        if not stat.S_ISDIR(metadata.st_mode):
            raise PersistenceError("non_directory_parent", "state directory is not a directory")
    return cursor


def _duplicate_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise PersistenceError("duplicate_key", f"duplicate JSON object name: {name}")
        result[name] = value
    return result


def _parse_state(raw: bytes) -> SupervisorStateRecord:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise PersistenceError("invalid_utf8", "persisted state is not valid UTF-8") from error
    try:
        parsed = json.loads(text, object_pairs_hook=_duplicate_object)
    except PersistenceError:
        raise
    except (json.JSONDecodeError, RecursionError) as error:
        raise PersistenceError("malformed_json", "persisted state is malformed JSON") from error
    if not isinstance(parsed, dict):
        raise PersistenceError("invalid_shape", "persisted state JSON must be an object")
    try:
        return SupervisorStateRecord.model_validate_json(raw)
    except ValidationError as error:
        raise PersistenceError("invalid_state", "persisted state violates its contract") from error


def _read_exact(artifact: StateArtifact, *, root: Path, max_bytes: int) -> bytes:
    _relative_path(artifact.relative_path)
    if type(max_bytes) is not int or max_bytes < 1 or max_bytes > 1024 * 1024:
        raise PersistenceError("invalid_bound", "max_bytes is outside the permitted domain")
    if artifact.byte_count > max_bytes:
        raise PersistenceError("oversized", f"persisted state exceeds {max_bytes} bytes")
    _reject_linked_parents(root, artifact.relative_path)
    path = root / artifact.relative_path
    try:
        metadata = path.lstat()
    except FileNotFoundError as error:
        raise PersistenceError("missing_state", "persisted state is missing") from error
    except OSError as error:
        raise PersistenceError("metadata_unavailable") from error
    if stat.S_ISLNK(metadata.st_mode):
        raise PersistenceError("path_symlink", "persisted state cannot be a symlink")
    if not stat.S_ISREG(metadata.st_mode):
        raise PersistenceError("non_regular", "persisted state is not a regular file")
    if metadata.st_size > max_bytes:
        raise PersistenceError("oversized", f"persisted state exceeds {max_bytes} bytes")
    try:
        with path.open("rb") as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode):
                raise PersistenceError("non_regular")
            if (metadata.st_dev, metadata.st_ino) != (opened.st_dev, opened.st_ino):
                raise PersistenceError("substitution", "persisted state changed while opening")
            raw = stream.read(max_bytes + 1)
    except PersistenceError:
        raise
    except OSError as error:
        raise PersistenceError("read_failed", "persisted state bytes cannot be read") from error
    if len(raw) > max_bytes:
        raise PersistenceError("oversized", f"persisted state exceeds {max_bytes} bytes")
    if len(raw) != artifact.byte_count:
        raise PersistenceError("byte_count_mismatch", "persisted state byte count mismatch")
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    if digest != artifact.sha256:
        raise PersistenceError("hash_mismatch", "persisted state exact-byte hash mismatch")
    return raw


def _fsync_directory(directory: Path) -> None:
    try:
        descriptor = os.open(directory, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


def persist_supervisor_state(
    state: SupervisorStateRecord,
    *,
    root: Path,
    directory: Path = Path("states"),
    max_bytes: int = DEFAULT_MAX_STATE_BYTES,
) -> StateArtifact:
    """Publish canonical state bytes atomically without overwriting any destination."""

    resolved_root = _root(root)
    target_directory = _ensure_directory(resolved_root, directory)
    raw = canonical_record_bytes(state)
    if len(raw) > max_bytes:
        raise PersistenceError("oversized", f"persisted state exceeds {max_bytes} bytes")
    digest_hex = hashlib.sha256(raw).hexdigest()
    relative = directory / f"{digest_hex}.json"
    artifact = StateArtifact(relative, "sha256:" + digest_hex, len(raw))
    destination = resolved_root / relative
    if destination.exists() or destination.is_symlink():
        try:
            existing = _read_exact(artifact, root=resolved_root, max_bytes=max_bytes)
        except PersistenceError as error:
            raise PersistenceError(
                "destination_collision", "digest destination collision or poison detected"
            ) from error
        if existing == raw:
            return artifact

    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=target_directory,
            prefix=f".{digest_hex}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, destination)
        except FileExistsError:
            existing = _read_exact(artifact, root=resolved_root, max_bytes=max_bytes)
            if existing != raw:
                raise PersistenceError(
                    "destination_collision", "concurrent destination collision or poison detected"
                ) from None
        except OSError as error:
            raise PersistenceError(
                "publication_failed", "atomic state publication failed"
            ) from error
        _fsync_directory(target_directory)
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            except OSError as error:
                raise PersistenceError(
                    "cleanup_failed", "temporary state cleanup failed"
                ) from error

    final = _read_exact(artifact, root=resolved_root, max_bytes=max_bytes)
    if final != raw:
        raise PersistenceError("final_verification_failed")
    return artifact


def load_supervisor_state(
    artifact: StateArtifact,
    *,
    root: Path,
    max_bytes: int = DEFAULT_MAX_STATE_BYTES,
) -> SupervisorStateRecord:
    """Load, exact-byte verify, duplicate-check, and parse one persisted state."""

    resolved_root = _root(root)
    raw = _read_exact(artifact, root=resolved_root, max_bytes=max_bytes)
    return _parse_state(raw)


def load_supervisor_state_or_fail_closed(
    artifact: StateArtifact,
    *,
    root: Path,
    fail_closed_state: SupervisorStateRecord,
    max_bytes: int = DEFAULT_MAX_STATE_BYTES,
) -> StateLoadResult:
    """Return explicit conservative state for every persistence uncertainty."""

    if not fail_closed_state.latched or fail_closed_state.supervisor_state in {
        "monitoring_normal",
        "monitoring_degraded",
    }:
        raise ValueError("fail_closed_state must preserve a non-monitoring latch")
    try:
        loaded = load_supervisor_state(artifact, root=root, max_bytes=max_bytes)
    except PersistenceError as error:
        return StateLoadResult(fail_closed_state, "failed_closed", error.code)
    return StateLoadResult(loaded, "verified", "verified")
