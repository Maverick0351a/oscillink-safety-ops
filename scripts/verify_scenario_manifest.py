"""Verify the frozen synthetic runtime corpus against its exact-byte manifest."""

from __future__ import annotations

import hashlib
import json
import stat
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

CORPUS_FORMAT = "oscillink-runtime-scenario-manifest-v1"
_ALLOWED_ROLES = {"authority", "configuration", "scenario_input", "expected_report"}
_REQUIRED_PATHS = {
    "authority.json",
    "clean.jsonl",
    "configuration.json",
    "contradictory-source.jsonl",
    "expected/clean.report.json",
    "expected/contradictory-source.report.json",
    "expected/stale-source.report.json",
    "expected/zone-entry.report.json",
    "stale-source.jsonl",
    "zone-entry.jsonl",
}


class _DuplicateKey(ValueError):
    pass


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKey(key)
        result[key] = value
    return result


def _canonical(value: object) -> bytes:
    return (
        json.dumps(
            value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
        )
        + "\n"
    ).encode("utf-8")


def _corpus_files(corpus: Path) -> set[str]:
    ignored = {"MANIFEST.json", "README.md"}
    return {
        path.relative_to(corpus).as_posix()
        for path in corpus.rglob("*")
        if (path.is_file() or path.is_symlink())
        and path.relative_to(corpus).as_posix() not in ignored
    }


def _expected_role(path: str) -> str:
    if path == "authority.json":
        return "authority"
    if path == "configuration.json":
        return "configuration"
    if path.startswith("expected/"):
        return "expected_report"
    return "scenario_input"


def verify_scenario_manifest(corpus: Path) -> tuple[str, ...]:
    """Return stable exact-byte manifest errors for one closed synthetic corpus."""

    if not isinstance(corpus, Path):
        return ("corpus root must be a Path",)
    try:
        root_metadata = corpus.lstat()
    except OSError:
        return ("corpus root is unavailable",)
    if stat.S_ISLNK(root_metadata.st_mode) or not stat.S_ISDIR(root_metadata.st_mode):
        return ("corpus root must be a real directory",)
    root = corpus.resolve()
    manifest_path = root / "MANIFEST.json"
    try:
        metadata = manifest_path.lstat()
    except OSError:
        return ("manifest is missing",)
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        return ("manifest must be a regular file",)
    try:
        raw = manifest_path.read_bytes()
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return ("manifest is not valid UTF-8",)
    except OSError:
        return ("manifest cannot be read",)
    try:
        document = json.loads(text, object_pairs_hook=_object)
    except _DuplicateKey as error:
        return (f"manifest contains duplicate JSON key: {error}",)
    except (json.JSONDecodeError, RecursionError):
        return ("manifest is malformed JSON",)
    if type(document) is not dict:
        return ("manifest must be a JSON object",)
    try:
        canonical = _canonical(document)
    except (TypeError, ValueError):
        return ("manifest is malformed JSON",)
    if raw != canonical:
        return ("manifest must be canonical UTF-8 JSON plus LF",)
    if set(document) != {"schema_version", "corpus_format", "scope_id", "files"}:
        return ("manifest has unknown or missing fields",)
    if document.get("schema_version") != 1 or document.get("corpus_format") != CORPUS_FORMAT:
        return ("manifest identity is invalid",)
    if type(document.get("scope_id")) is not str or not document["scope_id"]:
        return ("manifest scope_id is invalid",)
    entries = document.get("files")
    if type(entries) is not list:
        return ("manifest files must be an array",)

    errors: list[str] = []
    seen: set[str] = set()
    listed: set[str] = set()
    paths_in_order: list[str] = []
    for index, entry in enumerate(entries):
        if type(entry) is not dict or set(entry) != {"path", "role", "sha256", "byte_count"}:
            errors.append(f"invalid manifest entry: {index}")
            continue
        path = entry.get("path")
        if type(path) is not str or not path:
            errors.append(f"invalid manifest path: {index}")
            continue
        paths_in_order.append(path)
        pure = PurePosixPath(path)
        if (
            pure.is_absolute()
            or pure.anchor
            or PureWindowsPath(path).drive
            or ".." in pure.parts
            or "\\" in path
        ):
            return (f"manifest path escapes corpus: {path}",)
        if path in seen:
            errors.append(f"duplicate manifest path: {path}")
        seen.add(path)
        listed.add(path)
        role = entry.get("role")
        if role not in _ALLOWED_ROLES or role != _expected_role(path):
            errors.append(f"invalid role: {path}")
        byte_count = entry.get("byte_count")
        if type(byte_count) is not int or byte_count < 1:
            errors.append(f"invalid byte_count: {path}")
        digest = entry.get("sha256")
        valid_digest = (
            type(digest) is str
            and len(digest) == 71
            and digest.startswith("sha256:")
            and all(character in "0123456789abcdef" for character in digest[7:])
        )
        if not valid_digest:
            errors.append(f"invalid SHA-256: {path}")

        target = root / Path(*pure.parts)
        cursor = root
        target_metadata = None
        try:
            for part in pure.parts:
                cursor /= part
                target_metadata = cursor.lstat()
                if stat.S_ISLNK(target_metadata.st_mode):
                    errors.append(f"manifested path is a symlink: {path}")
                    target_metadata = None
                    break
        except FileNotFoundError:
            errors.append(f"manifested file is missing: {path}")
            continue
        except OSError:
            errors.append(f"manifested file metadata unavailable: {path}")
            continue
        if target_metadata is None:
            continue
        if not stat.S_ISREG(target_metadata.st_mode):
            errors.append(f"manifested path is not a regular file: {path}")
            continue
        try:
            contents = target.read_bytes()
        except OSError:
            errors.append(f"manifested file cannot be read: {path}")
            continue
        if type(byte_count) is int and byte_count > 0 and len(contents) != byte_count:
            errors.append(f"byte count mismatch: {path}")
        actual = "sha256:" + hashlib.sha256(contents).hexdigest()
        if valid_digest and actual != digest:
            errors.append(f"SHA-256 mismatch: {path}")

    if paths_in_order != sorted(paths_in_order):
        errors.append("manifest paths must be sorted")
    actual_files = _corpus_files(root)
    for path in sorted(_REQUIRED_PATHS - listed):
        errors.append(f"missing manifest entry: {path}")
    for path in sorted(actual_files - _REQUIRED_PATHS):
        errors.append(f"unmanifested corpus file: {path}")
    for path in sorted(listed - _REQUIRED_PATHS):
        if f"manifested file is missing: {path}" not in errors:
            errors.append(f"unexpected manifest entry: {path}")
    return tuple(dict.fromkeys(errors))


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    errors = verify_scenario_manifest(root / "scenarios" / "robot_cell_v1")
    if errors:
        raise SystemExit("\n".join(errors))
    print("runtime scenario manifest: ok")


if __name__ == "__main__":
    main()
