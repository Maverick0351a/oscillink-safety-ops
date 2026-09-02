"""Create portable release-verification files for local candidate artifacts."""

from __future__ import annotations

import argparse
import hashlib
from collections.abc import Sequence
from pathlib import Path

from oscillink_safety_ops.release import ReleaseArtifact, ReleaseVerification


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_release_files(
    *,
    artifacts: Sequence[Path],
    output_dir: Path,
    package_version: str,
    candidate_commit: str,
) -> ReleaseVerification:
    """Write deterministic JSON and basename-only checksum files."""
    entries: list[ReleaseArtifact] = []
    names: set[str] = set()
    for path in artifacts:
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"artifact must be a regular file: {path.name}")
        if path.name in names:
            raise ValueError(f"duplicate artifact basename: {path.name}")
        names.add(path.name)
        entries.append(
            ReleaseArtifact(
                name=path.name,
                sha256=sha256_file(path),
                size_bytes=path.stat().st_size,
            )
        )
    entries.sort(key=lambda item: (not item.name.endswith(".tar.gz"), item.name))
    manifest = ReleaseVerification(
        schema_version=1,
        package_name="oscillink-safety-ops",
        package_version=package_version,
        candidate_commit=candidate_commit,
        artifacts=tuple(entries),
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "release-verification.json").write_text(
        manifest.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    checksums = "".join(f"{item.sha256}  {item.name}\n" for item in manifest.artifacts)
    (output_dir / "SHA256SUMS.txt").write_text(
        checksums,
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def verify_release_directory(root: Path) -> ReleaseVerification:
    """Verify a self-contained release directory without external paths."""
    manifest = ReleaseVerification.model_validate_json(
        (root / "release-verification.json").read_text(encoding="utf-8")
    )
    expected_names = {
        "release-verification.json",
        "SHA256SUMS.txt",
        *(item.name for item in manifest.artifacts),
    }
    if {path.name for path in root.iterdir()} != expected_names:
        raise ValueError("release directory file set does not match the manifest")
    for item in manifest.artifacts:
        path = root / item.name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"artifact must be a regular file: {item.name}")
        if path.stat().st_size != item.size_bytes:
            raise ValueError(f"artifact size does not match: {item.name}")
        if sha256_file(path) != item.sha256:
            raise ValueError(f"artifact checksum does not match: {item.name}")
    expected_checksums = "".join(f"{item.sha256}  {item.name}\n" for item in manifest.artifacts)
    if (root / "SHA256SUMS.txt").read_text(encoding="utf-8") != expected_checksums:
        raise ValueError("checksum file does not match the release manifest")
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create", help="create release verification files")
    create.add_argument("--artifact", action="append", required=True, type=Path)
    create.add_argument("--output-dir", required=True, type=Path)
    create.add_argument("--package-version", required=True)
    create.add_argument("--candidate-commit", required=True)
    verify = subparsers.add_parser("verify", help="verify an isolated release directory")
    verify.add_argument("--release-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.command == "create":
        create_release_files(
            artifacts=args.artifact,
            output_dir=args.output_dir,
            package_version=args.package_version,
            candidate_commit=args.candidate_commit,
        )
        return 0
    if args.command == "verify":
        manifest = verify_release_directory(args.release_dir)
        print(
            f"verified release: package={manifest.package_name} "
            f"version={manifest.package_version} commit={manifest.candidate_commit} "
            f"artifacts={len(manifest.artifacts)}"
        )
        return 0
    raise AssertionError("unreachable command")


if __name__ == "__main__":
    raise SystemExit(main())
