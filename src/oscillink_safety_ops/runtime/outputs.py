"""Atomic root-confined publication of local simulated output artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Final

from pydantic import ValidationError

from .contracts import ActionRequest
from .supervisor import canonical_record_bytes

DEFAULT_MAX_OUTPUT_BYTES: Final = 8 * 1024 * 1024


class OutputError(ValueError):
    """Typed local output publication failure."""

    def __init__(self, code: str, message: str | None = None) -> None:
        self.code = code
        super().__init__(message or code)


@dataclass(frozen=True, slots=True)
class OutputArtifact:
    """Verified local output locator and exact-byte identity."""

    relative_path: Path
    sha256: str
    byte_count: int
    delivery_mode: str = "local_closed_file_simulation"
    operational_authority: str = "none"


def _relative(path: Path) -> None:
    if not isinstance(path, Path):
        raise OutputError("invalid_path", "output path must be a Path")
    if path.is_absolute() or path.anchor or PureWindowsPath(str(path)).drive or ".." in path.parts:
        raise OutputError("path_escape", "output path must be relative and root-confined")
    if path in {Path(""), Path(".")} or not path.name:
        raise OutputError("non_regular", "output path must name a regular file")


def _root(root: Path) -> Path:
    if not isinstance(root, Path):
        raise OutputError("invalid_root", "output root must be a Path")
    try:
        metadata = root.lstat()
    except OSError as error:
        raise OutputError("invalid_root", "output root is unavailable") from error
    if stat.S_ISLNK(metadata.st_mode):
        raise OutputError("root_symlink", "output root cannot be a symlink")
    if not stat.S_ISDIR(metadata.st_mode):
        raise OutputError("invalid_root", "output root must be a directory")
    return root.resolve()


def _directory(root: Path, relative: Path) -> Path:
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
                pass
            except OSError as error:
                raise OutputError("directory_creation_failed") from error
            try:
                metadata = cursor.lstat()
            except OSError as error:
                raise OutputError("metadata_unavailable") from error
        except OSError as error:
            raise OutputError("metadata_unavailable") from error
        if stat.S_ISLNK(metadata.st_mode):
            raise OutputError("path_symlink", "output path contains a symlink")
        if not stat.S_ISDIR(metadata.st_mode):
            raise OutputError("non_directory_parent", "output parent is not a directory")
    return cursor


def _read_verified(path: Path, *, expected: bytes, maximum: int) -> None:
    try:
        metadata = path.lstat()
    except OSError as error:
        raise OutputError("verification_failed", "published output is unavailable") from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise OutputError("non_regular", "published output is not a regular file")
    if metadata.st_size > maximum:
        raise OutputError("oversized", "published output exceeds its byte bound")
    try:
        with path.open("rb") as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode):
                raise OutputError("non_regular")
            if (metadata.st_dev, metadata.st_ino) != (opened.st_dev, opened.st_ino):
                raise OutputError("substitution", "published output changed while opening")
            actual = stream.read(maximum + 1)
    except OutputError:
        raise
    except OSError as error:
        raise OutputError("verification_failed", "published output cannot be read") from error
    if len(actual) != len(expected):
        raise OutputError("collision", "output destination byte-count collision")
    if hashlib.sha256(actual).digest() != hashlib.sha256(expected).digest() or actual != expected:
        raise OutputError("collision", "output destination exact-byte collision")


def _validate_existing_directory(root: Path, relative: Path) -> Path:
    cursor = root
    for part in relative.parts:
        if part in {"", "."}:
            continue
        cursor /= part
        try:
            metadata = cursor.lstat()
        except FileNotFoundError as error:
            raise OutputError("missing_output", "output parent is missing") from error
        except OSError as error:
            raise OutputError("metadata_unavailable", "output parent is unavailable") from error
        if stat.S_ISLNK(metadata.st_mode):
            raise OutputError("path_symlink", "output path contains a symlink")
        if not stat.S_ISDIR(metadata.st_mode):
            raise OutputError("non_directory_parent", "output parent is not a directory")
    return cursor


def _read_bounded_snapshot(path: Path, *, maximum: int) -> bytes:
    try:
        metadata = path.lstat()
    except FileNotFoundError as error:
        raise OutputError("missing_output", "request artifact is missing") from error
    except OSError as error:
        raise OutputError("metadata_unavailable", "request artifact is unavailable") from error
    if stat.S_ISLNK(metadata.st_mode):
        raise OutputError("path_symlink", "request artifact cannot be a symlink")
    if not stat.S_ISREG(metadata.st_mode):
        raise OutputError("non_regular", "request artifact must be a regular file")
    if metadata.st_size > maximum:
        raise OutputError("oversized", f"request artifact exceeds {maximum} bytes")
    try:
        with path.open("rb") as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode):
                raise OutputError("non_regular", "request artifact must be a regular file")
            if (metadata.st_dev, metadata.st_ino) != (opened.st_dev, opened.st_ino):
                raise OutputError("substitution", "request artifact changed while opening")
            raw = stream.read(maximum + 1)
    except OutputError:
        raise
    except OSError as error:
        raise OutputError("read_failed", "request artifact cannot be read") from error
    if len(raw) > maximum:
        raise OutputError("oversized", f"request artifact exceeds {maximum} bytes")
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


def publish_local_output(
    raw: bytes,
    *,
    root: Path,
    relative_path: Path,
    max_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
) -> OutputArtifact:
    """Publish exact bytes once; an existing destination must be byte-identical."""

    if type(raw) is not bytes or not raw:
        raise OutputError("invalid_bytes", "output must be nonempty exact bytes")
    if type(max_bytes) is not int or max_bytes < 1 or max_bytes > 64 * 1024 * 1024:
        raise OutputError("invalid_bound", "output byte bound is invalid")
    if len(raw) > max_bytes:
        raise OutputError("oversized", f"output exceeds {max_bytes} bytes")
    _relative(relative_path)
    resolved_root = _root(root)
    target_directory = _directory(resolved_root, relative_path.parent)
    destination = resolved_root / relative_path
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    artifact = OutputArtifact(relative_path, digest, len(raw))

    if destination.exists() or destination.is_symlink():
        _read_verified(destination, expected=raw, maximum=max_bytes)
        return artifact

    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=target_directory,
            prefix=f".{destination.name}.",
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
            _read_verified(destination, expected=raw, maximum=max_bytes)
        except OSError as error:
            raise OutputError("publication_failed", "atomic local publication failed") from error
        _fsync_directory(target_directory)
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            except OSError as error:
                raise OutputError("cleanup_failed", "temporary output cleanup failed") from error
    _read_verified(destination, expected=raw, maximum=max_bytes)
    return artifact


def _request_binding_bytes(request: ActionRequest, artifact: OutputArtifact) -> bytes:
    return (
        json.dumps(
            {
                "operational_authority": "none",
                "request_id": request.request_id,
                "request_relative_path": artifact.relative_path.as_posix(),
                "request_sha256": artifact.sha256,
                "schema_version": 1,
            },
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def load_action_request(
    artifact: OutputArtifact,
    *,
    root: Path,
    max_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
) -> ActionRequest:
    """Load one local simulated request artifact."""

    _relative(artifact.relative_path)
    if type(max_bytes) is not int or max_bytes < 1 or max_bytes > 64 * 1024 * 1024:
        raise OutputError("invalid_bound", "output byte bound is invalid")
    if artifact.byte_count > max_bytes:
        raise OutputError("oversized", f"request artifact exceeds {max_bytes} bytes")
    resolved_root = _root(root)
    _validate_existing_directory(resolved_root, artifact.relative_path.parent)
    path = resolved_root / artifact.relative_path
    raw = _read_bounded_snapshot(path, maximum=max_bytes)
    if len(raw) != artifact.byte_count:
        raise OutputError("byte_count_mismatch", "request artifact byte count mismatch")
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    if digest != artifact.sha256:
        raise OutputError("hash_mismatch", "request artifact exact-byte hash mismatch")
    if artifact.relative_path.name != f"{digest.removeprefix('sha256:')}.json":
        raise OutputError("content_address_mismatch", "request artifact path is not its digest")
    try:
        request = ActionRequest.model_validate_json(raw)
    except ValidationError as error:
        raise OutputError("invalid_request", "request artifact violates its contract") from error
    if canonical_record_bytes(request) != raw:
        raise OutputError("noncanonical_request", "request artifact bytes are not canonical")
    identity_digest = hashlib.sha256(request.request_id.encode("utf-8")).hexdigest()
    binding_path = (
        resolved_root / artifact.relative_path.parent / "by-id" / f"{identity_digest}.json"
    )
    try:
        _validate_existing_directory(resolved_root, artifact.relative_path.parent / "by-id")
    except OutputError as error:
        if error.code == "missing_output":
            raise OutputError(
                "missing_identity_binding", "request identity binding is missing"
            ) from error
        raise
    try:
        binding_path.lstat()
    except FileNotFoundError as error:
        raise OutputError(
            "missing_identity_binding", "request identity binding is missing"
        ) from error
    except OSError as error:
        raise OutputError(
            "metadata_unavailable", "request identity binding is unavailable"
        ) from error
    _read_verified(
        binding_path,
        expected=_request_binding_bytes(request, artifact),
        maximum=max_bytes,
    )
    return request


def persist_action_request(
    request: ActionRequest,
    *,
    root: Path,
    directory: Path = Path("requests"),
    max_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
) -> OutputArtifact:
    """Publish one canonical simulated request under its exact content address."""

    raw = canonical_record_bytes(request)
    digest = hashlib.sha256(raw).hexdigest()
    artifact = publish_local_output(
        raw,
        root=root,
        relative_path=directory / f"{digest}.json",
        max_bytes=max_bytes,
    )
    identity_digest = hashlib.sha256(request.request_id.encode("utf-8")).hexdigest()
    binding = _request_binding_bytes(request, artifact)
    try:
        publish_local_output(
            binding,
            root=root,
            relative_path=directory / "by-id" / f"{identity_digest}.json",
            max_bytes=max_bytes,
        )
    except OutputError as error:
        if error.code == "collision":
            raise OutputError(
                "request_identity_collision",
                "request identity is already bound to different exact bytes",
            ) from error
        raise
    return artifact
