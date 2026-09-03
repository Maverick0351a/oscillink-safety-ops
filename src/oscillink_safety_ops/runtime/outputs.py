"""Atomic root-confined publication of local simulated output artifacts."""

from __future__ import annotations

import hashlib
import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Final

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
