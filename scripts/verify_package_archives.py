"""Inspect built wheel and source archives without extracting hostile paths."""

from __future__ import annotations

import argparse
import stat
import tarfile
import zipfile
from collections.abc import Iterable, Sequence
from pathlib import Path, PurePosixPath, PureWindowsPath

PROHIBITED_PARTS = {
    ".git",
    ".hermes",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "artifacts",
    "build",
    "customer-data",
    "hidden",
    "incident-data",
    "licensed-standards",
    "private",
    "runtime",
}
PROHIBITED_SUFFIXES = {".db", ".key", ".p12", ".pem", ".pfx", ".sqlite", ".sqlite3"}


def _parts(name: str) -> tuple[str, ...]:
    trimmed = name[:-1] if name.endswith("/") else name
    if (
        not trimmed
        or "\\" in trimmed
        or trimmed.startswith("/")
        or PureWindowsPath(trimmed).drive
        or any(part in {"", ".", ".."} for part in trimmed.split("/"))
    ):
        raise ValueError(f"unsafe archive member path: {name}")
    path = PurePosixPath(trimmed)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"unsafe archive member path: {name}")
    return tuple(part.casefold() for part in path.parts)


def _check_name(name: str, *, allow_runtime_package: bool) -> None:
    parts = _parts(name)
    checked = parts
    for index, part in enumerate(checked):
        if part == "runtime":
            if allow_runtime_package and index > 0 and checked[index - 1] == "oscillink_safety_ops":
                continue
            if index <= 1:
                raise ValueError(f"prohibited archive member: {name}")
            continue
        if part in PROHIBITED_PARTS:
            raise ValueError(f"prohibited archive member: {name}")
    basename = parts[-1]
    if (
        basename == ".env"
        or basename.startswith(".env.")
        or PurePosixPath(basename).suffix in PROHIBITED_SUFFIXES
    ):
        raise ValueError(f"prohibited credential or runtime artifact: {name}")


def _one(paths: Iterable[Path], label: str) -> Path:
    found = list(paths)
    if len(found) != 1:
        raise ValueError(f"expected exactly one {label}, found {len(found)}")
    path = found[0]
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular file")
    return path


def _verify_wheel(path: Path, version: str) -> None:
    metadata_payload: bytes | None = None
    with zipfile.ZipFile(path) as archive:
        for item in archive.infolist():
            _check_name(item.filename, allow_runtime_package=True)
            mode = item.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise ValueError(f"wheel contains a symlink: {item.filename}")
            if item.filename.endswith(".dist-info/METADATA"):
                metadata_payload = archive.read(item)
    if metadata_payload is None or f"Version: {version}\n".encode() not in metadata_payload.replace(
        b"\r\n", b"\n"
    ):
        raise ValueError("wheel metadata version does not match")


def _verify_sdist(path: Path, version: str) -> None:
    package_info: bytes | None = None
    expected_root = f"oscillink_safety_ops-{version}"
    with tarfile.open(path, mode="r:gz") as archive:
        for item in archive.getmembers():
            parts = _parts(item.name)
            if parts[0] != expected_root:
                raise ValueError(f"source archive root does not match version: {item.name}")
            _check_name(item.name, allow_runtime_package=True)
            if item.issym() or item.islnk() or not (item.isfile() or item.isdir()):
                raise ValueError(f"source archive contains nonregular member: {item.name}")
            if item.name.endswith("/PKG-INFO") and item.isfile():
                stream = archive.extractfile(item)
                package_info = None if stream is None else stream.read()
    if package_info is None or f"Version: {version}\n".encode() not in package_info.replace(
        b"\r\n", b"\n"
    ):
        raise ValueError("source archive metadata version does not match")


def verify_package_archives(directory: Path, version: str) -> None:
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("archive directory must be a regular directory")
    wheel = _one(directory.glob("*.whl"), "wheel")
    sdist = _one(directory.glob("*.tar.gz"), "source distribution")
    _verify_wheel(wheel, version)
    _verify_sdist(sdist, version)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--version", required=True)
    args = parser.parse_args(argv)
    verify_package_archives(args.directory, args.version)
    print(f"package archives verified: version={args.version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
