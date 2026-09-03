"""Create and verify hostile-input release candidate directories."""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from oscillink_safety_ops.release import ReleaseArtifact, ReleaseVerification

CONTROL_FILES = {"release-verification.json", "SHA256SUMS.txt"}
JSON_EVIDENCE = {
    "cyclonedx-sbom.json",
    "provenance.json",
    "benchmark-metrics.json",
    "formal-result.json",
}


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(
            value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
        )
        + "\n"
    ).encode("utf-8")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _canonical_object(path: Path) -> dict[str, Any]:
    raw = _regular_bytes(path, label=path.name)
    try:
        value = json.loads(raw, object_pairs_hook=_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError(f"malformed JSON: {path.name}") from error
    if type(value) is not dict:
        raise ValueError(f"JSON evidence must be an object: {path.name}")
    try:
        expected = canonical_json(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"malformed JSON: {path.name}") from error
    if raw != expected:
        raise ValueError(f"artifact must use canonical JSON: {path.name}")
    return value


def _regular_bytes(path: Path, *, label: str) -> bytes:
    try:
        metadata = path.lstat()
    except FileNotFoundError as error:
        raise ValueError(f"missing regular file: {label}") from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise ValueError(f"artifact must be a regular file: {label}")
    if metadata.st_size < 1:
        raise ValueError(f"artifact must not be empty: {label}")
    raw = path.read_bytes()
    if len(raw) != metadata.st_size:
        raise ValueError(f"artifact changed while reading: {label}")
    return raw


def sha256_file(path: Path) -> str:
    return hashlib.sha256(_regular_bytes(path, label=path.name)).hexdigest()


def required_artifact_names(package_version: str) -> set[str]:
    stem = f"oscillink_safety_ops-{package_version}"
    return {
        f"{stem}.tar.gz",
        f"{stem}-py3-none-any.whl",
        *JSON_EVIDENCE,
    }


def _require_artifact_set(names: set[str], package_version: str) -> None:
    expected = required_artifact_names(package_version)
    if names != expected:
        missing = sorted(expected - names)
        extra = sorted(names - expected)
        raise ValueError(
            f"required release artifact set mismatch: missing={missing}; extra={extra}"
        )


def create_release_files(
    *,
    artifacts: Sequence[Path],
    output_dir: Path,
    package_version: str,
    candidate_commit: str,
    require_complete: bool = False,
) -> ReleaseVerification:
    """Write deterministic canonical JSON and basename-only checksum files."""
    entries: list[ReleaseArtifact] = []
    names: set[str] = set()
    for path in artifacts:
        raw = _regular_bytes(path, label=path.name)
        if path.name in CONTROL_FILES:
            raise ValueError(f"reserved artifact basename: {path.name}")
        if path.name in names:
            raise ValueError(f"duplicate artifact basename: {path.name}")
        names.add(path.name)
        entries.append(
            ReleaseArtifact(
                name=path.name,
                sha256=hashlib.sha256(raw).hexdigest(),
                size_bytes=len(raw),
            )
        )
    if require_complete:
        _require_artifact_set(names, package_version)
    entries.sort(key=lambda item: (not item.name.endswith(".tar.gz"), item.name))
    manifest = ReleaseVerification(
        schema_version=1,
        package_name="oscillink-safety-ops",
        package_version=package_version,
        candidate_commit=candidate_commit,
        artifacts=tuple(entries),
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    if output_dir.is_symlink() or not output_dir.is_dir():
        raise ValueError("output directory must be a regular directory")
    (output_dir / "release-verification.json").write_bytes(
        canonical_json(manifest.model_dump(mode="json"))
    )
    checksums = "".join(f"{item.sha256}  {item.name}\n" for item in manifest.artifacts)
    (output_dir / "SHA256SUMS.txt").write_text(checksums, encoding="utf-8", newline="\n")
    return manifest


def _validate_json_evidence(root: Path, manifest: ReleaseVerification) -> None:
    names = {item.name for item in manifest.artifacts}
    if "cyclonedx-sbom.json" in names:
        sbom = _canonical_object(root / "cyclonedx-sbom.json")
        component = sbom.get("metadata", {}).get("component", {})
        if (
            sbom.get("bomFormat") != "CycloneDX"
            or sbom.get("specVersion") != "1.6"
            or component.get("name") != manifest.package_name
            or component.get("version") != manifest.package_version
        ):
            raise ValueError("CycloneDX SBOM identity does not match release manifest")
    if "provenance.json" in names:
        provenance = _canonical_object(root / "provenance.json")
        if provenance.get("package_name") != manifest.package_name:
            raise ValueError("provenance package name does not match release manifest")
        if provenance.get("package_version") != manifest.package_version:
            raise ValueError("provenance package version does not match release manifest")
        if provenance.get("candidate_commit") != manifest.candidate_commit:
            raise ValueError("provenance candidate commit does not match release manifest")
    for name in ("benchmark-metrics.json", "formal-result.json"):
        if name in names:
            _canonical_object(root / name)


def verify_release_directory(
    root: Path,
    *,
    expected_version: str | None = None,
    expected_commit: str | None = None,
    require_complete: bool = False,
) -> ReleaseVerification:
    """Verify a self-contained release directory without external paths."""
    if root.is_symlink() or not root.is_dir():
        raise ValueError("release root must be a regular directory")
    manifest_value = _canonical_object(root / "release-verification.json")
    manifest = ReleaseVerification.model_validate(manifest_value)
    names = [item.name for item in manifest.artifacts]
    if len(names) != len(set(names)):
        raise ValueError("duplicate artifact basename in release manifest")
    if expected_version is not None and manifest.package_version != expected_version:
        raise ValueError("package version does not match expected release identity")
    if expected_commit is not None and manifest.candidate_commit != expected_commit:
        raise ValueError("candidate commit does not match expected release identity")
    if require_complete:
        _require_artifact_set(set(names), manifest.package_version)
    expected_names = {*CONTROL_FILES, *names}
    actual_names: set[str] = set()
    for path in root.iterdir():
        if path.name in actual_names:
            raise ValueError("duplicate release directory basename")
        actual_names.add(path.name)
        _regular_bytes(path, label=path.name)
    if actual_names != expected_names:
        raise ValueError("release directory file set does not match the manifest")
    for item in manifest.artifacts:
        path = root / item.name
        raw = _regular_bytes(path, label=item.name)
        if len(raw) != item.size_bytes:
            raise ValueError(f"artifact size does not match: {item.name}")
        if hashlib.sha256(raw).hexdigest() != item.sha256:
            raise ValueError(f"artifact checksum does not match: {item.name}")
    expected_checksums = "".join(f"{item.sha256}  {item.name}\n" for item in manifest.artifacts)
    checksum_raw = _regular_bytes(root / "SHA256SUMS.txt", label="SHA256SUMS.txt")
    if checksum_raw != expected_checksums.encode("utf-8"):
        raise ValueError("checksum file does not match the release manifest")
    _validate_json_evidence(root, manifest)
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create", help="create release verification files")
    create.add_argument("--artifact", action="append", required=True, type=Path)
    create.add_argument("--output-dir", required=True, type=Path)
    create.add_argument("--package-version", required=True)
    create.add_argument("--candidate-commit", required=True)
    create.add_argument("--require-complete", action="store_true")
    verify = subparsers.add_parser("verify", help="verify an isolated release directory")
    verify.add_argument("--release-dir", required=True, type=Path)
    verify.add_argument("--expected-version")
    verify.add_argument("--expected-commit")
    verify.add_argument("--require-complete", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "create":
        create_release_files(
            artifacts=args.artifact,
            output_dir=args.output_dir,
            package_version=args.package_version,
            candidate_commit=args.candidate_commit,
            require_complete=args.require_complete,
        )
        return 0
    manifest = verify_release_directory(
        args.release_dir,
        expected_version=args.expected_version,
        expected_commit=args.expected_commit,
        require_complete=args.require_complete,
    )
    print(
        f"verified release: package={manifest.package_name} "
        f"version={manifest.package_version} commit={manifest.candidate_commit} "
        f"artifacts={len(manifest.artifacts)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
